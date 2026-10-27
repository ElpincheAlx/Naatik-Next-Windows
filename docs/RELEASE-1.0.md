# Na’atik Next 1.0.0 — Windows x64

## Instalar
Cierra las copias abiertas mediante Acciones → Salir de Next. Ejecuta
Naatik-Next-1.0-Setup.exe y pulsa Instalar / reparar. Necesita Internet.
La ventana muestra la actividad y avisa si ocurre un error.
Al terminar, abre Naatik Next 1.0 desde el menú Inicio.

Ubicación: %LOCALAPPDATA%\Programs\NaatikNext\1.0.
No requiere administrador. El perfil existente se conserva; las rutas de
recursos guardadas anteriormente no se cambian silenciosamente.
Prepara OCR y traducción desde sus asistentes. Los modelos no vienen incluidos.
Si Windows bloquea el archivo por falta de firma, no hay certificado de editor
para esta compilación; el SHA-256 permite comprobar que es el archivo entregado.

Para desinstalar, usa Aplicaciones y características de Windows. Cierra Next
antes; se elimina la carpeta de instalación, conservando el perfil de datos en
%LOCALAPPDATA%\NaatikNextWindows. Los entornos Python de la instalación se eliminan.

## Rendimiento
Se reutilizan los procesos de consulta de diccionarios y selección de palabras.
Prueba local de ocho consultas sin modelos, mismo Windows y perfil temporal:
mediana después de la primera consulta: 143.17 ms antes; 6.12 ms con reutilización
(aproximadamente 23 veces más rápida en esta medición). Primera consulta:
170.45 ms frente a 138.53 ms. No es una medición de OCR ni de inferencia neuronal.
Los workers OCR y traducción ya eran persistentes; se conserva ese comportamiento.
El acceso directo inicia Python directamente, sin una consola PowerShell intermedia.
También se corrige el registro opcional de tiempos para Windows.

## Alcance de verificación
Pruebas automatizadas con Qt offscreen y kernels Windows. Sin certificado de
firma. No se acredita instalación/desinstalación en una VM limpia ni captura
interactiva, múltiples monitores o inferencia con los modelos del usuario.
La preparación de dependencias fue probada durante la revisión previa.

## Reproducir el empaquetado
Desde una carpeta con la base instalada:
`powershell -File packaging/build.ps1 -OutputDirectory dist`
El instalador admite `--extract RUTA` para inspeccionar el código empaquetado
sin instalar dependencias, crear accesos directos ni cambiar el registro.
