"""Windows global shortcuts using RegisterHotKey; no keyboard hook."""
from .i18n import tr
import ctypes as C
from ctypes import wintypes as W
import sys
from PySide6.QtCore import QObject, QAbstractNativeEventFilter, Qt, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence
from .storage import UserError
DEFAULT_SHORTCUT = 'Ctrl+Alt+Shift+R'

def combination(text):
    sequence = QKeySequence.fromString(text, QKeySequence.PortableText)
    if sequence.count() != 1 or sequence.isEmpty():
        raise UserError(tr('Pulsa una sola combinación de teclas.'))
    key = sequence[0]
    modifiers = key.keyboardModifiers()
    supported = Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier | Qt.MetaModifier
    if modifiers & ~supported or not modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
        raise UserError(tr('Incluye Ctrl, Alt o Meta junto con una tecla (Shift solo no basta).'))
    code = key.key()
    if Qt.Key_A <= code <= Qt.Key_Z:
        name = chr(code).lower()
    elif Qt.Key_0 <= code <= Qt.Key_9:
        name = chr(code)
    elif Qt.Key_F1 <= code <= Qt.Key_F24:
        name = f'F{code - Qt.Key_F1 + 1}'
    else:
        name = {Qt.Key_Space: 'space', Qt.Key_Print: 'Print', Qt.Key_Pause: 'Pause',
                Qt.Key_Home: 'Home', Qt.Key_End: 'End', Qt.Key_Insert: 'Insert',
                Qt.Key_Delete: 'Delete', Qt.Key_PageUp: 'Prior', Qt.Key_PageDown: 'Next',
                Qt.Key_Left: 'Left', Qt.Key_Right: 'Right', Qt.Key_Up: 'Up',
                Qt.Key_Down: 'Down'}.get(code)
    if not name:
        raise UserError(tr('Tecla no compatible: usa una letra, número, F1–F24, espacio, Impr Pant o navegación.'))
    return sequence.toString(QKeySequence.PortableText), name, modifiers


class NativeFilter(QAbstractNativeEventFilter):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            msg = W.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.owner.ident:
                self.owner.activated.emit()
                return True, 0
        return False, 0


class GlobalShortcut(QObject):
    activated = Signal()
    _next = 0x2000
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = ''
        self.filter = None
        self.ident = GlobalShortcut._next
        GlobalShortcut._next += 1
        if self.ident > 0xbfff: raise UserError(tr('Demasiados registros de atajos.'))
        self.api = None
    def register(self, text):
        normalized, name, modifiers = combination(text)
        if sys.platform != 'win32' or QGuiApplication.platformName() != 'windows':
            raise UserError(tr('El atajo global requiere una sesión de escritorio Windows.'))
        key = (ord(name.upper()) if len(name) == 1 else
               0x70 + int(name[1:]) - 1 if name.startswith('F') and name[1:].isdigit() else
               {'space':0x20, 'Print':0x2c, 'Pause':0x13, 'Home':0x24, 'End':0x23,
                'Insert':0x2d, 'Delete':0x2e, 'Prior':0x21, 'Next':0x22,
                'Left':0x25, 'Up':0x26, 'Right':0x27, 'Down':0x28}[name])
        mask = 0x4000  # MOD_NOREPEAT
        for qt, native in ((Qt.AltModifier,1),(Qt.ControlModifier,2),(Qt.ShiftModifier,4),(Qt.MetaModifier,8)):
            if modifiers & qt: mask |= native
        self.close()
        self.api = C.WinDLL('user32', use_last_error=True)
        self.api.RegisterHotKey.argtypes = [W.HWND, C.c_int, W.UINT, W.UINT]
        self.api.RegisterHotKey.restype = W.BOOL
        self.api.UnregisterHotKey.argtypes = [W.HWND, C.c_int]
        self.api.UnregisterHotKey.restype = W.BOOL
        if not self.api.RegisterHotKey(None, self.ident, mask, key):
            raise UserError(tr('Windows rechazó el atajo; puede estar reservado u ocupado. Código: ') + str(C.get_last_error()))
        self.active = normalized
        self.filter = NativeFilter(self)
        QGuiApplication.instance().installNativeEventFilter(self.filter)
        return normalized
    def close(self):
        if self.filter is not None:
            QGuiApplication.instance().removeNativeEventFilter(self.filter)
            self.filter = None
        if self.active and self.api:
            self.api.UnregisterHotKey(None, self.ident)
        self.active = ''
