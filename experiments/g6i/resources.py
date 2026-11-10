"""Summarize receipted wall time and sampled device utilization."""
import json
from pathlib import Path
import pandas as pd

def summarize(base):
    root=base/'run'
    intervals={}
    for line in (root/'queue.log').read_text().splitlines():
        parts=line.split()
        if len(parts)==3 and parts[1] in ('start','completed'):
            intervals.setdefault(parts[2],{})[parts[1]]=pd.Timestamp(parts[0]).tz_localize(None)
    telemetry=root/'runs/utilization.csv'
    cols=['time','mib','util','watt']
    def load(path,header):
        d=pd.read_csv(path,names=cols,header=header,skipinitialspace=True)
        d['time']=pd.to_datetime(d.time)
        for col in cols[1:]:
            d[col]=pd.to_numeric(d[col].str.split().str[0])
        return d
    observations=load(telemetry,0)
    rows=[]
    for path in sorted((root/'runs').glob('*/receipt.json')):
        family=path.parent.name
        rec=json.loads(path.read_text())
        interval=intervals.get(family,{})
        if family=='qwen':
            mon=path.parent/'utilization.csv'
            d=load(mon,None) if mon.is_file() else observations.iloc[:0]
        elif 'completed' in interval:
            d=observations[observations.time.between(interval['start'],interval['completed'])]
        else:
            d=observations.iloc[:0]
        seconds=rec['seconds_this_invocation']
        windows=rec.get('windows',rec.get('dev_windows'))
        fit=rec.get('passes',0)*5196
        rows.append(dict(family=family,training_windows_seen=fit,dev_windows=windows,
                         steps=rec.get('steps_per_pass',0)*rec.get('passes',0),run_s=seconds,
                         end_to_end_windows_per_s=(fit+windows)/seconds,
                         estimated_active_cny_at_prior_rate=seconds*3/3600,
                         allocated_peak_gib=rec['peak_bytes']/2**30,monitor_observations=len(d),
                         sampled_device_mib_max=d.mib.max(),sampled_mean_utilization_pct=d.util.mean(),
                         approximate_gpu_kwh=d.watt.mean()*seconds/3600000))
    pd.DataFrame(rows).to_csv(base/'resources.csv',index=False)

if __name__=='__main__':summarize(Path('manifests/g6i'))
