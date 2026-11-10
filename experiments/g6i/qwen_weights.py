"""Recover each shard only after verifying the immutable Hub revision."""
import hashlib,json,os,shutil,time
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor
rev='c202236235762e1c871ad0ccb60c8ee5ba337b9a'
repo='Qwen/Qwen3.5-9B'
dest=Path('/tmp/g6i-qwen')
dest.mkdir(exist_ok=True)
metadata=requests.get(f'https://huggingface.co/api/models/{repo}/revision/{rev}?blobs=true',timeout=30)
metadata.raise_for_status()
data=metadata.json()
assert data['sha']==rev
source=Path.home()/'work/jev-g3b/cache'/repo/rev
def fetch(row):
    name=row['rfilename']
    path=dest/name
    if not name.endswith('.safetensors'):
        if (source/name).is_file():
            b=(source/name).read_bytes()
            def valid(b):
                if row.get('lfs'):return hashlib.sha256(b).hexdigest()==row['lfs']['sha256']
                return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==row['blobId']
            if not valid(b):
                response=requests.get(f'https://huggingface.co/{repo}/resolve/{rev}/{name}',timeout=60)
                response.raise_for_status()
                b=response.content
            assert valid(b),name
            path.write_bytes(b)
        return
    old=Path.home()/'g6a-cache-recovery/jev-g3b/cache'/repo/rev/(name+'.partial')
    if not path.exists():shutil.copyfile(old,path)
    for attempt in range(4):
        size=path.stat().st_size
        if size==row['size']:
            with path.open('rb') as f:
                if hashlib.file_digest(f,'sha256').hexdigest()==row['lfs']['sha256']:
                    print('verified',name,flush=True)
                    return
            path.unlink()
            path.touch()
            size=0
        url=f'https://huggingface.co/{repo}/resolve/{rev}/{name}?g6i={int(time.time())}'
        try:
            with requests.get(url,headers={'Range':f'bytes={size}-'},stream=True,timeout=(20,90)) as r:
                r.raise_for_status()
                if r.status_code==206:
                    assert r.headers['Content-Range'].startswith(f'bytes {size}-')
                with path.open('ab' if r.status_code==206 else 'wb') as f:
                    for chunk in r.iter_content(2**20):f.write(chunk)
        except requests.RequestException as e:
            print(name,type(e).__name__,flush=True)
    raise RuntimeError(name)
with ThreadPoolExecutor(3) as pool:list(pool.map(fetch,data['siblings']))
(dest/'VERIFIED').write_text(rev)
