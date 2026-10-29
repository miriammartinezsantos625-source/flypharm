"""FLYPHARM · Decima las mallas de flybody (Janelia/DeepMind, Apache-2.0) y las
empaqueta con su árbol cinemático en un JSON que Three.js pueda posar."""
import xml.etree.ElementTree as ET, numpy as np, json, base64, re
from pathlib import Path
import trimesh, fast_simplification

D = Path('data/flybody'); OUT = Path('web/mosca3d.json')
r = ET.parse(D/'fruitfly.xml').getroot()

# --- escala por defecto de las mallas y materiales ---
esc_def = np.array([0.1,0.1,0.1])
for d in r.iter('default'):
    m = d.find('mesh')
    if m is not None and m.get('scale'): esc_def = np.array(list(map(float, m.get('scale').split())))
meshes = {m.get('name'): m.attrib for m in r.iter('mesh') if m.get('name')}
materiales = {m.get('name'): m.get('rgba') for m in r.iter('material') if m.get('name')}
print("materiales:", materiales)

# Presupuesto de triángulos por pieza (a ojo de lo que el navegador agradece)
def presupuesto(nombre):
    n = nombre.lower()
    if 'head_red' in n: return 5000
    if 'head' in n: return 3500
    if 'thorax' in n: return 3500
    if 'wing' in n and 'membrane' in n: return 600
    if 'wing' in n: return 1200
    if 'abdomen' in n: return 500
    if 'claw' in n: return 150
    if any(k in n for k in ('tarsus','tibia','femur','coxa')): return 320
    if 'antenna' in n: return 400
    if 'haltere' in n: return 150
    return 400

def color_de(nombre, rgba):
    if rgba: return rgba
    n = nombre.lower()
    if 'red' in n: return '0.69 0.20 0.16 1'
    if 'ocelli' in n: return '0.45 0.12 0.10 1'
    if 'black' in n: return '0.16 0.12 0.09 1'
    if 'membrane' in n: return '0.82 0.87 0.93 0.28'
    if 'wing' in n: return '0.36 0.26 0.16 0.9'
    if 'brown' in n or 'claw' in n: return '0.32 0.22 0.13 1'
    if 'lower' in n: return '0.78 0.64 0.45 1'
    return '0.63 0.47 0.31 1'          # cutícula

def b64(a): return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()

cache = {}
def malla(nombre):
    if nombre in cache: return cache[nombre]
    info = meshes[nombre]; f = D/info['file']
    m = trimesh.load(f, force='mesh', process=False)
    esc = np.array(list(map(float, info['scale'].split()))) if info.get('scale') else esc_def
    v = np.asarray(m.vertices, dtype=np.float64) * esc
    fc = np.asarray(m.faces, dtype=np.int64)
    obj = presupuesto(nombre)
    if len(fc) > obj:
        v, fc = fast_simplification.simplify(v.astype(np.float32), fc.astype(np.int32), target_count=obj)
        v = v.astype(np.float64); fc = fc.astype(np.int64)
    lo, hi = v.min(0), v.max(0); rango = np.where(hi-lo>0, hi-lo, 1)
    q = np.round((v-lo)/rango*65535).astype(np.uint16)
    out = dict(name=nombre, nv=int(len(v)), nf=int(len(fc)), min=lo.tolist(), max=hi.tolist(),
               pos=b64(q), idx=b64(fc.astype(np.uint16 if len(v)<65536 else np.uint32)),
               idx32=bool(len(v)>=65536))
    cache[nombre] = (out, len(m.faces)); return cache[nombre]

def num(s, n): return list(map(float, s.split())) if s else ([0]*n if n==3 else [1,0,0,0])
def euler2quat(e):   # 'xyz' intrínseco, radianes (MuJoCo por defecto)
    from scipy.spatial.transform import Rotation as R
    q = R.from_euler('XYZ', e).as_quat()  # x y z w
    return [q[3], q[0], q[1], q[2]]

partes = []
def walk(b, padre):
    nombre = b.get('name')
    quat = num(b.get('quat'),4) if b.get('quat') else (euler2quat(num(b.get('euler'),3)) if b.get('euler') else [1,0,0,0])
    geoms = []
    for g in b.findall('geom'):
        if not g.get('mesh'): continue
        gq = num(g.get('quat'),4) if g.get('quat') else (euler2quat(num(g.get('euler'),3)) if g.get('euler') else [1,0,0,0])
        rgba = g.get('rgba') or materiales.get(g.get('material'))
        geoms.append(dict(mesh=g.get('mesh'), pos=num(g.get('pos'),3), quat=gq, rgba=color_de(g.get('mesh'), rgba)))
        malla(g.get('mesh'))
    joints = [dict(name=j.get('name'), axis=num(j.get('axis'),3) if j.get('axis') else [0,0,1],
                   range=num(j.get('range'),2) if j.get('range') else None) for j in b.findall('joint')]
    partes.append(dict(name=nombre, parent=padre, pos=num(b.get('pos'),3), quat=quat, geoms=geoms, joints=joints))
    for c in b.findall('body'): walk(c, nombre)
raiz = r.find('worldbody').find('body')
walk(raiz, None)

tri_orig = sum(v[1] for v in cache.values()); tri_fin = sum(v[0]['nf'] for v in cache.values())
json.dump(dict(fuente='flybody · TuragaLab (HHMI Janelia + Google DeepMind) · Apache-2.0',
               partes=partes, mallas=[v[0] for v in cache.values()]), open(OUT,'w'))
print(f"{len(partes)} cuerpos · {len(cache)} mallas · triángulos {tri_orig:,} -> {tri_fin:,}")
print(f"{OUT}: {OUT.stat().st_size/1e6:.2f} MB")
