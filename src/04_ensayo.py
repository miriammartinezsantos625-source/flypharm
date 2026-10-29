"""FLYPHARM · El ensayo: curva dosis-respuesta para cada fármaco."""
import sys, time; sys.path.insert(0,'src')
import pandas as pd, numpy as np
from simulador import Mosca
import farmacos as fx

UMBRAL, PASOS = 0.09, 60
neu = pd.read_feather('data/processed/neuronas.feather')
con = pd.read_feather('data/processed/conexiones.feather')
m = Mosca(neu, con, umbral=UMBRAL)
loom, moto = m.indices_por_tipo(['LC4','LPLC2']), m.motoneuronas

base = fx.medir(m.simular(loom, pasos=PASOS), moto)
print(f"MOSCA SOBRIA (control): latencia {base['latencia']} pasos · "
      f"{base['motoneuronas']} motoneuronas · {base['cerebro_activo']:.1f}% cerebro activo\n")

filas = []
DOSIS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
for nombre, info in fx.CATALOGO.items():
    print(f"{'='*72}\n{nombre.upper()}  —  {info['clase']}\n{info['nota']}")
    print(f"{'dosis':>6} {'latencia':>9} {'motoneuronas':>13} {'% cerebro':>10}   veredicto")
    for d in DOSIS:
        M, u = fx.aplicar(m, nombre, d)
        r = fx.medir(m.simular(loom, pasos=PASOS, umbral=u, M=M), moto)
        if   r['cerebro_activo'] > 60: v = "CONVULSIÓN"
        elif not r['escapa']:          v = "NO ESCAPA  <-- letal"
        elif r['latencia'] > base['latencia']: v = f"escapa, {r['latencia']-base['latencia']} pasos más lento"
        elif r['latencia'] < base['latencia']: v = f"escapa, {base['latencia']-r['latencia']} pasos MÁS RÁPIDO"
        else: v = "escapa normal"
        lat = r['latencia'] if r['latencia']>=0 else '--'
        print(f"{d:6.1f} {str(lat):>9} {r['motoneuronas']:13} {r['cerebro_activo']:9.1f}%   {v}")
        filas.append(dict(farmaco=nombre, dosis=d, **r))
    print()

pd.DataFrame(filas).to_csv('outputs/ensayo_dosis_respuesta.csv', index=False)
print("Guardado -> outputs/ensayo_dosis_respuesta.csv")
