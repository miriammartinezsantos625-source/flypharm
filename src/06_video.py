"""FLYPHARM · El vídeo: seis moscas, seis fármacos, un matamoscas."""
import sys; sys.path.insert(0,'src')
import pyarrow.feather as ft, pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle
from matplotlib.animation import FuncAnimation, FFMpegWriter
from simulador import Mosca
import farmacos as fx

PASOS, ESTIM, UMBRAL, N_DIBUJO = 70, 10, 0.09, 45000
FONDO, TINTA, TINTA2, APAGADA = '#101014', '#ffffff', '#a8a89e', '#33333a'

CONDICIONES = [
    ('Mosca sobria',   None,             0.0, '#7a7a85'),
    ('Haloperidol',    'haloperidol',    1.0, '#199e70'),
    ('Benzodiacepina', 'benzodiacepina', 1.0, '#d95926'),
    ('Curare',         'curare',         0.4, '#3987e5'),
    ('Cafeína',        'cafeina',        0.8, '#22a822'),
    ('Fipronil',       'fipronil',       1.0, '#d55181'),
]
SUBTITULO = {
    'Mosca sobria':   'control',
    'Haloperidol':    'antipsicótico · bloquea dopamina',
    'Benzodiacepina': 'ansiolítico · potencia GABA',
    'Curare':         'paralizante · bloquea acetilcolina',
    'Cafeína':        'estimulante · baja el umbral',
    'Fipronil':       'INSECTICIDA · quita los frenos',
}

# ---------------------------------------------------------------- datos
print("Cargando cerebro...")
neu = pd.read_feather('data/processed/neuronas.feather')
con = pd.read_feather('data/processed/conexiones.feather')
m = Mosca(neu, con, umbral=UMBRAL)
loom, moto = m.indices_por_tipo(['LC4','LPLC2']), m.motoneuronas

ann = ft.read_table('data/raw/body-annotations-male-cns-v1.0-minconf-0.5.feather',
                    columns=['bodyId','somaLocation']).to_pandas()
ann = ann[ann.somaLocation.apply(lambda v: isinstance(v,(list,np.ndarray)) and len(v)==3)]
coord = dict(zip(ann.bodyId.values, ann.somaLocation.values))
tiene = neu.bodyId.map(lambda b: b in coord).values
idx_con_coord = np.where(tiene)[0]
XYZ = np.vstack([coord[b] for b in neu.bodyId.values[idx_con_coord]]).astype(float)
X, Z = XYZ[:,0], XYZ[:,2]          # proyección X-Z: cerebro arriba, médula abajo

rng = np.random.default_rng(0)
sel = rng.choice(len(idx_con_coord), size=min(N_DIBUJO,len(idx_con_coord)), replace=False)
g_idx, gX, gZ = idx_con_coord[sel], X[sel], Z[sel]
es_moto = np.isin(g_idx, moto)
print(f"   {len(g_idx):,} neuronas dibujadas ({es_moto.sum()} motoneuronas)")

# ---------------------------------------------------------------- simulaciones
regs, met = {}, {}
for nom, far, dosis, _ in CONDICIONES:
    M, u = (m.M_original, m.umbral) if far is None else fx.aplicar(m, far, dosis)
    r = m.simular(loom, pasos=PASOS, duracion_estimulo=ESTIM, umbral=u, M=M)
    regs[nom], met[nom] = r, fx.medir(r, moto)
    print(f"   {nom:16} latencia={met[nom]['latencia']:>3}  "
          f"motoneuronas={met[nom]['motoneuronas']:>3}  "
          f"cerebro={met[nom]['cerebro_activo']:.1f}%")

GOLPE = 8          # el matamoscas cae en el paso 8

def desenlace(nom):
    """¿Esquiva o la golpean? Y por qué."""
    r = met[nom]
    convulsiona = r['cerebro_activo'] > 60
    lat = r['latencia']
    # Un escape necesita COORDINACIÓN. Un cerebro al 77% no escapa: convulsiona.
    esquiva = (lat >= 0) and (lat < GOLPE) and not convulsiona
    if convulsiona:   txt, col = 'CONVULSIONA', '#ff6b6a'
    elif lat < 0:     txt, col = 'PARALIZADA', '#ff6b6a'
    elif not esquiva: txt, col = 'LLEGA TARDE', '#ffc24d'
    else:             txt, col = 'ESQUIVA', '#7ee38a'
    return esquiva, convulsiona, txt, col

# ---------------------------------------------------------------- lienzo
fig = plt.figure(figsize=(15.4, 10.4), facecolor=FONDO)
gs = fig.add_gridspec(2, 3, left=.025, right=.975, top=.845, bottom=.075,
                      hspace=.30, wspace=.08)
paneles = []
for i, (nom, far, dosis, color) in enumerate(CONDICIONES):
    sub = gs[i//3, i%3].subgridspec(2, 1, height_ratios=[5.0, 2.3], hspace=0.04)
    ax, axf = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
    for a in (ax, axf):
        a.set_facecolor(FONDO); a.set_xticks([]); a.set_yticks([])
        for s in a.spines.values(): s.set_visible(False)
    ax.scatter(gX, gZ, s=.35, c=APAGADA, lw=0, zorder=1)          # cerebro apagado
    viva = ax.scatter([], [], s=2.6, c=color, lw=0, zorder=2)      # neuronas activas
    mviva = ax.scatter([], [], s=42, c='#ffffff', lw=0, zorder=4,  # motoneuronas
                       marker='o', alpha=.95)
    ax.set_xlim(gX.min()-3000, gX.max()+3000)
    ax.set_ylim(gZ.max()+6000, gZ.min()-6000)                     # invertido: cerebro arriba
    ax.set_aspect('equal')
    ax.text(.5, 1.105, nom, transform=ax.transAxes, color=color, fontsize=15.5,
            fontweight='bold', ha='center')
    ax.text(.5, 1.048, SUBTITULO[nom], transform=ax.transAxes, color=TINTA2,
            fontsize=9.5, ha='center')

    # -- la escena: la mosca y el matamoscas --
    axf.set_xlim(0, 10); axf.set_ylim(-0.1, 3.4)
    axf.axhline(0.20, color='#32323c', lw=3, zorder=0)
    pala = Rectangle((2.6, 3.0), 4.6, 0.30, color='#5c5c68', zorder=5)
    mango = Rectangle((4.75, 3.3), 0.30, 1.2, color='#5c5c68', zorder=5)
    axf.add_patch(pala); axf.add_patch(mango)
    cuerpo = Ellipse((5, .62), 1.15, .80, color='#f2f2ea', zorder=4)
    ala1 = Ellipse((4.62, 1.02), 1.05, .38, angle=24, color='#cfd8e8', alpha=.55, zorder=3)
    ala2 = Ellipse((5.38, 1.02), 1.05, .38, angle=-24, color='#cfd8e8', alpha=.55, zorder=3)
    for q in (ala1, ala2, cuerpo): axf.add_patch(q)
    txt = axf.text(9.7, 2.5, '', fontsize=11.5, fontweight='bold',
                   ha='right', va='center', color=TINTA2)
    paneles.append(dict(nom=nom, viva=viva, mviva=mviva, txt=txt, color=color,
                        cuerpo=cuerpo, alas=[ala1, ala2], pala=pala, mango=mango))

tit = fig.text(.5, .955, '', color=TINTA, fontsize=25, fontweight='bold', ha='center')
sub_t = fig.text(.5, .912, '', color=TINTA2, fontsize=12.5, ha='center')
pie = fig.text(.5, .028, 'Conectoma MaleCNS v1.0 · 164.587 neuronas y 6,2 M de conexiones reales · '
               'simulación integrate-and-fire · las dosis son unidades arbitrarias',
               color='#6a6a72', fontsize=9.5, ha='center')

# ---------------------------------------------------------------- animación
INTRO, CIERRE = 12, 26
TOTAL = INTRO + PASOS + CIERRE

def frame(k):
    tt = k - INTRO
    if tt < 0:
        tit.set_text('Seis moscas. Seis fármacos. Un matamoscas.')
        sub_t.set_text('el matamoscas cae en el paso 8...'); sub_t.set_color(TINTA2)
        return []
    tp = min(tt, PASOS - 1)
    if tt < GOLPE:
        tit.set_text(f'⚠  EL MATAMOSCAS CAE EN {GOLPE - tt}')
        sub_t.set_text('estimulando LC4 + LPLC2, los detectores de peligro')
        sub_t.set_color('#ffc24d')
    else:
        tit.set_text('Seis moscas. Seis fármacos. Un matamoscas.')
        sub_t.set_text(f'paso {tp + 1} de {PASOS}'); sub_t.set_color(TINTA2)

    for p in paneles:
        s = regs[p['nom']][tp]
        act = s[g_idx]
        p['viva'].set_offsets(np.c_[gX[act], gZ[act]])
        mm = act & es_moto
        p['mviva'].set_offsets(np.c_[gX[mm], gZ[mm]])

        esquiva, convulsiona, vtxt, vcol = desenlace(p['nom'])
        lat = met[p['nom']]['latencia']

        # --- el matamoscas baja ---
        caida = min(tt / GOLPE, 1.0)
        y_pala = 3.0 - caida * (3.0 - (0.95 if esquiva else 0.34))
        p['pala'].set_y(y_pala); p['mango'].set_y(y_pala + 0.30)

        # --- la mosca ---
        cu, (a1, a2) = p['cuerpo'], p['alas']
        if esquiva and tt >= lat:
            av = min((tt - lat) / 7.0, 1.0)
            x, y = 5 + 3.7 * av, 0.62 + 1.55 * av
            cu.set_center((x, y)); cu.height = 0.80
            cu.set_color('#f2f2ea')
            for a, dx in zip((a1, a2), (-0.38, 0.38)):
                a.set_center((x + dx, y + 0.40))
                a.set_alpha(0.30 + 0.35 * abs(np.sin(tt * 1.5)))
        elif convulsiona and tt < GOLPE:
            j = 0.20 * np.sin(tt * 4.1), 0.14 * np.sin(tt * 6.3)   # temblor
            cu.set_center((5 + j[0], 0.62 + j[1]))
            for a, dx in zip((a1, a2), (-0.38, 0.38)):
                a.set_center((5 + dx + j[0], 1.02 + j[1])); a.set_alpha(0.55)
        elif tt >= GOLPE:                                          # aplastada
            cu.set_center((5, 0.28)); cu.height = 0.18
            cu.set_color('#ff6b6a')
            for a in (a1, a2):
                a.set_center((a.center[0], 0.30)); a.set_alpha(0.18)

        if tt >= GOLPE:
            p['txt'].set_text(vtxt); p['txt'].set_color(vcol)
    return []

print("\nRenderizando vídeo...")
anim = FuncAnimation(fig, frame, frames=TOTAL, interval=110, blit=False)
anim.save('outputs/flypharm.mp4', writer=FFMpegWriter(fps=9, bitrate=4200,
          codec='libx264', extra_args=['-pix_fmt','yuv420p']), dpi=100)
print("Guardado -> outputs/flypharm.mp4")
