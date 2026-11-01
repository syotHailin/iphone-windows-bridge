"""Sanitized, read-only preflight; HTTPS reachability is not signing success."""
import argparse, asyncio, concurrent.futures, json, platform, socket, time, urllib.request, urllib.error
from pathlib import Path
from kit_common import CONFIG, KIT

URLS = {
    'Apple downloads': 'https://www.apple.com/itunes/download/win64',
    'Apple account': 'https://account.apple.com/',
    'Apple developer': 'https://developer.apple.com/',
    'Apple trust': 'https://ppq.apple.com/',
    'Sideloadly': 'https://sideloadly.io/',
    'GitHub release host': 'https://github.com/danielpaulus/go-ios/releases/tag/v1.3.2',
    'Developer image manifest': 'https://raw.githubusercontent.com/doronz88/DeveloperDiskImage/main/PersonalizedImages/Xcode_iOS_DDI_Personalized/BuildManifest.plist',
}

def endpoint(item):
    name,url=item; started=time.monotonic()
    try:
        req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'iphone-windows-bridge-preflight/0.1'})
        with urllib.request.urlopen(req,timeout=12) as r:
            code=r.status
        result='http_reachable'
    except urllib.error.HTTPError as exc:
        code=exc.code; result='http_reachable_but_rejected'
    except Exception as exc:
        return {'name':name,'result':'unreachable','error_type':type(exc).__name__}
    return {'name':name,'result':result,'http_status':code,'elapsed_seconds':round(time.monotonic()-started,2)}

async def phone():
    from pymobiledevice3.usbmux import list_devices
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.wda import WdaServiceClient
    ds=[d for d in await list_devices() if d.connection_type=='USB']
    result={'usb_device_count':len(ds),'configured':bool(CONFIG.get('udid'))}
    if CONFIG.get('udid') and any(d.serial==CONFIG['udid'] for d in ds):
        async with await create_using_usbmux(serial=CONFIG['udid']) as lockdown:
            result['ios']=lockdown.all_values.get('ProductVersion')
            try:
                status=await asyncio.wait_for(WdaServiceClient(lockdown).get_status(),8)
                result['wda_ready']=status.get('value',{}).get('ready') is True
            except Exception as exc:
                result['wda_ready']=False;result['wda_error_type']=type(exc).__name__
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--network',action='store_true');p.add_argument('--output');args=p.parse_args()
    report={'schema':1,'host_arch':platform.machine(),'python':platform.python_version(),'network_location':'not_verified','signing_test':'not_performed'}
    try:
        with socket.create_connection(('127.0.0.1',27015),timeout=2): report['apple_service_port']=True
    except OSError: report['apple_service_port']=False
    try: report['device']=asyncio.run(asyncio.wait_for(phone(),20))
    except Exception as exc: report['device']={'error_type':type(exc).__name__}
    if args.network:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            report['network']=list(pool.map(endpoint,URLS.items()))
        report['note']='HEAD checks only; actual Apple sign-in/TSS/Anisette, large downloads and mainland routes still require on-site validation.'
    text=json.dumps(report,indent=2,ensure_ascii=False)
    print(text)
    if args.output: Path(args.output).write_text(text+'\n',encoding='utf-8')
    return 0 if report['apple_service_port'] and not report.get('device',{}).get('error_type') else 1

if __name__=='__main__': raise SystemExit(main())
