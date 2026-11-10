"""Hash immutable completed-family files once per release."""
import hashlib,json
from pathlib import Path
for receipt in Path('runs').glob('*/receipt.json'):
    folder=receipt.parent
    target=folder/'sha256.json'
    if target.exists():continue
    records={}
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name not in ('run.log','sha256.json','sha256.tmp'):
            with path.open('rb') as f:records[str(path.relative_to(folder))]=hashlib.file_digest(f,'sha256').hexdigest()
    temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(records))
    temp.replace(target)
