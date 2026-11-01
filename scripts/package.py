"""Explicit allowlist: never package device state, logs, runtime or user screenshots."""
import argparse, hashlib, json, zipfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source-only',action='store_true');p.add_argument('--include-private-prerequisites',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    allowed={'src','docs','skills','tests','scripts','licenses'}
    if not args.source_only: allowed.add('vendor')
    if args.include_private_prerequisites: allowed.add('private-prerequisites')
    rootnames={'.gitignore','LICENSE','README.md','dependencies.json','requirements.lock.txt','Install.ps1','Configure.ps1','Start.ps1','Stop.ps1','Doctor.ps1','Fetch-Prerequisites.ps1'}
    files=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file(): continue
        rel=path.relative_to(root)
        if '__pycache__' in rel.parts or path.suffix in {'.pyc','.log','.p12','.pem','.mobileprovision'}: continue
        if (len(rel.parts)==1 and rel.name in rootnames) or (len(rel.parts)>1 and rel.parts[0] in allowed): files.append(path)
    target=Path(args.output).resolve()
    if target.is_relative_to(root): raise RuntimeError('Output must be outside the source tree')
    if target.exists(): raise RuntimeError('Refusing to overwrite archive')
    manifest={path.relative_to(root).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for path in files:
            rel=path.relative_to(root).as_posix()
            # Already-compressed installers and assets need no costly second pass.
            compression=zipfile.ZIP_STORED if path.suffix in {'.exe','.zip','.ipa','.gz','.xz'} else zipfile.ZIP_DEFLATED
            archive.write(path,'iphone-windows-bridge/'+rel,compress_type=compression)
        archive.writestr('iphone-windows-bridge/FILES.sha256.json',json.dumps(manifest,indent=2)+'\n')
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix+'.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert not any('/runtime/' in n or '/test-state/' in n for n in archive.namelist())
    print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'files':len(files),'sha256':digest}))

if __name__=='__main__':main()
