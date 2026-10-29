"""FLYPHARM · La figura: curvas dosis-respuesta."""
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

d = pd.read_csv('outputs/ensayo_dosis_respuesta.csv')
SUP, TINTA, TINTA2, GRIS, ROJO = '#fcfcfb', '#0b0b0b', '#52514e', '#d8d7d3', '#a8302f'
COLOR = {'curare':'#2a78d6','benzodiacepina':'#eb6834','haloperidol':'#1baf7a',
         'fluoxetina':'#eda100','fipronil':'#e87ba4','cafeina':'#008300'}
NOMBRE = {'curare':'Curare','benzodiacepina':'Benzodiacepina','haloperidol':'Haloperidol',
          'fluoxetina':'Fluoxetina','fipronil':'Fipronil','cafeina':'Cafeína'}
ORDEN = ['curare','benzodiacepina','haloperidol','fluoxetina','cafeina','fipronil']


def etiquetas_sin_choques(ax, items, hueco=0.052):
    """items = [(y_datos, texto, color)] -> las separa verticalmente y las dibuja."""
    inv = ax.transAxes.inverted()
    ys = [inv.transform(ax.transData.transform((0, y)))[1] for y, _, _ in items]
    orden = np.argsort(ys)
    colocadas = {}
    ultimo = -9.0
    for i in orden:                                   # de abajo a arriba
        y = max(ys[i], ultimo + hueco)
        colocadas[i] = y; ultimo = y
    for i, (_, txt, c) in enumerate(items):
        ax.annotate(txt, (1.015, colocadas[i]), xycoords='axes fraction',
                    color=c, fontsize=10.5, fontweight='bold', va='center',
                    annotation_clip=False)


fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 11.2), facecolor=SUP,
                             gridspec_kw=dict(hspace=0.34))
BANDA = 11.4
for ax in (a1, a2):
    ax.set_facecolor(SUP)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRIS)
    ax.tick_params(colors=TINTA2, length=3, labelsize=10)
    ax.grid(axis='y', color=GRIS, lw=0.6, alpha=0.7); ax.set_axisbelow(True)
    ax.set_xlim(-0.03, 1.06); ax.set_xticks([0, .2, .4, .6, .8, 1.0])

# ---------------- PANEL 1 · tiempo de reacción ----------------
a1.axhspan(BANDA - 1.0, BANDA + 1.0, color='#e34948', alpha=0.08, zorder=0)
a1.text(0.012, BANDA, 'NO ESCAPA · parálisis', color=ROJO, fontsize=9.5, va='center',
        fontweight='bold', bbox=dict(fc=SUP, ec='none', pad=2.0), zorder=5)
et = []
for f in ORDEN:
    g = d[d.farmaco == f].sort_values('dosis'); c = COLOR[f]
    vivo, muerto = g[g.latencia >= 0], g[g.latencia < 0]
    a1.plot(vivo.dosis, vivo.latencia, color=c, lw=2, marker='o', ms=8,
            mec=SUP, mew=1.6, zorder=3, solid_capstyle='round')
    if len(muerto):
        a1.plot(muerto.dosis, [BANDA] * len(muerto), ls='none', marker='X', ms=11,
                color=c, mec=SUP, mew=1.6, zorder=4)
        et.append((BANDA, NOMBRE[f], c))
    else:
        et.append((vivo.latencia.iloc[-1], NOMBRE[f], c))
a1.axhline(6, color=TINTA2, lw=1, ls=(0, (4, 3)), zorder=1)
a1.text(0.012, 6.0, 'mosca sobria', color=TINTA2, fontsize=9, style='italic',
        va='center', bbox=dict(fc=SUP, ec='none', pad=2.0), zorder=5)
a1.set_ylim(2.2, 12.9); a1.set_yticks([3, 4, 5, 6, 7, 8, 9])
a1.set_ylabel('Tiempo de reacción\n(pasos hasta mover el músculo)', color=TINTA, fontsize=10.5)
a1.set_title('Cuánto tarda la mosca en huir', color=TINTA, fontsize=14.5,
             fontweight='bold', loc='left', pad=30)
a1.text(0, 1.035, 'más arriba = más lenta = más vulnerable', transform=a1.transAxes,
        color=TINTA2, fontsize=10)
etiquetas_sin_choques(a1, et)

# ---------------- PANEL 2 · cerebro activo ----------------
a2.axhspan(60, 100, color='#e34948', alpha=0.08, zorder=0)
a2.text(0.012, 74, 'CONVULSIÓN', color=ROJO, fontsize=9.5, va='center',
        fontweight='bold', bbox=dict(fc=SUP, ec='none', pad=2.0), zorder=5)
et = []
for f in ORDEN:
    g = d[d.farmaco == f].sort_values('dosis'); c = COLOR[f]
    a2.plot(g.dosis, g.cerebro_activo, color=c, lw=2, marker='o', ms=8,
            mec=SUP, mew=1.6, zorder=3, solid_capstyle='round')
    et.append((g.cerebro_activo.iloc[-1], NOMBRE[f], c))
a2.axhline(10.9, color=TINTA2, lw=1, ls=(0, (4, 3)), zorder=1)
a2.text(0.012, 10.9, 'mosca sobria', color=TINTA2, fontsize=9, style='italic',
        va='center', bbox=dict(fc=SUP, ec='none', pad=2.0), zorder=5)
a2.set_ylim(-3, 86); a2.set_yticks([0, 20, 40, 60, 80])
a2.yaxis.set_major_formatter(lambda v, p: f'{v:.0f}%')
a2.set_ylabel('Cerebro activo\n(% de las 164.587 neuronas)', color=TINTA, fontsize=10.5)
a2.set_xlabel('Dosis   0 = sin fármaco · 1 = bloqueo o potenciación completa',
              color=TINTA, fontsize=10.5, labelpad=9)
a2.set_title('Cuánto cerebro se enciende', color=TINTA, fontsize=14.5,
             fontweight='bold', loc='left', pad=30)
a2.text(0, 1.035, 'demasiado = pérdida de control', transform=a2.transAxes,
        color=TINTA2, fontsize=10)
etiquetas_sin_choques(a2, et)

fig.suptitle('Seis fármacos sobre un cerebro completo de mosca', color=TINTA,
             fontsize=19, fontweight='bold', x=0.052, ha='left', y=0.977)
fig.text(0.052, 0.944, 'Conectoma MaleCNS v1.0 · 164.587 neuronas · 6,2 M de conexiones '
         'reales · reflejo de escape de la Giant Fiber', color=TINTA2, fontsize=10.5)
fig.text(0.052, 0.016, 'Simulación integrate-and-fire sobre conectividad real. '
         'Dosis en unidades arbitrarias, no mg/kg.', color=TINTA2, fontsize=9)
fig.subplots_adjust(top=0.885, bottom=0.072, left=0.118, right=0.805)
fig.savefig('outputs/dosis_respuesta.png', dpi=130, facecolor=SUP)
print("Guardado -> outputs/dosis_respuesta.png")
