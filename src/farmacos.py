"""
FLYPHARM · La farmacia
=======================
Un fármaco, en este modelo, es UNA operación sobre la matriz de conexiones.

Casi todo lo que hace un psicofármaco real se reduce a: "las neuronas que
liberan X, ahora pesan más (o menos)". Eso en la matriz es multiplicar las
columnas de esas neuronas por un factor. Nada más.

  dosis = 0.0  ->  mosca sobria
  dosis = 1.0  ->  bloqueo o potenciación completa del diana
"""
import numpy as np

CATALOGO = {
    'haloperidol': dict(
        clase='Antipsicótico · antagonista D2',
        diana='dopamine', efecto='bloquea',
        nota='Bloquea la señal dopaminérgica. Solo 392 neuronas de 164.587.'),
    'benzodiacepina': dict(
        clase='Ansiolítico · modulador positivo GABA-A',
        diana='gaba', efecto='potencia',
        nota='Potencia la inhibición existente. El mecanismo del diazepam.'),
    'curare': dict(
        clase='Bloqueante neuromuscular · antagonista colinérgico',
        diana='acetylcholine', efecto='bloquea',
        nota='Bloquea el excitador principal de la mosca (63% de las neuronas).'),
    'fluoxetina': dict(
        clase='ISRS · antidepresivo',
        diana='serotonin', efecto='potencia',
        nota='Amplifica la señal de solo 48 neuronas serotoninérgicas.'),
    'fipronil': dict(
        clase='INSECTICIDA COMERCIAL · bloqueante de canales de cloro',
        diana=('gaba', 'glutamate'), efecto='bloquea',
        nota='Mecanismo real del fipronil: bloquea GABA-A y GluCl. Quita los frenos.'),
    'cafeina': dict(
        clase='Estimulante · antagonista de adenosina',
        diana=None, efecto='umbral',
        nota='No toca un neurotransmisor: baja el umbral de disparo global.'),
}


def aplicar(mosca, farmaco, dosis, factor_max=3.0):
    """Devuelve (matriz_modificada, umbral_modificado) sin tocar la mosca original."""
    info = CATALOGO[farmaco]
    M = mosca.M_original.copy()
    umbral = mosca.umbral

    if info['efecto'] == 'umbral':
        # La cafeína hace a todas las neuronas más fáciles de excitar.
        umbral = mosca.umbral * (1 - 0.35 * dosis)
        return M, umbral

    dianas = info['diana'] if isinstance(info['diana'], tuple) else (info['diana'],)
    # Factor por neurona presináptica: 1.0 = intacta.
    factor = np.ones(mosca.N, dtype=np.float32)
    for d in dianas:
        idx = mosca.indices_por_nt(d)
        if info['efecto'] == 'bloquea':
            factor[idx] = 1.0 - dosis                      # 1 -> silencio total
        else:
            factor[idx] = 1.0 + dosis * (factor_max - 1)   # potenciación
    # M es (destino x origen): las columnas son las neuronas que EMITEN.
    M.data *= factor[M.indices]
    return M, umbral


def medir(registro, moto, n_min=20):
    """Traduce una simulación a las 3 métricas clínicas del ensayo."""
    por_paso = registro[:, moto].sum(axis=1)
    responde = por_paso >= 5
    return dict(
        latencia=int(np.argmax(responde)) if responde.any() else -1,   # tiempo de reacción
        motoneuronas=int(registro[:, moto].any(axis=0).sum()),          # fuerza de la respuesta
        cerebro_activo=100 * float(registro.any(axis=0).mean()),        # >60% = convulsión
        escapa=bool(registro[:, moto].any(axis=0).sum() >= n_min),
    )
