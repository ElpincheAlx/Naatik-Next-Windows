"""Dispatch Python termination requests from the Qt event loop."""
import signal
from PySide6.QtCore import QObject, QTimer
class ShutdownSignals(QObject):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback, self.received, self.requested, self.closed = callback, None, False, False
        self.previous_handlers = {s: signal.signal(s, self._remember) for s in (signal.SIGINT, signal.SIGTERM)}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._drain)
        self.timer.start(100)
    def _remember(self, signum, frame):
        if self.received is None: self.received = signum
    def _drain(self):
        if self.received is not None and not self.requested and not self.closed:
            self.requested = True
            self.callback(self.received)
    def close(self):
        if self.closed: return
        self.closed = True
        self.timer.stop()
        for signum, previous in self.previous_handlers.items():
            signal.signal(signum, signal.SIG_IGN if self.received is not None else previous)
