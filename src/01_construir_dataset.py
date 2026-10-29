"""
FLYPHARM · Paso 1 — Construir el dataset de trabajo
====================================================
Partimos de 3 ficheros crudos de MaleCNS v1.0 (566 MB) y producimos
2 ficheros limpios y pequeños con los que trabajaremos siempre.

La idea: los datos crudos se tocan UNA vez. Todo lo demás parte de lo limpio.
Así si metes la pata más adelante, no tienes que volver a descargar 500 MB.
"""
import pyarrow.feather as ft
import numpy as np
import pandas as pd
from pathlib import Path

RAW = Path('data/raw')
OUT = Path('data/processed')
OUT.mkdir(parents=True, exist_ok=True)

# Umbral de sinapsis. Una conexión de 1-2 sinapsis entre dos neuronas puede ser
# ruido del algoritmo de reconstrucción. El estándar en el campo es quedarse con
# las de >=5, que conserva el 72% de las sinapsis con solo el 24% de las aristas.
UMBRAL_PESO = 5

print("[1/4] Cargando el cableado...")
con = ft.read_table(RAW/'connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather',
                    columns=['body_pre', 'body_post', 'weight']).to_pandas()
con = con.rename(columns={'body_pre': 'pre', 'body_post': 'post', 'weight': 'peso'})

# Las neuronas de nuestro universo: las que aparecen en el grafo.
neuronas_grafo = np.union1d(con.pre.unique(), con.post.unique())
print(f"      {len(con):,} conexiones entre {len(neuronas_grafo):,} neuronas")

print(f"[2/4] Filtrando conexiones con peso >= {UMBRAL_PESO}...")
con = con[con.peso >= UMBRAL_PESO].reset_index(drop=True)
print(f"      quedan {len(con):,} conexiones")

print("[3/4] Cargando neurotransmisores y anotaciones...")
# Neurotransmisor: nos quedamos con una fila por neurona.
nt = ft.read_table(RAW/'body-neurotransmitters-male-cns-v1.0.feather',
                   columns=['body', 'consensus_nt', 'predicted_nt_confidence']).to_pandas()
nt = nt.drop_duplicates('body').rename(
    columns={'body': 'bodyId', 'consensus_nt': 'nt', 'predicted_nt_confidence': 'nt_conf'})

# Anotaciones: quién es cada neurona.
ann = ft.read_table(RAW/'body-annotations-male-cns-v1.0-minconf-0.5.feather',
                    columns=['bodyId', 'type', 'class', 'superclass', 'somaSide']).to_pandas()

# Construimos la tabla de neuronas: SOLO las que están en el grafo.
neu = pd.DataFrame({'bodyId': neuronas_grafo})
neu = neu.merge(ann, on='bodyId', how='left').merge(nt, on='bodyId', how='left')
neu['nt'] = neu['nt'].fillna('unclear')

print("[4/4] Diagnóstico de cobertura (¿sabemos quién es quién?)")
print(f"      neuronas en el grafo : {len(neu):,}")
print(f"      con 'type' conocido  : {neu['type'].notna().sum():,}  "
      f"({100*neu['type'].notna().mean():.1f}%)")
print(f"      con 'class' conocida : {neu['class'].notna().sum():,}  "
      f"({100*neu['class'].notna().mean():.1f}%)")
print("\n      LA FARMACIA (neurotransmisor de las neuronas del grafo):")
for k, v in neu.nt.value_counts().items():
    print(f"         {k:16} {v:8,}  ({100*v/len(neu):5.2f}%)")

neu.to_feather(OUT/'neuronas.feather')
con.to_feather(OUT/'conexiones.feather')
print(f"\nGuardado -> {OUT}/neuronas.feather  ({len(neu):,} filas)")
print(f"Guardado -> {OUT}/conexiones.feather ({len(con):,} filas)")
