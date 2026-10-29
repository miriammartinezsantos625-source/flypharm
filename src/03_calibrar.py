"""Barrido de umbrales: buscamos la ventana donde la mosca responde sin convulsionar."""
import sys, time; sys.path.insert(0, 'src')
import pandas as pd, numpy as np
from simulador import Mosca

neu = pd.read_feather('data/processed/neuronas.feather')
con = pd.read_feather('data/processed/conexiones.feather')
print("Construyendo el cerebro..."); t0 = time.time()
m = Mosca(neu, con)
print(f"   listo en {time.time()-t0:.1f}s · {m.N:,} neuronas · {m.M.nnz:,} sinapsis\n")

loom = m.indices_por_tipo(['LC4', 'LPLC2'])      # la sombra que se acerca
moto = m.motoneuronas
gf   = m.indices_por_tipo(['DNp01'])
print(f"Estímulo: {len(loom)} neuronas LC4+LPLC2 | Salida: {len(moto)} motoneuronas\n")

print(f"{'umbral':>7} {'% cerebro activo':>17} {'disparos GF':>12} {'motoneur. activas':>18} {'latencia':>9}")
print("-"*70)
for u in [0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.40]:
    r = m.simular(loom, pasos=60, duracion_estimulo=10, umbral=u)
    activo = 100 * r.any(axis=0).mean()
    disp_gf = int(r[:, gf].sum())
    mn_act = int(r[:, moto].any(axis=0).sum())
    # latencia: primer paso con al menos 5 motoneuronas disparando a la vez
    por_paso = r[:, moto].sum(axis=1)
    lat = np.argmax(por_paso >= 5) if (por_paso >= 5).any() else -1
    marca = ""
    if activo > 60: marca = "  <- convulsión"
    elif mn_act < 10: marca = "  <- no responde"
    print(f"{u:7.2f} {activo:16.1f}% {disp_gf:12} {mn_act:18} {lat:9}{marca}")
