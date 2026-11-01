"""USB screen viewer with local pointer controls; no recordings."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

import psutil
from aiohttp import web
from pymobiledevice3.service_connection import ServiceConnection
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.wda import WdaServiceClient

from kit_common import ROOT, CONFIG
PORT = CONFIG.get('viewer_port', 19101)
URL = f'http://127.0.0.1:{PORT}'
PAGE = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>iPhone 实时画面</title>
<style>*{box-sizing:border-box}body{margin:0;background:#11151c;color:#f4f6fb;font:14px system-ui,"Microsoft YaHei",sans-serif;height:100vh;display:flex;flex-direction:column}header{padding:14px 18px;display:flex;align-items:center;justify-content:space-between;background:#1b2230}h1{font-size:16px;margin:0}#status{font-size:12px;color:#b8c4d7;margin-top:5px}button{background:#2c3b50;color:white;border:0;border-radius:8px;padding:8px 12px;cursor:pointer}main{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:10px}img{max-width:100%;max-height:100%;object-fit:contain;box-shadow:0 4px 24px #0006;background:#060709}footer{text-align:center;color:#a7b1c4;font-size:12px;padding:4px 8px 10px}</style>
<style>#screen{touch-action:none;user-select:none;-webkit-user-drag:none;cursor:crosshair}#action{min-height:18px;color:#d2deef}#ring{position:fixed;width:26px;height:26px;border:3px solid #71b7ff;border-radius:50%;pointer-events:none;transform:translate(-50%,-50%);display:none}nav{display:flex;gap:6px}button:disabled{opacity:.5}</style>
<header><div><h1>iPhone 实时画面</h1><div id="status">正在连接手机…</div></div><nav><button id="home">主屏幕</button><button id="retry">重连</button></nav></header><main><img id="screen" alt="iPhone 实时画面，可点击或拖动" draggable="false"></main><footer><div id="action" role="status">点击画面操作 · 按住拖动滑动</div>USB 连接 · 操作会直接作用于手机</footer><div id="ring"></div>
<script>
const pic=document.querySelector('#screen'),status=document.querySelector('#status'),action=document.querySelector('#action'),home=document.querySelector('#home'),ring=document.querySelector('#ring');let lastRetry=0,busy=false,live=false,down=null;
function connect(){lastRetry=Date.now();pic.src='/stream?t='+lastRetry;}
function point(e){const r=pic.getBoundingClientRect(),scale=Math.min(r.width/pic.naturalWidth,r.height/pic.naturalHeight),w=pic.naturalWidth*scale,h=pic.naturalHeight*scale;const x=(e.clientX-r.left-(r.width-w)/2)/w,y=(e.clientY-r.top-(r.height-h)/2)/h;if(!w||!h||x<0||x>1||y<0||y>1)return null;return {x,y,aspect:pic.naturalWidth/pic.naturalHeight};}
async function command(payload){if(busy||!live)return;busy=true;home.disabled=true;action.textContent='正在操作…';try{const r=await fetch('/control',{method:'POST',headers:{'Content-Type':'application/json','X-iPhone-Control':'1'},body:JSON.stringify(payload)});const v=await r.json();if(!r.ok)throw new Error(v.error||'操作未完成');action.textContent=payload.kind==='tap'?'已点击':payload.kind==='swipe'?'已滑动':'已返回主屏幕';}catch(e){action.textContent=e.message;}finally{busy=false;home.disabled=false;}}
pic.addEventListener('pointerdown',e=>{if(e.button!==0||busy||!live)return;let p=point(e);if(!p)return;down={...p,t:performance.now(),id:e.pointerId};pic.setPointerCapture(e.pointerId);e.preventDefault();});
pic.addEventListener('pointerup',e=>{let p=point(e),d=down;down=null;if(!d||d.id!==e.pointerId||!p)return;const distance=Math.hypot(p.x-d.x,p.y-d.y);ring.style.left=e.clientX+'px';ring.style.top=e.clientY+'px';ring.style.display='block';setTimeout(()=>ring.style.display='none',450);command(distance<.015?{kind:'tap',x:p.x,y:p.y,aspect:p.aspect}:{kind:'swipe',x:d.x,y:d.y,toX:p.x,toY:p.y,duration:Math.min(.8,Math.max(.1,(performance.now()-d.t)/1000)),aspect:p.aspect});});
pic.addEventListener('pointercancel',()=>down=null);pic.addEventListener('dragstart',e=>e.preventDefault());home.onclick=()=>command({kind:'home'});document.querySelector('#retry').onclick=connect;pic.onerror=()=>{live=false;status.textContent='连接已断开，正在重试…';};
setInterval(async()=>{try{let r=await fetch('/health',{cache:'no-store'}),h=await r.json();live=h.live;status.textContent=live?'● 实时画面 · 鼠标控制已启用':'等待手机画面 · 请保持手机解锁';if(!live&&Date.now()-lastRetry>6000)connect();}catch(e){live=false;status.textContent='画面服务已停止，请重新打开观看窗口';}},1500);connect();</script></html>'''


@web.middleware
async def local_only(request, handler):
    if request.host != f'127.0.0.1:{PORT}' or request.headers.get('Sec-Fetch-Site') == 'cross-site':
        raise web.HTTPForbidden()
    response = await handler(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


last_data = 0.0
received = 0
input_lock = asyncio.Lock()


async def page(request):
    return web.Response(text=PAGE, content_type='text/html', headers={'Content-Security-Policy': "default-src 'self'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'"})


async def health(request):
    return web.json_response({'service': 'iphone-usb-view', 'version': 2, 'live': time.monotonic() - last_data < 5, 'received_bytes': received})


async def control(request):
    if request.headers.get('Origin') != URL or request.headers.get('X-iPhone-Control') != '1' or request.content_type != 'application/json':
        raise web.HTTPForbidden()
    if input_lock.locked():
        return web.json_response({'error': '上一项操作尚未完成，请稍后点击。'}, status=409)
    if time.monotonic() - last_data > 5:
        return web.json_response({'error': '画面尚未连接，请等待实时画面恢复。'}, status=503)
    try:
        payload = await request.json()
        kind = payload.get('kind')
        if kind not in ['tap', 'swipe', 'home']:
            raise ValueError('Unsupported control')
        if kind != 'home':
            for key in ['x', 'y'] + (['toX', 'toY'] if kind == 'swipe' else []):
                if type(payload.get(key)) not in [float, int] or not math.isfinite(payload[key]) or not 0 <= payload[key] <= 1:
                    raise ValueError('Invalid position')
            if type(payload.get('aspect')) not in [float, int] or not math.isfinite(payload['aspect']) or payload['aspect'] <= 0:
                raise ValueError('Invalid aspect')
        if kind == 'swipe' and (type(payload.get('duration')) not in [float, int] or not math.isfinite(payload['duration']) or not .1 <= payload['duration'] <= .8):
            raise ValueError('Invalid duration')
    except (ValueError, AttributeError):
        return web.json_response({'error': '无效操作参数。'}, status=400)
    async with input_lock:
        try:
            async with asyncio.timeout(20):
                async with await create_using_usbmux(serial=CONFIG['udid']) as lockdown:
                    client = WdaServiceClient(lockdown)
                    current = await client.get_status()
                    # Reuse the live session. Replacing a WDA session can terminate
                    # its app and would send this click to a different foreground app.
                    manual_session = current.get('sessionId')
                    if not manual_session:
                        manual_session = await client.start_session()
                    if kind == 'home':
                        await client._request_json('POST', '/wda/homescreen', {})
                    else:
                        size = await client.get_window_size(session_id=manual_session)
                        w, h = size['width'], size['height']
                        if abs(w / h - payload['aspect']) > .03:
                            return web.json_response({'error': '手机方向已改变，请等画面更新后重新点击。'}, status=409)
                        x = min(w - 1, payload['x'] * w)
                        y = min(h - 1, payload['y'] * h)
                        if kind == 'tap':
                            await client._request_json('POST', f'/session/{manual_session}/wda/tap', {'x': x, 'y': y})
                        else:
                            await client.swipe(x, y, min(w - 1, payload['toX'] * w), min(h - 1, payload['toY'] * h), duration=payload['duration'], session_id=manual_session)
            return web.json_response({'ok': True})
        except Exception:
            return web.json_response({'error': '手机操作未完成，请确认已解锁且控制服务仍在运行。'}, status=502)


async def stream(request):
    global last_data, received
    response = None
    try:
        connection = await asyncio.wait_for(ServiceConnection.create_using_usbmux(CONFIG['udid'], 9100), 8)
        async with connection:
            await connection.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n')
            data = b''
            while b'\r\n\r\n' not in data:
                chunk = await asyncio.wait_for(connection.recv_any(8192), 8)
                if not chunk or len(data) > 65536:
                    raise RuntimeError('Invalid MJPEG headers')
                data += chunk
            header, remainder = data.split(b'\r\n\r\n', 1)
            content_type = next(line.split(b':', 1)[1].strip().decode('ascii') for line in header.split(b'\r\n') if line.lower().startswith(b'content-type:'))
            if not content_type.startswith('multipart/x-mixed-replace;'):
                raise RuntimeError('Unexpected media type')
            response = web.StreamResponse(headers={'Content-Type': content_type, 'Cache-Control': 'no-store'})
            await response.prepare(request)
            if remainder:
                await response.write(remainder)
            while True:
                chunk = await asyncio.wait_for(connection.recv_any(65536), 8)
                if not chunk:
                    break
                received += len(chunk)
                last_data = time.monotonic()
                await response.write(chunk)
    except (ConnectionError, asyncio.TimeoutError, OSError, RuntimeError):
        if response is None:
            raise web.HTTPServiceUnavailable(text='Connect and unlock the phone, then start iPhone control.')
    return response or web.Response(status=503)


def alive():
    try:
        with urllib.request.urlopen(URL + '/health', timeout=2) as r:
            return json.load(r).get('service') == 'iphone-usb-view'
    except Exception:
        return False


def start():
    if alive():
        return
    with (ROOT / 'viewer.log').open('ab') as log:
        p = subprocess.Popen([sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), 'serve'], stdout=log, stderr=log, stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    proc = psutil.Process(p.pid)
    (ROOT / 'viewer-process.json').write_text(json.dumps({'pid': p.pid, 'created': proc.create_time(), 'exe': proc.exe()}))
    for _ in range(30):
        if alive():
            return
        if p.poll() is not None:
            raise RuntimeError('Viewer failed to start; inspect local viewer.log')
        time.sleep(0.2)
    raise RuntimeError('Viewer startup timed out')


def stop():
    path = ROOT / 'viewer-process.json'
    if not path.exists():
        return
    state = json.loads(path.read_text())
    try:
        p = psutil.Process(state['pid'])
        if abs(p.create_time() - state['created']) < .1 and os.path.normcase(p.exe()) == os.path.normcase(state['exe']) and str(Path(__file__).resolve()) in p.cmdline():
            p.terminate()
            p.wait(timeout=5)
    except psutil.NoSuchProcess:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'serve'])
    args = parser.parse_args()
    if args.action == 'serve':
        app = web.Application(middlewares=[local_only], client_max_size=4096)
        app.add_routes([web.get('/', page), web.get('/health', health), web.get('/stream', stream), web.post('/control', control)])
        web.run_app(app, host='127.0.0.1', port=PORT, access_log=None, print=None)
    elif args.action == 'start':
        start()
        print(URL)
    else:
        stop()
