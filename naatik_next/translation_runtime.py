"""Own, pinned CPU runtime provisioning. Usable before Qt/Argos is installed."""
from .i18n import tr
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from .storage import UserError

PROJECT=Path(__file__).resolve().parent.parent


def run_progress(args, progress, *, env=None, timeout=900):
    import queue, threading
    from .i18n import language
    env = dict(os.environ if env is None else env, NAATIK_UI_LANGUAGE=language())
    progress(tr('Salida de herramientas externas (puede conservar su idioma original):'))
    messages=queue.Queue(maxsize=32)
    stopped=threading.Event()
    process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
    def reader():
        try:
            while not stopped.is_set():
                block=process.stdout.read1(8192)
                if not block: break
                while not stopped.is_set():
                    try: messages.put(block,timeout=.1); break
                    except queue.Full: pass
        finally:
            while not stopped.is_set():
                try: messages.put(None,timeout=.1); break
                except queue.Full: pass
    thread=threading.Thread(target=reader,daemon=True);thread.start()
    started=time.monotonic();tail=''
    try:
        while True:
            if time.monotonic()-started>timeout: raise UserError(tr('Se agotó el tiempo de preparación.'))
            try: block=messages.get(timeout=.2)
            except queue.Empty: continue
            if block is None: break
            value=block.decode('utf-8',errors='replace');tail=(tail+value)[-4000:];progress(value[-2000:])
        process.wait(timeout=5)
        if process.returncode: raise UserError(tr('No se completó la instalación.\n')+tail)
    finally:
        stopped.set()
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: process.kill();process.wait()
        thread.join(timeout=2)
        if not thread.is_alive(): process.stdout.close()


def runtime_directory():
    from .translation_setup import root
    return root()/'runtime'


def program():
    python=runtime_directory()/'Scripts/python.exe'
    return str(python) if python.is_file() and (runtime_directory()/'next-runtime.json').is_file() and not runtime_directory().is_symlink() else sys.executable


def compatible():
    import platform,sysconfig
    if sys.version_info[:2]!=(3,13) or sys.platform!='win32' or platform.machine().lower() not in ('amd64','x86_64') or sysconfig.get_config_var('Py_GIL_DISABLED'):
        raise UserError(tr('Esta preparación admite Python 3.13 estándar, Windows x64. Plataforma aún no compatible.'))


def prepare(progress=lambda text:None):
    from .translation_setup import locked,atomic_json
    compatible()
    target=runtime_directory()
    with locked('.provision.lock'):
        if target.is_symlink(): raise UserError(tr('No se admite un entorno enlazado.'))
        (target/'next-runtime.json').unlink(missing_ok=True)
        run_progress([sys._base_executable,str(PROJECT/'tools/install_windows.py'),
                      '--translation','--target',str(target)],progress)
        lock=PROJECT/'locks/translation-windows.lock'
        atomic_json(target/'next-runtime.json',dict(lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest(),cpu=True))
    return dict(detail=tr('Motor CPU instalado; falta validar modelos e inferencia.'),program=str(target/'Scripts/python.exe'))


def prepare_base(progress=lambda text:None):
    compatible()
    run_progress([sys._base_executable,str(PROJECT/'tools/install_windows.py')],progress)
    return dict(detail=tr('Entorno Windows preparado.'))
