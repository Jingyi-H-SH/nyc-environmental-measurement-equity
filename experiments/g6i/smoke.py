import json,sys,time
import torch
from models import Dense
family=sys.argv[1]
start=time.monotonic()
torch.manual_seed(62029)
m=Dense(family).cuda()
with torch.autocast('cuda',torch.bfloat16):
    logits=m(torch.rand(2,3,512,512,device='cuda'))
    loss=torch.nn.functional.cross_entropy(logits, torch.randint(8,(2,512,512),device='cuda'))
loss.backward()
assert torch.isfinite(loss) and any(p.grad is not None and p.grad.abs().sum().item()>0 for p in m.parameters())
print(json.dumps(dict(family=family,shape=list(logits.shape),loss=float(loss.detach()),seconds=time.monotonic()-start,peak_bytes=torch.cuda.max_memory_allocated())))
