"""Independent adapters. Presence is evidence, never a readiness assertion."""
from .i18n import tr
import importlib.util
from functools import lru_cache
from . import timings
import os
import sys
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
from .storage import UserError, Cancelled

_child = None
_stopping = False


def stop(signum, frame):
    global _stopping
    if _stopping:
        return
    _stopping = True
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    # Unwind finally blocks once, including subprocess reaping and observer cleanup.
    # BaseException cannot be swallowed by an OCR adapter's error-to-status handler.
    raise SystemExit(0)


def run(args, timeout=30, env=None):
    global _child
    # Supervised workers are session leaders. Keep their tools in the same group
    # so the GUI can terminate the whole owned family even if the worker is stuck.
    supervised = sys.platform == 'win32' or (os.environ.get('NAATIK_SUPERVISED') == '1' and os.getpid() == os.getpgrp())
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                         start_new_session=not supervised)
    _child = p
    def terminate(signum):
        try:
            if supervised:
                p.kill() if signum == getattr(signal, 'SIGKILL', 9) else p.terminate()
            else:
                os.killpg(p.pid, signum)
        except ProcessLookupError:
            pass
    try:
        out, err = p.communicate(timeout=timeout)
        if p.returncode:
            raise UserError(tr('{p0} falló ({p1}): {p2}', p0=f'{Path(args[0]).name}', p1=f'{p.returncode}', p2=f"{err.decode(errors='replace')[-1500:]}"))
        return out.decode(errors='replace')
    except subprocess.TimeoutExpired as e:
        raise UserError(tr('{p0}: se agotó el tiempo de espera ({p1}s).', p0=f'{Path(args[0]).name}', p1=f'{timeout}')) from e
    finally:
        if p.poll() is None:
            terminate(signal.SIGTERM)
            try:
                p.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                terminate(getattr(signal, 'SIGKILL', 9))
                p.communicate()
        if _child is p:
            _child = None


class Tesseract:
    key = 'tesseract'

    def detect(self, *, probe=True):
        executable = tesseract_executable()
        result = dict(id=self.key, name='Tesseract', status='detectado', detail=executable or '', languages=[])
        if not executable:
            return dict(result, status='recursos faltantes', detail=tr('Instala Tesseract 5 para Windows con sus datos de idioma; se detecta también en Program Files.'))
        try:
            version = run([executable, '--version'], 10)
            if not version.lower().startswith('tesseract '):
                return dict(result, status='incompatible', detail=tr('El comando no se identifica como Tesseract.'))
            langs = [x.strip() for x in run([executable, '--list-langs'], 10).splitlines()[1:] if x.strip() and x.strip() != 'osd']
            result['languages'] = langs
            if not langs:
                return dict(result, status='recursos faltantes', detail=tr('No hay datos de idioma OCR utilizables.'))
            if not probe:
                return dict(result, status='listo', detail=tr('{p0}; idiomas comprobados; sin inferencia de prueba.', p0=f'{version.splitlines()[0]}'))
            from PIL import Image, ImageDraw, ImageFont
            with tempfile.TemporaryDirectory(prefix='naatik-ocr-probe-') as tmp:
                path = Path(tmp) / 'probe.png'
                image = Image.new('RGB', (650, 120), 'white')
                font = ImageFont.load_default(size=52)
                ImageDraw.Draw(image).text((20, 20), 'TEST 123', fill='black', font=font)
                image.save(path)
                lang = 'eng' if 'eng' in langs else langs[0]
                text = self.recognize(str(path), lang)
                if not text.strip() or ('eng' in langs and 'TEST' not in text.upper()):
                    return dict(result, status='error', detail=tr('La prueba real no devolvió el texto esperado.'))
            return dict(result, status='listo', detail=tr('{p0}; prueba OCR real correcta con {p1}.', p0=f'{version.splitlines()[0]}', p1=f'{lang}'))
        except (UserError, OSError) as e:
            return dict(result, status='error', detail=str(e))

    def recognize(self, image, language):
        if not language or not all(c.isalnum() or c in '_+' for c in language):
            raise UserError(tr('Selecciona un idioma OCR válido.'))
        executable = tesseract_executable()
        if not executable:
            raise UserError(tr('Tesseract ya no está disponible. Vuelve a detectar.'))
        return run([executable, image, 'stdout', '-l', language, '--psm', '6'], 90).strip()


class UnsupportedPythonOCR:
    def __init__(self, key, module, label):
        self.key, self.module, self.label = key, module, label

    def detect(self):
        evidence = []
        if importlib.util.find_spec(self.module):
            evidence.append(tr('paquete presente en este entorno'))
        return dict(id=self.key, name=self.label, status='incompatible', languages=[],
                    detail=(tr('Detectado: ') + '; '.join(evidence) + '. ' if evidence else tr('No se encontró evidencia local. '))
                    + tr('Adaptador de inferencia todavía no implementado; no se acredita disponibilidad ni se contactan servicios antiguos.'))


def detect():
    from .manga import descriptor
    return [Tesseract().detect(), descriptor(),
            UnsupportedPythonOCR('paddleocr', 'paddleocr', 'PaddleOCR').detect()]


def capture(trace=None):
    from .windows_capture import capture_region
    return capture_region(trace)


def tesseract_executable():
    found = shutil.which('tesseract')
    if found:
        return found
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        root = os.environ.get(variable)
        if root:
            candidate = Path(root) / 'Tesseract-OCR/tesseract.exe'
            if candidate.is_file():
                return str(candidate)
    return None
