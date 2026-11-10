"""Consume verified tiles during transfer. File locks and per-tract receipts prevent duplicate processing."""
import csv,time,concurrent.futures as cf
import qualify as q
if __name__=='__main__':
    q.G=q.geoms(q.Path.home()/'work/jev-g6a/tl_2019_36_tract.zip');q.links={}
    for r in csv.DictReader(open('index_links.csv')):q.links.setdefault(r['geoid'],[]).append(r)
    pending={r['geoid']:r for r in csv.DictReader(open('baseline_coverage.csv'))};stop=time.monotonic()+3600
    with cf.ProcessPoolExecutor(4) as pool:
        while pending and time.monotonic()<stop:
            ready=[gid for gid in pending if all((q.out/(z['image']+'.json')).exists() for z in q.links.get(gid,[]))]
            if ready:
                list(pool.map(q.tract,[pending.pop(gid) for gid in ready]));print('qualified cumulative',483-len(pending),time.time(),flush=True)
            if pending:time.sleep(15)
