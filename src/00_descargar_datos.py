"""
FLYPHARM · Paso 0 — Descargar los datos públicos
=================================================
Los datos NO viven en este repositorio (pesan ~700 MB y no son míos): se bajan de
sus fuentes originales. Este script hace exactamente eso, y nada más.

  1) MaleCNS v1.0  (Janelia FlyEM + Cambridge + Google Research) · licencia CC-BY
     3 ficheros .feather de un bucket público de Google Cloud, ~566 MB.
     Se descartan a propósito los ~30 GB de coordenadas de sinapsis individuales:
     para simular no hacen falta.
  2) flybody       (HHMI Janelia + Google DeepMind) · licencia Apache-2.0
     Las mallas 3D del cuerpo de la mosca, ~140 MB. Se fija el commit exacto para
     que el resultado no cambie si el repositorio original se actualiza.

Uso:
    python3 src/00_descargar_datos.py              # descarga lo que falte
    python3 src/00_descargar_datos.py --comprobar  # solo comprueba que las URL responden
"""
import argparse, sys, time
from pathlib import Path
import requests

MALECNS_URL = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome"
MALECNS = [
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",                  # quién es cada neurona
    "body-neurotransmitters-male-cns-v1.0.feather",                        # su neurotransmisor
    "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",    # el cableado
]
FLYBODY_REPO = "TuragaLab/flybody"
FLYBODY_SHA = "d015e9bfe441bd90ae431bac24c55cb74bdbce26"          # versión fijada de flybody
FLYBODY_PREFIX = "flybody/fruitfly/assets/"

RAW, FLY = Path("data/raw"), Path("data/flybody")


def tamano_remoto(url):
    r = requests.head(url, allow_redirects=True, timeout=30)
    r.raise_for_status()
    return int(r.headers.get("Content-Length", 0))


def bajar(url, destino, comprobar=False, intentos=4):
    """Baja url -> destino. Salta lo que ya está completo. Reintenta si la red falla."""
    esperado = tamano_remoto(url)
    if destino.exists() and esperado and destino.stat().st_size == esperado:
        print(f"  ya está   {destino.name}")
        return esperado
    if comprobar:
        print(f"  {esperado/1e6:8.1f} MB  {destino.name}")
        return esperado
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".part")
    for n in range(1, intentos + 1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(parcial, "wb") as f:
                    for trozo in r.iter_content(chunk_size=1 << 20):
                        f.write(trozo)
            parcial.rename(destino)
            print(f"  bajado    {destino.name}  ({destino.stat().st_size/1e6:.1f} MB)")
            return esperado
        except (requests.RequestException, OSError) as e:
            print(f"  intento {n}/{intentos} falló en {destino.name}: {e}")
            time.sleep(2 * n)
    sys.exit(f"No se pudo descargar {url}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--comprobar", action="store_true", help="solo comprobar que las URL responden")
    comprobar = ap.parse_args().comprobar

    print("MaleCNS v1.0 (CC-BY) → data/raw/")
    total = sum(bajar(f"{MALECNS_URL}/{f}", RAW / f, comprobar) for f in MALECNS)
    print(f"  total MaleCNS: {total/1e6:.0f} MB\n")

    print(f"flybody @ {FLYBODY_SHA[:10]} (Apache-2.0) → data/flybody/")
    arbol = requests.get(f"https://api.github.com/repos/{FLYBODY_REPO}/git/trees/{FLYBODY_SHA}?recursive=1", timeout=60)
    arbol.raise_for_status()
    ficheros = [(i["path"], i.get("size", 0)) for i in arbol.json()["tree"]
                if i["type"] == "blob" and i["path"].startswith(FLYBODY_PREFIX)
                and i["path"].endswith((".obj", "fruitfly.xml"))]
    ficheros.append(("LICENSE", 0))
    raw = f"https://raw.githubusercontent.com/{FLYBODY_REPO}/{FLYBODY_SHA}"
    if comprobar:
        print(f"  {len(ficheros)} ficheros, {sum(s for _, s in ficheros)/1e6:.0f} MB en el árbol del commit")
    else:
        for ruta, _ in ficheros:
            bajar(f"{raw}/{ruta}", FLY / Path(ruta).name)
    print("\nListo. Siguiente paso:  python3 src/01_construir_dataset.py")


if __name__ == "__main__":
    main()
