"""Bounded five public NYC borough archives; range-resume with pinned ETag and exact length."""
import concurrent.futures as cf, os, pathlib, requests, time, zipfile, json
root=pathlib.Path('/tmp/g6h-ortho');root.mkdir(exist_ok=True)
base='https://s3.amazonaws.com/sa-static-customer-assets-us-east-1-fedramp-prod/data.cityofnewyork.us/Map_Downloads/2016_orthos/boro_{}_sp16.zip'
def fetch(arg):
    name,url,tag,n,a,b=arg;p=root/f'{name}.{a}.ok'; dest=root/f'{name}.part'
    if p.exists() and p.read_text()==tag and dest.stat().st_size==n:return
    for i in range(4):
        try:
            r=requests.get(url,headers={'Range':f'bytes={a}-{b}','If-Match':tag},timeout=(15,80))
            assert r.status_code==206 and r.headers['Content-Range']==f'bytes {a}-{b}/{n}' and len(r.content)==b-a+1
            with dest.open('r+b') as f:f.seek(a);f.write(r.content)
            p.write_text(tag);return
        except Exception:
            if i==3:raise
            time.sleep(1+i)
def main():
    jobs=[]; meta={}
    pin=pathlib.Path('archive_sources.pinned.json');pin=json.loads(pin.read_text()) if pin.exists() else None
    for name in ['bronx','manhattan','brooklyn','queens','staten_island']:
        url=base.format(name);r=requests.get(url,headers={'Range':'bytes=0-0'},timeout=30);r.raise_for_status()
        n=int(r.headers['Content-Range'].split('/')[-1]);tag=r.headers['ETag'];meta[name]=dict(url=url,etag=tag,bytes=n)
        if pin is not None and meta[name]!=pin[name]:raise ValueError('public archive revision changed: '+name)
        if (root/f'{name}.zip').exists():
            assert (root/f'{name}.zip').stat().st_size==n;continue
        part=root/f'{name}.part'
        if not part.exists() or part.stat().st_size!=n:
            for marker in root.glob(name+'.*.ok'):marker.unlink()
        with (root/f'{name}.part').open('ab') as f:f.truncate(n)
        jobs.extend((name,url,tag,n,a,min(n-1,a+(8<<20)-1)) for a in range(0,n,8<<20))
    print(json.dumps(meta),flush=True);pathlib.Path('archive_sources.json').write_text(json.dumps(meta,indent=2))
    with cf.ThreadPoolExecutor(12) as pool:
        for i,_ in enumerate(pool.map(fetch,jobs)):
            if i%100==0:print(i,len(jobs),time.time(),flush=True)
    for name in meta:
        p=root/f'{name}.part'
        if p.exists():
            with zipfile.ZipFile(p) as z:assert z.namelist()
            p.rename(root/f'{name}.zip')
if __name__=='__main__':main()
