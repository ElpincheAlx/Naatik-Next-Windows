# Validación del port Windows

Fecha: 2026-10-21. Objetivo Windows 10/11 x64 / CPython 3.13 estándar.

## Evidencia ejecutada en Fedora

- Compilación sintáctica de aplicación, herramientas y tests: correcta.
- `tools/verify_windows.py`: 87 pruebas, 83 correctas, 4 omitidas.
- Qt offscreen; perfil temporal `NAATIK_WINDOWS_PROFILE`. Ninguna conexión a la
  colección personal de Anki. Transporte simulado o servidor efímero de prueba.
- Cobertura: SQLite/diccionarios, traducción y popups con resultados inyectados,
  Anki y previsualización, apariencia, workers reales para operaciones sin modelos,
  cancelación/timeout, perfil Windows independiente, comandos Unicode con caracteres
  especiales, rechazo de dependencias sin hash/origen válido y recorte a DPI 200%.
- Omitidas: servidor HTTP local bloqueado por sandbox; dos pruebas del runtime
  Fugashi no instalado; prueba nativa Windows de Job Objects.
- Se utilizó el intérprete Qt ya instalado para pruebas, **sin copiar ni enlazar
  ese entorno dentro del port**. Esa ejecución no comprueba ruedas Windows.

## Pendiente de ejecutar en Windows

El workflow propio ejecutará la base y los tests cuando se publique este árbol en
su repositorio. No se ha ejecutado un workflow remoto desde esta sesión.
El instalador crea un lock Windows con hashes antes de instalar; todavía no hay
informes de resolución de Windows. Los locks Linux se archivan como referencia.

En una máquina Windows limpia:

1. Instalar Python 3.13 x64, el runtime Visual C++ x64 si falta y ejecutar
   `install.cmd`. Conservar los informes/locks generados.
2. Ejecutar `.venv\Scripts\python.exe tools\verify_windows.py`. Esta vez debe
   ejecutarse la prueba de Job Objects y el transporte local no debe omitirse
   salvo restricción del entorno. No usar un perfil Anki personal.
3. Abrir `launch.cmd`. Preparar Tesseract e idiomas o MangaOCR CPU/modelo con el
   asistente. Verificar carga e inferencia; repetir tras desconectar Internet.
4. Preparar una ruta de traducción, validar inferencia y usar Translator offline.
5. Con Next en bandeja y otra aplicación enfocada, disparar captura/copiar con el
   atajo. Confirmar una sola selección, OCR al portapapeles y ausencia de apertura
   automática de Translator. Abrir Translator con su propio atajo.
6. Probar Escape, botón derecho, timeout, cancelación durante OCR, cierre normal y
   cierre abrupto. Comprobar que no quedan procesos hijos.
7. Probar DPI 100/125/150/200%, monitores con distintas escalas y coordenadas
   negativas. La selección se limita a un monitor. Verificar dimensiones y bordes.
8. Probar colisiones de atajos, dos instancias, rutas con espacios y caracteres
   japoneses, reinicio y permisos estándar sin administrador.
9. Preparar el opcional de frase y ejecutar otra vez los tests de análisis real.
10. Revisar licencias/NOTICE de ruedas Windows antes de distribuir binarios.

No hay ejecutable `.exe` compilado ni evidencia de escritorio Windows en esta
entrega. Los tiempos de respuesta reales y la compatibilidad final dependen de
estas comprobaciones, no de la suite offscreen.


## Revisión ejecutada en Windows — 2026-10-22

Esta sección actualiza el estado pendiente anterior; se conserva la evidencia Fedora
como antecedente. No es una certificación de escritorio ni de inferencia con modelos.

- Windows x64, CPython 3.13.9 en la base de pruebas; intérprete privado 3.13.17
  preparado y validado para el bootstrap y los opcionales. Sin paquetes del usuario.
- Base: resolución Windows, instalación con hashes, carga de Qt/Pillow y carga de
  Argos/SentencePiece/CTranslate2 en worker sin importar Qt. Correctas.
- Frase: instalación completa Fugashi/UniDic Lite, `pip check` y análisis real japonés.
- MangaOCR: instalación completa, Torch 2.13.0+cpu, `torch.version.cuda is None`,
  importación MangaOcr y `pip check`. Correctos. No se descargaron modelos.
- Traducción separada: instalación con hashes e imports nativos correctos utilizando
  el directorio DLL del Qt propio de la base. No se importaron modelos Argos.
- Bootstrap PowerShell: detección mediante NAATIK_PYTHON y preparación sin `py`
  a partir del paquete NuGet en caché, con SHA-256 verificado. Correctos.
  La descarga HTTPS directa de PowerShell está bloqueada por las credenciales/TLS
  del entorno de ejecución; el paquete se obtuvo por un cliente HTTPS con validación
  de certificados. No se deshabilitó TLS ni se relajó el control de hashes.
  Queda pendiente comprobar la descarga directa en un escritorio Windows normal.
- Lanzador PowerShell con `--help`: correcto; genera launch.log.
- Suite: 88 pruebas, 87 correctas, 1 omitida por falta de enumeración de fuentes
  en Qt offscreen. Incluye análisis real japonés, named pipes, Job Objects,
  cancelación con rollback de SQLite y recorte simulado a DPI 200%.
- Correcciones comprobadas: independencia del comando `py`; perfil temporal de
  los smoke checks; DLL del worker; cancelación inmediata en Windows; validación
  de etiqueta de rueda en win32-setctime; resolución PyPI separada de Torch;
  rutas Win32 extendidas y reparación de instalación parcial sin RECORD.
- Se incluyó la imagen de prueba japonesa ausente en el ZIP original.
- Los avisos de Torch sobre Visual C++ y Transformers sobre torchvision aparecen
  en este entorno: la carga funciona; Transformers utiliza su backend Pillow.
  No se añadió torchvision porque no es necesario para esta ruta.

Pendientes: captura global y atajos con otra aplicación enfocada; DPI y múltiples
monitores reales; carga e inferencia con modelos elegidos por el usuario; idiomas
Tesseract; funcionamiento offline tras descargar modelos; instalación en VM limpia.
No se ejecutó el workflow remoto. Los logs de prueba adjuntos al informe se han
normalizado para no distribuir rutas personales del equipo.

## Progreso visible de preparación
El instalador MangaOCR transmite stdout/stderr durante la ejecución mediante run_progress. El asistente muestra barra indeterminada al instalar y porcentaje por archivo al descargar el modelo; conserva hasta 250 líneas de actividad. Se bloquean acciones incompatibles mientras trabaja y se muestra el resultado de cancelación/error. Se añadieron dos pruebas: transmisión antes de finalizar el proceso y estados de progreso/controles. Ambas pasan; la suite existente conserva 87 correctas y una omitida. El asistente admite desplazamiento en pantallas pequeñas.


Corrección de comprobación MangaOCR: el worker finaliza tras una petición cuando no se solicita modo persistente. Se probaron resultado sin cerrar stdin y dos peticiones consecutivas en modo persistente. Ambos casos pasan; el asistente recibe progreso de revisión de archivos, carga de Torch, carga de modelo e inferencia. No se ha probado inferencia con el modelo del perfil personal.


Guía de traducción: pasos de preparación automática en Traducción; catálogo Argos y documentación oficial en Opciones avanzadas; instrucciones para importar .argosmodel sin extraer, dirección de idioma y rutas intermedias. Enlaces directos de los modelos seleccionados obtenidos del catálogo ya validado; etiquetas y URLs escapadas para HTML. El resumen de la ruta evita repetir el detalle completo de la confirmación. No se añadieron dependencias ni se descargaron modelos.


## Tutorial — 2026-10-22, revisión local actual

Base: ZIP de fuentes Windows 1.0 de la entrega del 22 de octubre, conservando sus
correcciones posteriores. `tools/verify_windows.py` ejecutado con el Python Qt
local de Next, perfiles temporales `NAATIK_WINDOWS_PROFILE` y Qt offscreen:
102 pruebas, 98 correctas, 4 omitidas; detalle en `evidence/tutorial/tests.txt`.
Omisiones: listener local bloqueado, dos pruebas del opcional de frase ausente y
Job Objects que requiere kernel Windows. No se accedió a perfiles personales.

Se comprobó perfil nuevo, configuración anterior (incluido archivo vacío),
omisión/reinicio, cierre/reanudación, completado/reinicio, reapertura desde Ayuda,
arranque de ventana en segundo plano/popup, conservación de preferencias y fallo
de guardado sin adelantar el estado persistido.

Se generaron seis imágenes Qt offscreen y se inspeccionó su presentación; no son
validación de captura real. Intento xcb: no se pudo conectar al display :0.
No se ejecutaron inferencias ni se descargaron recursos. Falta revisión de
escritorio y captura real en Windows.

Se intentó invocar csc.exe con Wine: `wineserver: bind: Operation not permitted`.
No se pudo reconstruir el EXE aquí. Se reconstruyó el ZIP mediante el procedimiento
Python del proyecto; el instalador anterior no es parte de esta nueva entrega.

## Corrección posterior — captura inicial y consulta desde OCR

Suite ejecutada de nuevo con `tools/verify_windows.py`: **107 pruebas, 103 correctas,
4 omitidas**, Qt offscreen y perfiles Windows temporales aislados. Informe:
`evidence/tutorial/tests-followup.txt`. Se mantienen las cuatro omisiones anteriores.

Cinco pruebas adicionales recorren:

- `main()` sin argumentos: la ventana nueva abre el tutorial al procesar los timers.
- `main(--capture)` con perfil nuevo: se encola la captura, no aparece el tutorial;
  el menú Ayuda permite abrirlo.
- `main(--capture)` con progreso previo: conserva estado y paso hasta abrir Ayuda,
  que retoma ese paso, y mantiene las preferencias del perfil.
- `recognized()` con texto OCR inyectado y tres consultas automáticas: worker real
  de diccionarios, explicación y acceso a configuración sin diálogos repetidos.
  El botón de configuración y la entrada de importación existente son accesibles.
- Selección real en el editor y botón Consultar selección: worker real detecta
  diccionario desactivado, se activa mediante el control de la tabla existente y
  la consulta siguiente devuelve el término y retira el aviso.

En las pruebas de main se aíslan IPC y la aplicación propietaria del bucle; la
ventana y los callbacks Qt son reales. La detección de modelos se sustituye para
no iniciar recursos ni captura. No se ejecutó captura real, inferencia OCR ni
validación nativa Windows. El EXE sigue pendiente por la limitación documentada;
solo se regenera el ZIP de fuentes y se verifica su contenido y SHA-256.
