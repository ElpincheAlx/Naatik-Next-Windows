"""Qt regional capture: one overlay per screen, native pixel resolution preserved."""
from .i18n import tr
import base64
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRect, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPainter, QColor, QPen
from PySide6.QtWidgets import QApplication, QWidget
from .storage import UserError, Cancelled
from . import timings

class Selector(QWidget):
    def __init__(self, screen, image, finish, trace):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.screen, self.image, self.finish, self.trace = screen, image, finish, trace
        self.origin = self.point = None
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(),self.image)
        painter.fillRect(self.rect(),QColor(0,0,0,95))
        if self.origin is not None:
            rect = QRect(self.origin,self.point).normalized().intersected(self.rect())
            ratio = self.image.devicePixelRatio()
            source = QRect(round(rect.x()*ratio),round(rect.y()*ratio),round(rect.width()*ratio),round(rect.height()*ratio))
            painter.drawPixmap(rect,self.image,source)
            painter.setPen(QPen(QColor('#65cfff'),2)); painter.drawRect(rect)
        painter.setPen(Qt.white)
        painter.drawText(20,30,tr('Arrastra una región · Esc cancela · selecciona dentro de un monitor'))
    def mousePressEvent(self,event):
        if event.button() == Qt.RightButton: self.finish(None); return
        if event.button() != Qt.LeftButton: return
        self.origin = self.point = event.position().toPoint()
        timings.event('selection_user_begin',self.trace)
        self.grabMouse(); self.update()
    def mouseMoveEvent(self,event):
        self.point = event.position().toPoint(); self.update()
    def mouseReleaseEvent(self,event):
        if self.origin is None or event.button() != Qt.LeftButton: return
        self.releaseMouse()
        rect = QRect(self.origin,event.position().toPoint()).normalized().intersected(self.rect())
        timings.event('selection_user_end',self.trace)
        if rect.width() < 2 or rect.height() < 2: self.finish(None); return
        ratio=self.image.devicePixelRatio()
        image=self.image.copy(QRect(round(rect.x()*ratio),round(rect.y()*ratio),round(rect.width()*ratio),round(rect.height()*ratio)))
        self.finish(image)
    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Escape: self.finish(None)
    def closeEvent(self,event):
        self.finish(None); event.accept()


_application = None

def capture_region(trace=None):
    global _application
    # Capture worker is short-lived: QApplication lives for exactly this request.
    app=QApplication.instance() or QApplication([])
    _application = app
    app.setQuitOnLastWindowClosed(False)
    screens=QGuiApplication.screens()
    snapshots=[(screen,screen.grabWindow(0)) for screen in screens]
    if not snapshots or any(image.isNull() for _,image in snapshots):
        raise UserError(tr('Windows no permitió capturar el escritorio de esta sesión.'))
    result=[]; windows=[]
    def finish(image):
        if result: return
        result.append(image)
        for window in windows: window.hide()
        app.quit()
    for screen,image in snapshots:
        windows.append(Selector(screen,image,finish,trace))
    timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(lambda:finish(None));timer.start(120000)
    for window in windows: window.show(); window.raise_()
    windows[0].activateWindow()
    timings.event('selector_ready',trace)
    app.exec()
    timer.stop()
    for window in windows: window.deleteLater()
    if not result or result[0] is None: raise Cancelled(tr('Selección cancelada.'))
    image=result[0]
    if image.width()*image.height()>40_000_000: raise UserError(tr('La captura supera los 40 megapíxeles.'))
    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer,'PNG'): raise UserError(tr('No se pudo codificar la captura.'))
    return base64.b64encode(bytes(data)).decode('ascii')
