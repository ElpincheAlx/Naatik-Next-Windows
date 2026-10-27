"""Generate a single-action POSIX script, without interpolating shell code."""
from .i18n import tr
import os
from pathlib import Path
import shlex
import stat
import tempfile
from .storage import UserError, paths


def launcher_path():
    return Path(__file__).resolve().parent.parent / 'launch.ps1'

ACTIONS = {'capture-copy': tr('Capturar y copiar'), 'translator': 'Translator', 'phrase': 'OCR Phrase', 'show': tr('Abrir ventana principal')}

def profile_environment():
    return {'NAATIK_WINDOWS_PROFILE': str(paths()['config'].parent)}

def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"

def action_command(action, launcher=None):
    if action not in ACTIONS: raise UserError(tr('Acción desconocida.'))
    import base64
    command = '$env:NAATIK_WINDOWS_PROFILE=' + ps_quote(profile_environment()['NAATIK_WINDOWS_PROFILE'])
    command += '; & ' + ps_quote(launcher or launcher_path()) + ' --' + action
    encoded=base64.b64encode(command.encode('utf-16-le')).decode('ascii')
    return 'powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand ' + encoded

def action_script(action, launcher=None):
    return '@echo off\n' + action_command(action, launcher) + '\n'

def capture_script(launcher=None):
    return action_script('capture-copy', launcher)


def write_capture_script(path, *, overwrite=False):
    return write_action_script(path, 'capture-copy', overwrite=overwrite)


def write_action_script(path, action, *, overwrite=False):
    return write_artifact(path, action_script(action), overwrite=overwrite)


def write_artifact(path, content, *, overwrite=False):
    """Atomic replace of a user-confirmed regular file; no symlink traversal."""
    path = Path(path).absolute()
    if path == launcher_path() or path.resolve() == launcher_path().resolve():
        raise UserError(tr('Elige otra ruta: no se puede reemplazar el lanzador de Next.'))
    if path.is_symlink():
        raise UserError(tr('No se sobrescriben enlaces simbólicos. Elige otro archivo.'))
    if path.exists():
        if not stat.S_ISREG(path.stat().st_mode):
            raise UserError(tr('La ruta seleccionada no es un archivo normal.'))
        if not overwrite:
            raise FileExistsError(str(path))
    fd, temporary = tempfile.mkstemp(prefix='.naatik-script-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            output.write(content)
            output.flush()
            if os.name != 'nt': os.fchmod(output.fileno(), 0o700)
            os.fsync(output.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            # No-clobber creation, even if a file appeared after the save dialog.
            os.link(temporary, path)
        return path
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_action_desktop(path, action, *, overwrite=False):
    # Windows executable launcher, usable from Explorer/Stream Deck.
    return write_action_script(path, action, overwrite=overwrite)
