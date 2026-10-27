# Tutorial de primera ejecución

El tutorial se abre en la primera apertura normal de un perfil nuevo. No se abre
en segundo plano ni para captura/popup. Una petición explícita de mostrar la
ventana desde una instancia residente puede abrirlo. Ayuda → Tutorial y
configuración inicial permite retomarlo o repetirlo desde Bienvenida después de
omitirlo/completarlo.

Se recorren Bienvenida, OCR, Traducción, Diccionarios, Anki opcional y una prueba
con acciones de captura, reconocimiento, consulta y traducción. Se reutilizan
SetupDialog, TranslationSection, la importación de ZIP, la sección Anki y las
operaciones principales. No se instala ni descarga nada al abrir o avanzar.
Las confirmaciones, tamaños conocidos/desconocidos y verificaciones pertenecen a
los asistentes existentes y se conservan.

Volver/Continuar guardan el paso. Continuar permite saltar la preparación de
cualquier función. Omitir por ahora guarda `skipped`; cerrar conserva
`in_progress` y el último paso. Completar guarda `completed`. La prueba guiada no
certifica inferencia ni cambia el estado de recursos. Cuando falta OCR, idioma,
ruta de traducción o diccionario activo, la operación principal explica qué falta
y ofrece abrir su preparación. Las acciones popup conservan sus mensajes y
entradas de configuración existentes.

`settings.json` del perfil Windows guarda `tutorial: {status, step}`. Los estados
son `pending`, `in_progress`, `skipped`, `completed`; el índice comienza en cero.
Un archivo de preferencias anterior, incluso vacío, se considera perfil anterior
y no dispara el tutorial. No se infiere preparación de `setup_completed`. Se
mantienen rutas explícitas, preferencias y evidencia de recursos; no se importan
datos de otros proyectos. La escritura usa el reemplazo atómico existente: ante
un fallo se muestra el error y se conserva el estado anterior en memoria/disco;
la ventana se puede cerrar y la aplicación continúa disponible.

## Base de esta entrega

Este árbol parte del ZIP Windows 1.0 entregado el 22 de octubre de 2026, que contiene
correcciones posteriores al árbol local `Naatik-next-windows`. Se conserva este
último y el árbol Linux. Las modificaciones respecto al ZIP base son:

- `naatik_next/app.py`: arranque, Ayuda, configuración de recursos faltantes y cierre.
- `naatik_next/tutorial.py`: recorrido no modal y progreso independiente.
- `tests/test_tutorial.py`: pruebas aisladas de comportamiento y cableado de ventana.
- `README.md`, `docs/TUTORIAL.md`, `docs/VALIDATION.md`: uso y evidencia actual.
- `docs/evidence/tutorial/`: imágenes offscreen e informes de esta revisión.

No se añadieron dependencias. Actualizar/reparar usa el empaquetado existente y
conserva el perfil externo a la instalación; no se probó una reparación Windows
real en esta sesión.

## Reproducción

Desde la base Windows preparada, ejecutar
`powershell -File packaging/build.ps1 -OutputDirectory dist`.
Este script construye el ZIP con `tools/build_source_zip.py` y compila Setup.cs
con el compilador .NET Framework 64 bits, incorporando el ZIP como `payload.zip`.
En este entorno se ejecutó únicamente la construcción del ZIP. Wine no pudo
iniciar el compilador: `wineserver: bind: Operation not permitted`.
Falta ejecutar el procedimiento completo en Windows con el Python privado/base
instalada y el compilador .NET Framework disponible, y probar extracción,
instalación/reparación y uso interactivo. El EXE anterior no contiene este tutorial.

## Corrección de acciones de captura y consulta OCR

`main()` pasa explícitamente la acción de inicio a `Window(startup_action=...)`.
Solo `show` permite programar el tutorial automático; `--capture` conserva su
solicitud de captura sin abrir el tutorial ni avanzar su progreso. Ayuda sigue
disponible para iniciarlo o retomar el paso guardado.

En el recorrido `recognized()` → `lookup_dictionary_text()` → worker →
`selection_result()`, la ausencia de diccionarios activos muestra una explicación
junto con «Importar o activar diccionarios…». Este botón abre la pestaña existente,
con importación ZIP y controles de activación. También funciona al pulsar
«Consultar selección» desde el editor. Las consultas automáticas no abren ventanas,
importaciones ni confirmaciones, aunque se repitan. El aviso se invalida al cambiar
la selección o iniciar otra consulta; una consulta con diccionarios activos retira
el acceso de preparación. Estos cambios no modifican el progreso del tutorial.
