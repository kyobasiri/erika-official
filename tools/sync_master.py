"""Copy the frontend's master catalog into the Cloud Run build context."""
from pathlib import Path
import json
import shutil

base = Path(__file__).resolve().parents[1]
source = base / 'public/assets/game-master.json'
target = base / 'GoogleCloudRun/erika-action-api/game-master.json'
data = json.loads(source.read_text(encoding='utf-8'))
assert len(data['enemies']) >= 7, 'at least seven enemies are required'
assert len(data['bosses']) == 12, 'exactly twelve bosses are required'
assert len(data['stages']) >= 6, 'at least six stages are required'
assert len({e['type'] for e in data['enemies']}) == len(data['enemies'])
assert len({e['id'] for e in data['bosses']}) == len(data['bosses'])
shutil.copy2(source, target)
print(f'Synced {len(data["enemies"])} enemies, {len(data["bosses"])} bosses, {len(data["stages"])} stage themes.')
