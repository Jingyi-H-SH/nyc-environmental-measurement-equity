"""Run one reserve8 family, with recovery at pass boundaries."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset,DataLoader
from models import Dense

SEED=62029
def digest(path):
    with open(path,'rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()

def atomic_json(path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data))
    temp.replace(path)

class Windows(Dataset):
    def __init__(self,split):
        assert split in ('train','dev')
        self.rows=[r for r in json.loads(Path(f'prepared/{split}.json').read_text()) if r['n']]
        for r in self.rows:
            assert Path(r['path']).parent.parent==Path('/tmp/g6i-reserve8')/split
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):
        r=self.rows[i]
        a=np.load(r['path'])
        y=a[:,:,3].copy()
        x=a[:,:,:3].copy()
        x[y==0]=127
        return torch.from_numpy(x.transpose(2,0,1)),torch.from_numpy(y),i

def run(family):
    start=time.monotonic()
    torch.manual_seed(SEED)
    torch.set_num_threads(2)
    torch.backends.cudnn.benchmark=False
    folder=Path('runs')/family
    folder.mkdir(exist_ok=True,parents=True)
    train,dev=Windows('train'),Windows('dev')
    ident={p:digest(p) for p in ['prepared/train.json','prepared/dev.json','run.py','models.py']}
    model=Dense(family).cuda()
    enc=set(model.encoder_parameters())
    opt=torch.optim.AdamW([{'params':[p for p in model.parameters() if p in enc and p.requires_grad],'lr':3e-5},
                           {'params':[p for p in model.parameters() if p not in enc and p.requires_grad],'lr':3e-4}],weight_decay=.01)
    checkpoint=folder/'checkpoint.pt'
    epoch0=0
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu')
        assert state['identity']==ident
        model.load_state_dict(state['weights'],strict=family!='ijepa')
        opt.load_state_dict(state['optimizer'])
        epoch0=state['passes']
    atomic_json(folder/'config.json',dict(identity=ident,seed=SEED,passes=8,batch=8,train=len(train),dev=len(dev),gpu=torch.cuda.get_device_name(),torch=torch.__version__,trainable=sum(p.numel() for p in model.parameters() if p.requires_grad),encoder_lr=.00003,head_lr=.0003,weight_decay=.01,mask_fill=127,loss='pixel cross entropy',precision='bfloat16 autocast'))
    model.eval()
    with torch.no_grad(),torch.autocast('cuda',torch.bfloat16):
        probe=model(torch.zeros(1,3,512,512,device='cuda'))
        assert torch.isfinite(probe).all()
    print('SMOKE PASS',family,flush=True)
    for epoch in range(epoch0,8):
        torch.manual_seed(SEED+epoch)
        loader=DataLoader(train,batch_size=8,shuffle=True,generator=torch.Generator().manual_seed(SEED+epoch),num_workers=3,pin_memory=True)
        model.train()
        for step,(x,y,_) in enumerate(loader):
            target=y.cuda().long()-1
            opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',torch.bfloat16):
                logits=model(x.cuda().float()/255)
                loss=torch.nn.functional.cross_entropy(logits,target,ignore_index=-1)
            if not torch.isfinite(loss):raise RuntimeError('nonfinite fitting loss')
            loss.backward()
            opt.step()
            if step%100==0:print('fit',epoch+1,step,len(loader),round(loss.item(),4),flush=True)
        weights={k:v for k,v in model.state_dict().items() if family!='ijepa' or not k.startswith('model.')}
        tmp=folder/'checkpoint.tmp'
        torch.save(dict(weights=weights,optimizer=opt.state_dict(),identity=ident,passes=epoch+1),tmp)
        tmp.replace(checkpoint)
    model.eval()
    conf={}
    with torch.no_grad(),torch.autocast('cuda',torch.bfloat16):
        for x,y,idx in DataLoader(dev,batch_size=8,num_workers=3):
            pred=model(x.cuda().float()/255).argmax(1).cpu().numpy()
            for i,ref,hat in zip(idx.tolist(),y.numpy(),pred):
                r=dev.rows[i]
                valid=ref>0
                cm=np.bincount((ref[valid].astype(int)-1)*8+hat[valid],minlength=64).reshape(8,8)
                assert cm.sum()==r['n']
                gid=r['geoid']
                conf.setdefault(gid,np.zeros((8,8),dtype=np.int64))
                conf[gid]+=cm
                out=folder/'predictions'/gid
                out.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(out/f"{r['x']}_{r['y']}.npz",labels=np.where(valid,hat+1,0).astype('uint8'))
    assert len(conf)==53
    atomic_json(folder/'tract_confusion.json',{gid:cm.tolist() for gid,cm in conf.items()})
    atomic_json(folder/'receipt.json',dict(seconds_this_invocation=time.monotonic()-start,peak_bytes=torch.cuda.max_memory_allocated(),checkpoint_sha256=digest(checkpoint),passes=8,steps_per_pass=(len(train)+7)//8,dev_windows=len(dev)))

if __name__=='__main__':run(sys.argv[1])
