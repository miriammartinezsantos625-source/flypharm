"""FLYPHARM · Exporta un conectoma reducido que quepa en un navegador."""
import pyarrow.feather as ft, pandas as pd, numpy as np, json, base64
from pathlib import Path

OBJ, OUT = 31000, Path('web')
neu = pd.read_feather('data/processed/neuronas.feather')
con = pd.read_feather('data/processed/conexiones.feather')
ann = ft.read_table('data/raw/body-annotations-male-cns-v1.0-minconf-0.5.feather',
                    columns=['bodyId','somaLocation','somaSide']).to_pandas()
ann['ok'] = ann.somaLocation.apply(lambda v: isinstance(v,(list,np.ndarray)) and len(v)==3)
coord = dict(zip(ann.bodyId[ann.ok], ann.somaLocation[ann.ok]))
lado = dict(zip(ann.bodyId, ann.somaSide.fillna('')))
neu['coord'] = neu.bodyId.isin(coord)
neu['lado'] = neu.bodyId.map(lado).fillna('')

t, sc = neu.type.fillna(''), neu.superclass.fillna('')
ES_MOTO = sc.isin(['vnc_motor','cb_motor'])
ES_LOOM = t.str.match(r'^(LC4|LPLC2)$')
imprescindible = (ES_MOTO | ES_LOOM | sc.isin(['descending_neuron','ascending_neuron'])
                  | sc.str.contains('sensory') | neu.nt.isin(['dopamine','serotonin','octopamine']))

grado = con.groupby('pre').peso.sum().add(con.groupby('post').peso.sum(), fill_value=0)
neu['grado'] = neu.bodyId.map(grado).fillna(0)
relleno = neu.index[(~imprescindible) & neu.coord].values
relleno = relleno[np.argsort(-neu.grado.values[relleno])][:max(0, OBJ - int(imprescindible.sum()))]
sel = np.union1d(neu.index[imprescindible].values, relleno)
assert len(sel) < 65536, "los índices deben caber en Uint16"

sub = neu.loc[sel].reset_index(drop=True)
mapa = pd.Series(np.arange(len(sub)), index=sub.bodyId.values)
ids = set(sub.bodyId)
e = con[con.pre.isin(ids) & con.post.isin(ids)].copy()
e['i'], e['j'] = mapa[e.pre].values, mapa[e.post].values
e = e.sort_values(['j','i'])                      # CSR por neurona de DESTINO
print(f"{len(sub):,} neuronas · {len(e):,} conexiones · "
      f"{int(ES_MOTO[sel].sum())} motoneuronas · {int(ES_LOOM[sel].sum())} detectores de peligro")

N, E = len(sub), len(e)
indptr = np.zeros(N+1, dtype=np.int32)
np.add.at(indptr, e.j.values + 1, 1); indptr = np.cumsum(indptr).astype(np.int32)
indices = e.i.values.astype(np.uint16)
pesos = np.clip(e.peso.values, 0, 65535).astype(np.uint16)

# posiciones 3D escaladas a 0..10000 (Uint16) con la MISMA escala en los tres ejes
# (para no deformar la anatomía). 65535 = sin coordenada.
xs = np.full(N, 65535, dtype=np.uint16); ys = np.full(N, 65535, dtype=np.uint16); zs = np.full(N, 65535, dtype=np.uint16)
hay = sub.bodyId.map(lambda b: b in coord).values
xyz = np.vstack([coord[b] for b in sub.bodyId.values[hay]]).astype(float)
lo = xyz.min(0); rango = (xyz.max(0)-lo).max()
q = np.round((xyz - lo) / rango * 10000).astype(np.uint16)
xs[hay], ys[hay], zs[hay] = q[:,0], q[:,1], q[:,2]

GRUPOS = ['acetylcholine','gaba','glutamate','histamine','dopamine','serotonin','octopamine','unclear']
ntg = sub.nt.map({g:i for i,g in enumerate(GRUPOS)}).fillna(7).values.astype(np.uint8)
banderas = (ES_MOTO[sel].values.astype(np.uint8) * 1
            + ES_LOOM[sel].values.astype(np.uint8) * 2
            + (sub.lado.values == 'L').astype(np.uint8) * 4
            + (sub.lado.values == 'R').astype(np.uint8) * 8)

with open(OUT/'net.bin','wb') as f:
    f.write(indptr.tobytes()); f.write(indices.tobytes()); f.write(pesos.tobytes())
with open(OUT/'nodes.bin','wb') as f:
    f.write(xs.tobytes()); f.write(ys.tobytes()); f.write(zs.tobytes()); f.write(ntg.tobytes()); f.write(banderas.tobytes())
json.dump(dict(N=int(N), E=int(E), grupos=GRUPOS, coords3d=True,
               n_moto=int(ES_MOTO[sel].sum()), n_loom=int(ES_LOOM[sel].sum()),
               fuente='MaleCNS v1.0 · Janelia FlyEM + Google Research',
               total_neuronas=164587, total_conexiones=6235682),
          open(OUT/'meta.json','w'), ensure_ascii=False)
for f in ['net.bin','nodes.bin','meta.json']:
    print(f"   {(OUT/f).stat().st_size/1e6:7.2f} MB  {f}")

# datos.json: la app carga el conectoma entero desde UN json (net y nodes en base64),
# porque los .bin no se pueden servir como tipo web estándar en un Artifact.
meta = json.load(open(OUT/'meta.json'))
meta['net']   = base64.b64encode((OUT/'net.bin').read_bytes()).decode()
meta['nodes'] = base64.b64encode((OUT/'nodes.bin').read_bytes()).decode()
json.dump(meta, open(OUT/'datos.json','w'), ensure_ascii=False)
print(f"   {(OUT/'datos.json').stat().st_size/1e6:7.2f} MB  datos.json")
