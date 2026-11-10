"""Freeze the roster, show exposure geography, independently verify source guards and record input versions."""
from design import O,E,M,geoms,digest,cfg
from pathlib import Path
import hashlib,json,sys,platform,importlib.metadata as meta
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
import shapely
root=Path(sys.argv[1])
geo=geoms(root/'tl_2019_36_tract.zip')
d=pd.read_csv(O/'reserve8_roster.csv',dtype={'geoid':str,'cell':str})
hist=pd.read_csv(O/'historical_exact_screen.csv',dtype={'geoid':str})
q=d[d.split=='test'].merge(hist,validate='one_to_one')
assert len(q)==267 and (q[['distance_window_ft','distance_source_ft']]>3600).all().all()
assert q[['overlapping_window_occurrences','overlapping_source_keys']].to_numpy().max()==0
cov=pd.read_csv(M/'g6e/coverage.csv',dtype={'geoid':str})
seal=cov[(cov.partition=='final')&(cov.selected==1)][['geoid','partition']]
assert len(seal)==74 and not set(seal.geoid)&set(d[d.split!='excluded'].geoid)
seal.to_csv(O/'original_seal_ids.csv',index=False)
fig,ax=plt.subplots(figsize=(8,8))
def layer(geoms,color):
    polys=[np.asarray(p.exterior.coords) for g in geoms for p in shapely.get_parts(g)]
    ax.add_collection(PolyCollection(polys,facecolor=color,edgecolor='none'))
layer([geo[i] for i in d.geoid],'#dedede')
layer([geo[i] for i in q.geoid],'#167993')
layer([geo[i] for i in seal.geoid],'#765792')
w=pd.read_csv(O/'historical_windows.csv')
layer([shapely.box(r.left,r.bottom,r.right,r.top) for r in w.itertuples()],'#bb5025')
ax.autoscale();ax.set_aspect('equal');ax.axis('off')
ax.legend(handles=[Patch(color=c,label=s) for c,s in [('#dedede','Strict frame'),('#167993','Prospective evaluation'),('#765792','Original seal'),('#bb5025','Historical image windows')]],loc='upper left',frameon=False)
fig.savefig(O/'historical_map.png',dpi=155,bbox_inches='tight');plt.close(fig)
sources=[M/'g6d/frame.json',M/'g6e/coverage.csv',M/'g6e/raster_checksums.txt',M/'g6c/patches.json',M/'g6c/full_tract.json',M/'g6d/windows/patches.json',*sorted((M/'g6c/whole').glob('*.tif'))[:1],M/'g6f/block_inventory.csv',O/'nyc_service_metadata.json']
provenance={'parent':'1166e09','python':platform.python_version(),'packages':{k:meta.version(k) for k in ['numpy','pandas','scipy','shapely','pyproj','pyshp','tifffile','matplotlib']},'inputs':{str(p):digest(p) for p in sources},'geometry':{p.name:{'sha256':digest(p),'url':'https://www2.census.gov/geo/tiger/TIGER'+p.name.split('_')[1]+'/TRACT/'+p.name} for p in sorted(root.glob('tl_*_36_tract.zip'))}}
(O/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(O/'frozen_proposal.json').write_text(json.dumps({'version':'G6G-NYC-proposal-1','decision':'A for eligible 267 only','design':'reserve8','roster_sha256':digest(O/'reserve8_roster.csv'),'standardization_weights_sha256':digest(O/'standardization_weights.csv'),'seed':cfg['allocation_seed'],'simulation_seed':cfg['simulation_seed'],'authorized_training':False,'old_seal_count':74,'fit':163,'dev':53,'test':267,'mean_balanced_evaluation':221},indent=2)+'\n')
