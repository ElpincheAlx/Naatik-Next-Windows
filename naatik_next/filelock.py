"""Cross-process file locks; kernel releases the lock when its stream closes."""
from .i18n import tr
import os
LOCK_EX, LOCK_NB = 1, 2

def flock(stream, flags):
    if os.name != 'nt':
        import fcntl
        return fcntl.flock(stream, fcntl.LOCK_EX | (fcntl.LOCK_NB if flags & LOCK_NB else 0))
    import msvcrt
    stream.flush()
    stream.seek(0, os.SEEK_END)
    if stream.tell() == 0:
        stream.write(' ')
        stream.flush()
    stream.seek(0)
    try:
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK if flags & LOCK_NB else msvcrt.LK_LOCK, 1)
    except OSError as error:
        raise BlockingIOError(tr('Recurso ocupado por otra operación.')) from error
