# Na’atik Next 1.0 — Windows · Español / English

Aplicación local de OCR, traducción, diccionarios y Anki para Windows 10/11 x64.

### Instalador 1.0

Abre `Naatik-Next-1.0-Setup.exe`, elige **Español / English** y pulsa
**Instalar / reparar**. Antes de pulsarlo no descarga ni instala nada; puedes
cerrar la ventana para cancelar. Requiere Internet para Python y dependencias.
Después abre **Na’atik Next** desde el menú Inicio. Los modelos y diccionarios
se preparan por separado, con confirmación, desde el tutorial o las pestañas.

El tutorial aparece en perfiles nuevos. Puedes omitirlo y retomarlo desde Ayuda;
omitirlo no instala ni acredita recursos. `--capture` no abre el tutorial.
**Configuración → Idioma** guarda el idioma por perfil: se aplica al volver a
abrir la aplicación cuando tú decidas. No cambia el idioma OCR ni la ruta de
traducción. Reparar conserva preferencias y preselecciona el idioma guardado.
Consulta [validación de esta entrega](docs/VALIDACION-1.0.txt) para los límites reales.

### English quick start

Open `Naatik-Next-1.0-Setup.exe`, choose **English**, then click **Install / repair**.
No download or installation begins before that click. Close the window to cancel
before installation. Internet is required for Python and dependencies. Open
**Na’atik Next** from Start afterwards. Models and dictionaries require separate,
explicit preparation in the tutorial or application tabs.

New profiles receive the tutorial; skip it and resume from Help at any time.
Skipping does not install or certify resources. Capture mode does not open it.
**Settings → Language** saves your choice for the next launch, without forcing a
restart or changing OCR/translation languages. Repair preserves profile data.
See [release validation](docs/VALIDACION-1.0.txt): automated and offscreen tests
do not certify a complete interactive installation or global desktop shortcuts.

### Desarrollo y fuentes / Source development

El procedimiento siguiente prepara las fuentes directamente. Para la selección
visual previa de idioma usa el EXE. Para preparar las fuentes en inglés, establece
`$env:NAATIK_UI_LANGUAGE='en'` antes de `powershell -ExecutionPolicy Bypass -File install.ps1`.
Para reconstruir, prepara `.venv` y ejecuta
`powershell -ExecutionPolicy Bypass -File packaging/build.ps1 -OutputDirectory dist`.
El alcance de `-ExecutionPolicy Bypass` es ese proceso, no cambia la política del sistema.

Copia independiente de la aplicación actual, incluidos Anki y Apariencia.
Objetivo: **Windows 10/11 x64, CPython 3.13 estándar, CPU**.
Estado: instalación base y análisis japonés comprobados en Windows; pruebas Qt offscreen.
Captura de escritorio, OCR con modelos y traducción con modelos requieren comprobación interactiva.
El instalador incluye las fuentes, pero descarga el entorno; no es portable ni
un paquete sin conexión. La validación interactiva completa sigue pendiente.

## Empezar en Windows

1. Copia esta carpeta a una ubicación tuya con permiso de escritura.
2. Extrae todo el ZIP antes de ejecutar archivos. No lo abras desde dentro del ZIP.
3. Ejecuta `install.cmd` y espera al mensaje «Entorno preparado». Después ejecuta `launch.cmd`.

El instalador encuentra Python 3.13 x64 aunque no exista `py`. Si no lo encuentra,
descarga Python 3.13.17 oficial de NuGet, verifica su SHA-256 y lo prepara en `.python`.
No modifica PATH ni necesita administrador. La extracción inicial puede tardar varios minutos.
Si la red bloquea NuGet, instala Python 3.13 x64 desde python.org y repite.
Para un intérprete explícito, configura `NAATIK_PYTHON` con la ruta a `python.exe`.
El archivo `install.log` conserva el diagnóstico; `launch.log` conserva los errores de apertura.
No muevas la carpeta después de instalar: los entornos Python contienen rutas absolutas;
si necesitas otra ubicación, extrae allí el ZIP fuente y ejecuta de nuevo el instalador.

CTranslate2 requiere el [runtime Microsoft Visual C++ x64](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
Si falta, instálalo desde Microsoft. La primera instalación necesita Internet.
Las siguientes aperturas usan el entorno local; no consultan PyPI ni catálogos.

En el asistente, elige Tesseract ya instalado o prepara MangaOCR CPU y su modelo
japonés con los botones de la interfaz. MangaOCR es opcional y considerablemente
más pesado que la base. El instalador no incluye modelos ni traduce antes de que
hayas preparado una ruta local de traducción. Para Tesseract, la
[documentación oficial](https://tesseract-ocr.github.io/tessdoc/Installation.html)
remite a las compilaciones Windows de UB Mannheim; instala los idiomas deseados.
Se detecta el ejecutable en PATH y en `Program Files\Tesseract-OCR`.

El flujo se conserva: **capturar región → reconocer y copiar → abrir Translator
con su atajo actual**. Soltar la región no abre Translator automáticamente.
Configura los atajos en Integraciones y deja Next en la bandeja para reutilizar
los workers y modelos cargados. Anki conserva revisión editable y envío explícito.

## Equivalencias implementadas

| Linux | Windows |
| --- | --- |
| Spectacle/KDE/X11 | Selector regional propio con Qt `QScreen.grabWindow`; sin programa de captura externo |
| libX11 / XGrabKey | Win32 `RegisterHotKey`, sin repetición ni hook de teclado |
| Socket Unix | Named pipes de Qt, restringidas al usuario, con protocolo limitado |
| Grupos POSIX / señales | Job Objects con cierre de procesos descendientes |
| `fcntl.flock` | Bloqueos de archivos de `msvcrt`, biblioteca estándar |
| XDG y `.venv/bin/python` | Perfil propio en LOCALAPPDATA y `.venv\Scripts\python.exe` |
| Scripts Bash / `.desktop` | Lanzadores `.cmd` / PowerShell |
| Qt completo | PySide6 Essentials + Shiboken: solo módulos utilizados |
| OCR/traducción locales | Tesseract/MangaOCR y Argos/CTranslate2 CPU locales |

Perfil: `%LOCALAPPDATA%\NaatikNextWindows\{config,data,state}`.
`NAATIK_WINDOWS_PROFILE` admite una ruta absoluta para perfiles de prueba.
No se descubren ni reutilizan entornos, configuración, modelos o diccionarios de
`Naatik-next`, JapaneseMining ni otras instalaciones. Desinstalar la carpeta de
código no elimina el perfil.

## Instalación y pruebas reproducibles

`locks/*-windows.in` fija las versiones semilla. En la primera preparación de cada
modo, el instalador pide a pip un informe de resolución Windows, valida orígenes y
SHA-256, guarda `locks/*-windows.lock` y `*-report.json`, y luego instala con
`--no-deps --require-hashes`. Las reinstalaciones usan ese lock existente.
Esta entrega incluye locks e informes de resolución obtenidos en Windows para base,
frase, traducción separada y MangaOCR. Las fuentes y versiones no se actualizan automáticamente.
Torch CPU se fija mediante URL y hash propios, sin usar su índice para otros paquetes.
El instalador admite rutas largas de Windows y repara entornos cuya preparación no terminó.
Los locks Linux de `docs/upstream-*` son solamente evidencia del origen.

Para preparar opcionales desde consola, también existen `install.cmd --phrase`
y `install.cmd --manga-cpu`; los botones de la interfaz invocan el mismo instalador.
Los modelos se preparan separadamente con integridad y consentimiento explícito.
No hay PaddleOCR, comparador manual ni OCR remoto en el flujo de captura.

Pruebas desde la carpeta, después de instalar la base:

```powershell
.venv\Scripts\python.exe tools\verify_windows.py
```

El script crea un perfil temporal y usa Qt offscreen. No accede a tu colección de
Anki. El workflow `.github/workflows/windows.yml` prepara instalación y pruebas
en un runner Windows cuando este port tenga su propio repositorio.
La captura está limitada a una región dentro de un monitor por operación.
Revisar [VALIDATION.md](docs/VALIDATION.md) para la validación pendiente de DPI,
monitores y escritorio. Inventario y fuentes en
[THIRD_PARTY_DEPENDENCIES.md](docs/THIRD_PARTY_DEPENDENCIES.md).

## Preparar funciones después de instalar
El asistente de primer inicio muestra instrucciones según el motor seleccionado. Tesseract incluye enlace al instalador y selección de idiomas; MangaOCR separa instalación y descarga del modelo. Las rutas existentes se pueden cambiar en Opciones avanzadas. Pulsa Comprobar OCR antes de guardar. Para volver al asistente utiliza la opción de configuración inicial de la aplicación.


## Tutorial y configuración inicial

Los perfiles nuevos abren un tutorial con los asistentes de preparación existentes.
Puedes usar «Omitir por ahora», cerrar para posponer o retomarlo desde
«Ayuda → Tutorial y configuración inicial». Consulta [el recorrido y su persistencia](docs/TUTORIAL.md).
Esta revisión entrega fuentes actualizadas; el instalador EXE está pendiente de
reconstruir y validar en Windows.
