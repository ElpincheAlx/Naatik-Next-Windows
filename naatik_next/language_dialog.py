"""Language-only preference; never restarts or mutates resource settings."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from .i18n import tr, saved_language, save_language


def show_language(owner):
    dialog = QDialog(owner)
    dialog.setWindowTitle(tr('Idioma de la interfaz'))
    dialog.setMinimumWidth(420)
    layout = QVBoxLayout(dialog)
    label = QLabel(tr('El idioma de la interfaz es independiente del idioma OCR y de la ruta de traducción.'))
    label.setWordWrap(True); layout.addWidget(label)
    languages = QComboBox()
    languages.addItem('Español', 'es'); languages.addItem('English', 'en')
    languages.setCurrentIndex(languages.findData(saved_language()))
    layout.addWidget(languages)
    notice = QLabel(tr('El cambio se aplicará al volver a abrir Next. Puedes seguir trabajando y cerrarlo cuando quieras.'))
    notice.setWordWrap(True); layout.addWidget(notice)
    save = QPushButton(tr('Guardar')); layout.addWidget(save)
    close = QPushButton(tr('Cancelar')); layout.addWidget(close)
    close.clicked.connect(dialog.reject)
    def apply():
        try:
            save_language(languages.currentData())
        except (OSError, ValueError) as error:
            QMessageBox.warning(dialog, tr('Idioma de la interfaz'), tr('No se pudo guardar el idioma: {p0}', p0=str(error)))
            return
        QMessageBox.information(dialog, tr('Idioma de la interfaz'), tr('Idioma guardado. Se aplicará la próxima vez que abras Next; no es necesario cerrarlo ahora.'))
        dialog.accept()
    save.clicked.connect(apply)
    dialog.exec()
