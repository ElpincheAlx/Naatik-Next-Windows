"""Explicit, pinned model provisioning. Never used by inference workers."""
from .i18n import tr
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from .storage import UserError, paths


def catalogue():
    return json.loads(Path(__file__).with_name('model-catalog.json').read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_model(progress=lambda text: None, *, spec=None, opener=urllib.request.urlopen):
    spec = spec or catalogue()
    target = paths()['data'] / 'models/manga-ocr-base'
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    # A private lock prevents two setup dialogs/processes writing partial files.
    from . import filelock as fcntl
    with (target / '.download.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise UserError(tr('Ya hay una preparación de este modelo en curso.')) from e
        for item in spec['files']:
            name = item['name']
            if Path(name).name != name or name.startswith('.'):
                raise UserError(tr('Nombre de recurso inválido en el catálogo.'))
            final, partial = target / name, target / (name + '.part')
            if final.is_symlink() or partial.is_symlink():
                raise UserError(tr('El destino del modelo no puede ser un enlace simbólico.'))
            if final.is_file() and final.stat().st_size == item['bytes'] and digest(final) == item['sha256']:
                progress(tr('{p0}: verificado, se conserva', p0=f'{name}'))
                continue
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > item['bytes']:
                partial.unlink(); offset = 0
            if offset != item['bytes']:
                url = f"https://huggingface.co/{spec['id']}/resolve/{spec['revision']}/{name}"
                request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'} if offset else {})
                started = time.monotonic()
                try:
                    # No cookies, tokens or authenticated Hub configuration.
                    with opener(request, timeout=20) as response:
                        if not response.geturl().startswith('https://'):
                            raise UserError(tr('El recurso se redirigió fuera de HTTPS.'))
                        status = response.status
                        if status == 206:
                            content_range = response.headers.get('Content-Range', '')
                            if not content_range.startswith(f'bytes {offset}-') or not content_range.endswith(f"/{item['bytes']}"):
                                raise UserError(tr('Respuesta de reanudación incoherente.'))
                        elif status == 200:
                            offset = 0
                        else:
                            raise UserError(tr('HTTP inesperado: {p0}', p0=f'{status}'))
                        with partial.open('ab' if offset else 'wb') as stream:
                            while True:
                                if time.monotonic() - started > 900:
                                    raise UserError(tr('Se agotó el tiempo total de descarga (15 min por archivo).'))
                                block = response.read(1024 * 1024)
                                if not block:
                                    break
                                offset += len(block)
                                if offset > item['bytes']:
                                    raise UserError(tr('El recurso supera el tamaño del catálogo.'))
                                stream.write(block)
                                progress(f'{name}: {offset:,} / {item["bytes"]:,} bytes')
                except (OSError, ValueError) as e:
                    raise UserError(tr('Descarga interrumpida de {p0}: {p1}. Reintenta para recuperar el parcial; no se usará como modelo listo.', p0=f'{name}', p1=f'{e}')) from e
            if not partial.exists() or partial.stat().st_size != item['bytes']:
                raise UserError(tr('Descarga incompleta de {p0}; reintenta para reanudar.', p0=f'{name}'))
            if digest(partial) != item['sha256']:
                partial.unlink()
                raise UserError(tr('Integridad incorrecta de {p0}; parcial descartado. No se acredita el modelo.', p0=f'{name}'))
            partial.replace(final)
        (target / 'verified-manifest.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'model': str(target), 'detail': tr('Descarga verificada. Pendiente carga e inferencia del motor.')}


def prepare_phrase_runtime():
    """One installation per project, even when both popup actions request it."""
    from . import filelock as fcntl
    from .ocr import run
    project = Path(__file__).resolve().parent.parent
    with (project / '.phrase-install.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UserError(tr('Ya se están preparando los recursos de frase de Next.')) from error
        import sys
        return run([sys._base_executable, str(project / 'tools/install_windows.py'), '--phrase'], 900)
