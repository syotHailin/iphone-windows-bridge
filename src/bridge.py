"""Configure the selected USB device; run bounded native WDA requests."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from kit_common import CONFIG, CONFIG_PATH, ROOT
from pymobiledevice3.usbmux import list_devices
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.wda import WdaServiceClient


async def configure(args):
    if not all(1024 <= port <= 65535 for port in (args.tunnel_port,args.viewer_port)) or args.tunnel_port == args.viewer_port:
        raise RuntimeError('Choose distinct ports between 1024 and 65535.')
    devices = [d for d in await list_devices() if d.connection_type == 'USB']
    if args.udid:
        devices = [d for d in devices if d.serial == args.udid]
    if len(devices) != 1:
        raise RuntimeError(f'Found {len(devices)} matching USB devices. Connect exactly one, or pass --udid explicitly.')
    udid = devices[0].serial
    async with await create_using_usbmux(serial=udid) as lockdown:
        async with InstallationProxyService(lockdown) as proxy:
            apps = await proxy.get_apps(application_type='User')
        candidates = [bid for bid, app in apps.items() if 'webdriveragent' in (bid + str(app.get('CFBundleName','')) + str(app.get('CFBundleExecutable',''))).lower()]
        if args.bundle_id:
            candidates = [bid for bid in apps if bid == args.bundle_id]
        if len(candidates) != 1:
            raise RuntimeError(f'Found {len(candidates)} WDA runners. Sign/install the supplied IPA first; use --bundle-id for a renamed runner.')
        config = dict(CONFIG, udid=udid, bundle_id=candidates[0], tunnel_info_port=args.tunnel_port, viewer_port=args.viewer_port)
        if CONFIG_PATH.exists():
            (ROOT/'config.previous.json').write_bytes(CONFIG_PATH.read_bytes())
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')
        return {'configured':True,'ios':lockdown.all_values.get('ProductVersion'),'private_config':str(CONFIG_PATH)}


async def native(args):
    if not CONFIG.get('udid'):
        raise RuntimeError('Run configure after signing WDA.')
    async with await create_using_usbmux(serial=CONFIG['udid']) as lockdown:
        client = WdaServiceClient(lockdown)
        if args.action == 'status':
            s = await client.get_status()
            return {'ready':s.get('value',{}).get('ready',False),'os':s.get('value',{}).get('os',{}).get('version')}
        if args.action == 'source':
            data = await client.get_source()
            Path(args.output).write_text(data if isinstance(data,str) else json.dumps(data),encoding='utf-8')
            return {'saved':args.output}
        if args.action == 'screenshot':
            data = await client.get_screenshot()
            Path(args.output).write_bytes(data)
            return {'saved':args.output}
        # Explicit CLI actions only; agent must authorize the intended UI operation.
        session = (await client.get_status()).get('sessionId') or await client.start_session()
        if args.action == 'launch':
            await client._request_json('POST',f'/session/{session}/wda/apps/launch',{'bundleId':args.bundle_id})
        elif args.action == 'click':
            matches = await client._request_json('POST',f'/session/{session}/elements',{'using':'xpath','value':args.xpath})
            if len(matches.get('value',[])) != 1:
                raise RuntimeError('XPath must match exactly one current element.')
            item = matches['value'][0]
            element = item.get('element-6066-11e4-a52e-4f735466cecf') or item.get('ELEMENT')
            if not element:
                raise RuntimeError('WDA did not return an element ID.')
            await client.click(element,session_id=session)
        return {'ok':True}


def main():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest='action',required=True)
    p = subs.add_parser('configure')
    p.add_argument('--udid'); p.add_argument('--bundle-id')
    p.add_argument('--tunnel-port',type=int,default=60105)
    p.add_argument('--viewer-port',type=int,default=19101)
    subs.add_parser('status')
    for name in ['source','screenshot']:
        p = subs.add_parser(name); p.add_argument('--output',required=True)
    p = subs.add_parser('launch'); p.add_argument('--bundle-id',required=True)
    p = subs.add_parser('click'); p.add_argument('--xpath',required=True)
    args = parser.parse_args()
    try:
        result = asyncio.run(asyncio.wait_for(configure(args) if args.action == 'configure' else native(args),60))
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'error_type':type(exc).__name__,'message':str(exc)},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
