#!/usr/bin/env python3
"""Build the private remaining-parts print view from checked native/sliced inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from holder_geometry import print_plate

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--system', type=Path, required=True)
    ap.add_argument('--holder-prep', type=Path)
    ap.add_argument('--outside-prep', type=Path)
    ap.add_argument('--overnight-prep', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    manifest = json.loads((a.system/'manifest.json').read_text())
    if manifest.get('incomplete') or not manifest['checks']['system']['pass']:
        raise ValueError('Current connected-system build has not passed')
    out = a.output.resolve()
    (out/'print').mkdir(parents=True, exist_ok=True)
    names = {p['id']: p['name'] for p in manifest['inventory']['parts']}
    plates = []
    if a.overnight_prep:
        recipes = [('overnight', a.overnight_prep)]
    elif a.holder_prep and a.outside_prep:
        recipes = [('holder', a.holder_prep), ('outside', a.outside_prep)]
    else:
        ap.error('Supply --overnight-prep or both --holder-prep and --outside-prep')
    native = {}
    for producer in manifest['producers'].values():
        native.update(producer['outputs_sha256'])
    for key, prep in recipes:
        record = json.loads((prep/'manifest.json').read_text())
        for name, item in record['artifacts'].items():
            if sha(prep/name) != item['sha256']:
                raise ValueError(f'{key}: changed preparation artifact {name}')
        parts = json.loads((prep/'plate-parts.json').read_text())
        for p in parts:
            path = Path(p['source_step'])
            if sha(path) != p['source_step_sha256'] or native[path.name] != p['source_step_sha256']:
                raise ValueError(f'{key}: {p["id"]} differs from the checked native build')
        job = 'critical-tree-slim'
        plate = print_plate(prep, job)
        for mesh in plate['meshes']:
            mesh['name'] = names[mesh['id']]
        plate.update(id=key, title={'overnight': 'Six remaining parts · one plate',
                                   'holder': 'Holder: five remaining parts',
                                   'outside': 'Outside handwheel: four parts'}[key])
        plate['downloads'] = {}
        for label, source, filename in [
                ('project', prep/job/f'{job}.3mf', f'{key}.3mf'),
                ('sliced', prep/job/'out'/f'{job}-sliced.3mf', f'{key}-sliced.3mf')]:
            shutil.copy2(source, out/'print'/filename)
            plate['downloads'][label] = f'print/{filename}'
        plates.append(plate)
    (out/'geometry.json').write_text(json.dumps({'plates': plates}, separators=(',', ':')))
    (out/'vendor').mkdir(exist_ok=True)
    shutil.copy2(HERE/'node_modules/three/build/three.module.js', out/'vendor/three.module.js')
    shutil.copy2(HERE/'node_modules/three/examples/jsm/controls/OrbitControls.js', out/'vendor/OrbitControls.js')
    for name in ['index.html', 'viewer.js']:
        shutil.copy2(HERE/'printing'/name, out/name)
    print(json.dumps({'output': str(out), 'parts': sum(len(p['meshes']) for p in plates)}))


if __name__ == '__main__':
    main()
