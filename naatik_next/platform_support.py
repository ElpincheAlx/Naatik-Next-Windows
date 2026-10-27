"""Windows port support boundary."""
from .i18n import tr
import sys
def kde_x11(): return False
def summary():
    return (tr('Port Windows 10/11 x64: captura regional Qt, atajos Win32 y OCR/traducción local CPU. Validación de escritorio Windows pendiente; Linux offscreen solo verifica lógica e interfaz.'))
