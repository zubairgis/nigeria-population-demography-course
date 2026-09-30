from __future__ import annotations
import argparse, json, hashlib, zipfile
from pathlib import Path

def sha256sum(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1024*1024), b""):
            h.update(c)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--zip", required=True)
    args=p.parse_args()
    d=Path(args.input_dir)
    files=[x for x in d.rglob("*") if x.is_file()]
    if not files:
        raise ValueError("Nothing to package.")
    manifest=[]
    for f in files:
        manifest.append({
            "path":str(f.relative_to(d)),
            "size_bytes":f.stat().st_size,
            "sha256":sha256sum(f)
        })
    (d/"package_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    files=[x for x in d.rglob("*") if x.is_file()]
    z=Path(args.zip)
    z.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_DEFLATED) as out:
        for f in files:
            out.write(f, arcname=f.relative_to(d))
    print("Packaged", len(files), "files:", z)
    print("ZIP sha256:", sha256sum(z))

if __name__=="__main__":
    main()
