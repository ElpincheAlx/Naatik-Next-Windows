# Dependencias del port Windows

Revisión: 2026-10-21. No se distribuyen ruedas, runtimes Microsoft, modelos,
fuentes ni diccionarios. Se preservan versión y hashes del código fuente de origen
en `SOURCE_SNAPSHOT.json`. Los requisitos Linux archivados no acreditan ruedas Windows.
Las importaciones de la aplicación solo usan QtCore, QtGui, QtWidgets y QtNetwork;
[PySide6 Essentials](https://pypi.org/project/PySide6-Essentials/6.11.1/) los incluye.

## Base

Versiones exactas en `../locks/base-windows.in`; se conserva el motor de traducción
mínimo del proyecto original, usando descubrimiento/tokenizadores de Argos sin
importar su capa SBD ni descargar spaCy/Stanza. Por ello no se instala todo el
grafo declarado de Argos ni se acredita un `pip check` global de ese metapaquete.
Sí se prueban sus imports realmente usados. `colorama` cubre Click en Windows.

| Paquete | Versión | Uso | Licencia declarada / fuente |
| --- | --- | --- | --- |
| PySide6 Essentials, Shiboken6 | 6.11.1 | Interfaz, captura, IPC | [LGPL/GPL/comercial](https://doc.qt.io/qtforpython-6/licenses.html); revisar componentes Qt antes de redistribuir |
| Pillow | 12.3.0 | Imágenes y prueba OCR | [MIT-CMU](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| argostranslate | 1.11.0 | Paquetes y tokenización | [MIT](https://github.com/argosopentech/argos-translate/blob/master/LICENSE) |
| ctranslate2 | 4.8.1 | Inferencia CPU | [MIT](https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE) |
| sentencepiece | 0.2.2 | Tokenización | [Apache-2.0](https://github.com/google/sentencepiece/blob/master/LICENSE) |
| sacremoses | 0.1.1 | BPE | [MIT](https://github.com/hplt-project/sacremoses/blob/master/LICENSE) |
| numpy | 2.5.2 | Arrays | [BSD y avisos de componentes](https://github.com/numpy/numpy/blob/main/LICENSE.txt) |
| click | 8.4.2 | Dependencia de sacremoses | [BSD-3-Clause](https://github.com/pallets/click/blob/main/LICENSE.txt) |
| joblib | 1.5.3 | Dependencia de sacremoses | [BSD-3-Clause](https://github.com/joblib/joblib/blob/main/LICENSE.txt) |
| packaging | 26.3 | Versionado | [Apache-2.0/BSD](https://github.com/pypa/packaging/blob/main/LICENSE) |
| PyYAML | 6.0.3 | Configuración de CTranslate2 | [MIT](https://github.com/yaml/pyyaml/blob/main/LICENSE) |
| regex | 2026.7.19 | Tokenización | [Apache/CNRI](https://pypi.org/project/regex/) |
| setuptools | 84.0.0 | Compatibilidad y construcción | [MIT](https://github.com/pypa/setuptools/blob/main/LICENSE) |
| tqdm | 4.70.0 | Dependencia de sacremoses | [MPL/MIT](https://github.com/tqdm/tqdm/blob/master/LICENCE) |
| colorama | 0.4.6 | Consola de Click en Windows | [BSD-3-Clause](https://github.com/tartley/colorama/blob/master/LICENSE.txt) |

El runtime Visual C++ es un prerrequisito externo, con licencia Microsoft propia;
[CTranslate2 lo requiere en Windows](https://opennmt.net/CTranslate2/installation.html).
No se incluye ni se descarga un instalador de Microsoft desde este código.

## Componentes nativos

Captura, atajos y supervisión utilizan Qt y APIs del sistema mediante ctypes,
sin nuevas dependencias pip: [QScreen](https://doc.qt.io/qtforpython-6.11/PySide6/QtGui/QScreen.html),
[RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey),
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[msvcrt](https://docs.python.org/3.13/library/msvcrt.html).
La semántica de usuario de QLocalServer se documenta en
[QLocalServer](https://doc.qt.io/qtforpython-6.11/PySide6/QtNetwork/QLocalServer.html).

## Opcionales y recursos

- Tesseract 5: ejecutable externo, Apache-2.0; la versión exacta y los idiomas se
  detectan y prueban localmente. Sus datos tienen licencia propia. No se instala
  ni redistribuye un binario no verificado. [Fuente oficial](https://github.com/tesseract-ocr/tesseract).
- MangaOCR 0.1.16: Apache-2.0, [fuente](https://github.com/kha-white/manga-ocr).
  Torch 2.13.0+cpu se solicita al índice CPU oficial; Transformers 5.14.1 y resto de
  versiones semilla figuran en `manga-windows.in`. Se exige `torch.version.cuda is None`.
  El cierre y la carga del runtime se comprobaron en Windows el 2026-10-22.
  La inferencia con modelo sigue pendiente de preparación explícita.
- Fugashi 1.5.2: [MIT](https://github.com/polm/fugashi/blob/master/LICENSE).
  UniDic Lite 1.0.8: datos UniDic con sus avisos propios,
  [fuente y condiciones](https://github.com/polm/unidic-lite). No heredar MIT del motor.
  Se construye su sdist con setuptools/packaging/wheel fijados por versión/hash.
- Manga-ocr-base: identidad, revisión, tamaños, SHA-256 y fuente/licencia de cada
  snapshot conservados en `naatik_next/model-catalog.json`. No se copia el modelo.
- Argos: cada paquete se prepara explícitamente por el asistente y se registra su
  integridad. El estado de licencia de los modelos no se deduce de MIT del motor.
- AnkiConnect: integración HTTP local existente; no se distribuye Anki ni su addon.
- Fuentes: se usan las instaladas en Windows a través de Qt. No se incluyen fuentes.

Los informes pip guardados al preparar cada modo contienen metadatos, versiones,
URLs y hashes de los archivos seleccionados; el instalador rechaza orígenes no
permitidos y hashes ausentes. Las licencias/NOTICE de ruedas Windows y de sus
componentes embebidos **no están auditadas para redistribución**; antes de publicar
un paquete deben contrastarse sus textos y conservarse los avisos aplicables.
El instalador usa los informes para fijar el cierre, no como autorización de licencia.


## Revisión Windows del 22 de octubre de 2026

- Python privado: CPython 3.13.17 x64, paquete oficial
  https://api.nuget.org/v3-flatcontainer/python/3.13.17/python.3.13.17.nupkg
  SHA-256: `dce409744b088f94c6e37ba41f8100c384c27e029e843237364c602d30d475e5`.
  Procedimiento oficial: https://docs.python.org/3.13/using/windows.html#the-nuget-org-packages .
  Licencia PSF y componentes propios: https://docs.python.org/3.13/license.html .
  Se descarga/extraye en el equipo del usuario; no se incorpora el binario a este ZIP.
  Sus avisos se conservan sin modificar. No actualizable in situ: para cambiar versión
  hay que renovar origen/hash y recrear los entornos, conservando perfiles.
- Los workers de la base añaden únicamente el directorio DLL del PySide6 de su
  propio entorno mediante `os.add_dll_directory`; no copian DLL ni buscan otros
  proyectos. Permite cargar SentencePiece sin importar Qt en el worker.
  La distribución Qt existente conserva sus DLL y avisos. El runtime separado
  también puede usar el Qt de la base propia `.venv`; si ninguno está disponible,
  requiere Visual C++ x64 instalado en el sistema.
- MangaOCR: Torch CPU se obtiene exclusivamente de la URL fijada en
  `locks/manga-windows.in`. Las otras dependencias se resuelven solo con PyPI,
  para evitar artefactos del espejo PyTorch sin SHA-256. No se relajó la validación.
- `win32-setctime` es un paquete Python puro válido: la plataforma se valida
  por la etiqueta final de la rueda, no por palabras contenidas en su nombre.
- Evidencia de resolución: `locks/base-report.json`, `phrase-report.json`,
  `manga-report.json` y sus locks con SHA-256. No se redistribuyen ruedas ni
  modelos. La auditoría de avisos para una futura distribución binaria sigue pendiente.

- Imagen de diagnóstico `examples/nihon.png`: creada para esta revisión con el
  texto 日本 y Pillow, renderizando Yu Gothic Medium instalado en Windows.
  No se redistribuye el archivo de fuente ni un modelo. SHA-256 de la imagen: `09fba2f802eccb753cc9a07416715d192c39971a8d807740c9893ff01239e3b5`.


## Instalador 1.0
El ejecutable contiene el código de la aplicación y su instalador, sin ruedas,
Python, modelos ni fuentes. Utiliza .NET Framework y PowerShell del sistema.
Las dependencias se descargan al instalar usando las versiones, orígenes y
hashes documentados anteriormente. La compilación usa csc de .NET Framework
de Windows; no se incorpora un framework redistribuido. El ejecutable no está
firmado con un certificado de editor.
