"""Zero-shot frozen RGB window composition on reserve8 development only."""
import hashlib,json,math,os,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from transformers import AutoModelForImageTextToText,AutoProcessor

MODEL=Path('/tmp/g6i-qwen')
PROMPT=('Estimate the area composition of this NYC aerial photograph. Ignore the neutral gray masked area. '
        'Give percentages of visible unmasked area in this exact order: tree canopy, grass or shrub, '
        'bare soil, water, buildings, roads, other impervious surfaces, railroad. '
        'Return only a JSON array of eight numbers summing to 100.')
def parse(raw):
    try:a=json.loads(raw.strip())
    except ValueError:return None
    if not isinstance(a,list) or len(a)!=8 or any(type(v) not in (float,int) or not math.isfinite(v) or v<0 or v>100 for v in a):return None
    if abs(sum(a)-100)>1:return None
    return [v*100/sum(a) for v in a]

def main():
    from importlib.metadata import version
    start=time.monotonic()
    assert (MODEL/'VERIFIED').read_text()=='c202236235762e1c871ad0ccb60c8ee5ba337b9a'
    out=Path('runs/qwen')
    out.mkdir(parents=True,exist_ok=True)
    pool=Path('prepared/dev.json')
    rows=[r for r in json.loads(pool.read_text()) if r['n']]
    assert all(Path(r['path']).parent.parent==Path('/tmp/g6i-reserve8/dev') for r in rows)
    config=dict(prompt=PROMPT,revision=(MODEL/'VERIFIED').read_text(),dtype='bf16',batch=4,
                dev_sha256=hashlib.sha256(pool.read_bytes()).hexdigest(),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                versions={k:version(k) for k in ['transformers','torch','torchvision','pillow','accelerate']},
                generation=dict(max_new_tokens=80,do_sample=False,enable_thinking=False))
    cfg=out/'config.json'
    if cfg.exists():assert json.loads(cfg.read_text())==config
    cfg.write_text(json.dumps(config))
    p=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
    p.tokenizer.padding_side='left'
    model=AutoModelForImageTextToText.from_pretrained(MODEL,dtype=torch.bfloat16,device_map={'':'cuda:0'},local_files_only=True).eval()
    @torch.inference_mode()
    def infer(images):
        msgs=[[dict(role='user',content=[dict(type='image',image=image),dict(type='text',text=PROMPT)])] for image in images]
        inputs=p.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,enable_thinking=False,padding=True,return_dict=True,return_tensors='pt').to('cuda',dtype=torch.bfloat16)
        output=model.generate(**inputs,do_sample=False,max_new_tokens=80)
        return p.batch_decode(output[:,inputs.input_ids.shape[1]:],skip_special_tokens=True)
    print('synthetic',infer([Image.new('RGB',(512,512),'green')]),flush=True)
    for offset in range(0,len(rows),4):
        target=out/f'batch_{offset:05}.json'
        if target.exists():continue
        batch=rows[offset:offset+4]
        images=[]
        for r in batch:
            a=np.load(r['path'])
            rgb=a[:,:,:3].copy()
            rgb[a[:,:,3]==0]=127
            images.append(Image.fromarray(rgb))
        raw=infer(images)
        assert len(raw)==len(batch)
        result=[dict(geoid=r['geoid'],x=r['x'],y=r['y'],area=r['n'],raw=s,shares=parse(s)) for r,s in zip(batch,raw)]
        tmp=target.with_suffix('.tmp')
        tmp.write_text(json.dumps(result))
        tmp.replace(target)
        if offset%100==0:print(offset,len(rows),flush=True)
    (out/'receipt.json').write_text(json.dumps(dict(windows=len(rows),seconds_this_invocation=time.monotonic()-start,peak_bytes=torch.cuda.max_memory_allocated())))
if __name__=='__main__':main()
