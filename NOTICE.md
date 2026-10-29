# Atribuciones y licencias de terceros

FlyPharm no existiría sin datos y código abiertos de otros. Esto es lo que se usa, bajo qué licencia y qué se ha cambiado.

## Datos del conectoma — MaleCNS v1.0 (CC-BY)

- **Referencia:** Berg S, Beckett IR, Costa M, Schlegel P, Januszewski M, Marin EC, Nern A, *et al.* (111 autores; último: Jefferis GSXE). *Sexual dimorphism in the complete Drosophila male central nervous system connectome.* **Cell** 2026;189(18):5504-5526.e15. doi:[10.1016/j.cell.2026.08.015](https://doi.org/10.1016/j.cell.2026.08.015)
- **Creado por:** HHMI Janelia FlyEM, University of Cambridge (Dept. of Zoology), MRC Laboratory of Molecular Biology y Google Research.
- **Licencia:** CC-BY, según <https://male-cns.janelia.org/download/>.
- **Origen de los ficheros:** `gs://flyem-male-cns/v1.0/connectome-data/flat-connectome/` (los descarga `src/00_descargar_datos.py`; no se redistribuyen en bruto).
- **Cambios realizados** (`web/datos.json` es una obra derivada): se conservan las conexiones de ≥5 sinapsis; se reduce a 31.000 neuronas (todas las motoneuronas, sensoriales, descendentes y neuromoduladoras, más las mejor conectadas); las coordenadas se cuantizan a 16 bits; todo se reempaqueta en un único JSON.
- Esto no implica respaldo de FlyPharm por parte de los autores del conectoma.

## Cuerpo 3D — flybody (Apache-2.0)

- **Referencia:** Vaxenburg R, *et al.* *Whole-body physics simulation of fruit fly locomotion.* **Nature** 2025. <https://www.nature.com/articles/s41586-025-09029-4>
- **Creado por:** HHMI Janelia Research Campus y Google DeepMind. Código y mallas: <https://github.com/TuragaLab/flybody> (commit fijado en `src/00_descargar_datos.py`).
- **Licencia:** Apache-2.0. Copia en [`data/flybody/LICENSE`](data/flybody/LICENSE).
- **Cambios realizados** (`web/mosca3d.json` es una obra derivada): 85 mallas reducidas de 272.550 a 52.020 triángulos; colores sustituidos por una paleta oscura; se descartan las capas de pelo y cerdas; la animación (batido de alas, patas recogidas, marcha, muerte) es propia y no procede de la física de flybody.

## Bibliotecas y tipografías (se cargan desde CDN, no se redistribuyen)

- **Three.js** r152 — MIT — vía cdnjs.
- **IBM Plex** (Sans, Sans Condensed, Mono) — SIL Open Font License 1.1 — vía Google Fonts.
