"""
FLYPHARM · El simulador
========================
Un modelo "leaky integrate-and-fire" (integración y disparo con fugas).
La idea, en una frase: cada neurona va acumulando lo que recibe, se le escapa
un poco en cada instante, y si acumula suficiente, dispara.

Tres reglas, nada más:
  1. ACUMULA   V = V*decaimiento + entradas
  2. DISPARA   si V >= umbral  ->  spike, y V vuelve a 0
  3. DESCANSA  tras disparar, ignora todo durante unos pasos (refractario)

Lo único que sabemos de biología aquí es EL SIGNO: si una neurona suma o resta
a sus destinatarias. Y eso lo da su neurotransmisor.
"""
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

# ---------------------------------------------------------------------------
# El signo de cada neurotransmisor en Drosophila.
# Ojo con el glutamato: en mamíferos es EXCITADOR, pero en mosca actúa sobre
# canales de cloro (GluCl) y es mayoritariamente INHIBIDOR. Es el error clásico
# de quien viene de neurociencia de mamíferos.
SIGNO_NT = {
    'acetylcholine': +1,   # el excitador principal de la mosca (63% de neuronas)
    'dopamine':      +1,
    'octopamine':    +1,   # la "noradrenalina" de los insectos
    'serotonin':     +1,
    'gaba':          -1,
    'glutamate':     -1,   # inhibidor en mosca
    'histamine':     -1,   # inhibidor (fotorreceptores)
    'unclear':        0,   # 1,9% de neuronas: no inventamos, no contribuyen
}


class Mosca:
    def __init__(self, neuronas, conexiones, umbral=0.15, tau=5.0, refractario=2):
        self.neu = neuronas.reset_index(drop=True)
        self.N = len(self.neu)
        self.umbral = umbral
        self.decaimiento = np.exp(-1.0 / tau)   # cuánto se conserva cada paso
        self.refractario = refractario

        # bodyId (números gigantes) -> posición 0..N-1 en la matriz
        self.pos = pd.Series(np.arange(self.N), index=self.neu.bodyId.values)

        signo = self.neu.nt.map(SIGNO_NT).fillna(0).values.astype(np.float32)
        self.signo = signo

        pre = self.pos[conexiones.pre].values
        post = self.pos[conexiones.post].values
        peso = conexiones.peso.values.astype(np.float32)

        # NORMALIZACIÓN: dividimos por el total de sinapsis que recibe la neurona
        # de destino. Sin esto, una neurona con 100.000 entradas dispararía siempre
        # y una con 50 no dispararía nunca. Tras normalizar, "entrada = 1.0"
        # significa "todas mis entradas excitadoras han disparado a la vez".
        total_entrada = np.bincount(post, weights=peso, minlength=self.N)
        total_entrada[total_entrada == 0] = 1.0
        datos = signo[pre] * peso / total_entrada[post]

        # Matriz (destino x origen): entrada = M @ spikes
        self.M = csr_matrix((datos, (post, pre)), shape=(self.N, self.N))
        self.M_original = self.M.copy()   # copia limpia, para poder "lavar" el fármaco

    # -- utilidades para seleccionar poblaciones --------------------------------
    def indices_por_tipo(self, tipos):
        return self.neu.index[self.neu.type.isin(tipos)].values

    def indices_por_nt(self, nt):
        return self.neu.index[self.neu.nt == nt].values

    @property
    def motoneuronas(self):
        return self.neu.index[self.neu.superclass.isin(['vnc_motor', 'cb_motor'])].values

    # -- el bucle principal -----------------------------------------------------
    def simular(self, estimulo, pasos=100, duracion_estimulo=10, umbral=None, M=None):
        """estimulo: índices de neuronas a las que forzamos a disparar.
        Devuelve la matriz de disparos (pasos x N) como booleanos."""
        umbral = self.umbral if umbral is None else umbral
        Mat = self.M if M is None else M      # M = cerebro drogado
        V = np.zeros(self.N, dtype=np.float32)
        descanso = np.zeros(self.N, dtype=np.int8)
        s = np.zeros(self.N, dtype=np.float32)
        registro = np.zeros((pasos, self.N), dtype=bool)

        for t in range(pasos):
            entrada = Mat @ s                         # lo que llega por las sinapsis
            V = V * self.decaimiento + entrada        # 1. ACUMULA (con fugas)
            V[descanso > 0] = 0.0                     # 3. los que descansan, a cero
            V[V < 0] = 0.0                            # no modelamos hiperpolarización

            s = (V >= umbral).astype(np.float32)      # 2. DISPARA
            if t < duracion_estimulo:                 # el estímulo externo manda
                s[estimulo] = 1.0

            descanso = np.maximum(descanso - 1, 0)
            descanso[s > 0] = self.refractario
            V[s > 0] = 0.0                            # reset tras disparar

            registro[t] = s > 0
        return registro
