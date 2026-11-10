"""One disjoint, bounded early validation of complete tiles (before the main tract pass)."""
import csv,sys
import qualify as q
if __name__=='__main__':
    q.G=q.geoms(q.Path.home()/'work/jev-g6a/tl_2019_36_tract.zip');q.links={}
    for r in csv.DictReader(open('index_links.csv')):q.links.setdefault(r['geoid'],[]).append(r)
    rows=[r for r in csv.DictReader(open('baseline_coverage.csv')) if all((q.out/(z['image']+'.json')).exists() for z in q.links[r['geoid']])]
    with q.cf.ProcessPoolExecutor(3) as pool:list(pool.map(q.tract,rows))
    print('verified tract native reference and terrestrial counts:',len(rows))
