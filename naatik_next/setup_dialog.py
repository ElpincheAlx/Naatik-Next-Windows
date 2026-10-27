"""Non-blocking first-use setup; only explicit confirmation permits downloads."""
from .i18n import tr, status_text
import platform
from pathlib import Path
import shutil
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QPlainTextEdit, QWidget, QProgressBar, QScrollArea)
from .processes import Task
from .resources import catalogue
from .manga import defaults


class SetupDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.operation_buttons = []
        self.operation = None
        self.setWindowTitle(tr('Primer inicio — idioma y OCR local'))
        self.resize(740, 700)
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        intro = QLabel(tr('1. Elige cómo reconocer texto de imágenes. Solo necesitas uno de los dos motores.'))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.language = QComboBox()
        for label, code in [(tr('Japonés (jpn)'), 'jpn'), (tr('Inglés (eng)'), 'eng'), (tr('Español (spa)'), 'spa'), (tr('Japonés vertical (jpn_vert)'), 'jpn_vert')]:
            self.language.addItem(label, code)
        for engine in owner.engines:
            for code in engine.get('languages', []):
                if self.language.findData(code) < 0: self.language.addItem(code, code)
        index = self.language.findData(owner.settings.get('ocr_language', 'jpn'))
        self.language.setCurrentIndex(max(index, 0))
        self.language_label = QLabel(tr('Idioma del texto:'))
        layout.addWidget(self.language_label)
        layout.addWidget(self.language)
        self.engine = QComboBox()
        self.engine.addItem(tr('Tesseract — requiere ejecutable y datos del sistema'), 'tesseract')
        self.engine.addItem(tr('MangaOCR — japonés fijo, CPU'), 'mangaocr')
        self.engine.setCurrentIndex(max(self.engine.findData(owner.settings.get('ocr_engine', 'tesseract')), 0))
        layout.addWidget(self.engine)
        self.guide = QLabel()
        self.guide.setWordWrap(True)
        self.guide.setOpenExternalLinks(True)
        layout.addWidget(self.guide)
        self.manga_options = QWidget()
        manga_layout = QVBoxLayout(self.manga_options)
        layout.addWidget(self.manga_options)
        self.add_button(manga_layout, tr('1. Instalar MangaOCR'), self.runtime)
        self.add_button(manga_layout, tr('2. Descargar modelo japonés'), self.download)
        advanced = QPushButton(tr('Opciones avanzadas: usar recursos existentes'))
        advanced.setCheckable(True)
        manga_layout.addWidget(advanced)
        self.advanced = QWidget()
        advanced_layout = QVBoxLayout(self.advanced)
        manga_layout.addWidget(self.advanced)
        self.advanced.hide()
        advanced.toggled.connect(self.advanced.setVisible)
        self.python = QLineEdit(owner.settings['manga_python'])
        self.model = QLineEdit(owner.settings['manga_model'])
        advanced_layout.addWidget(QLabel(tr('Intérprete Python de MangaOCR:')))
        advanced_layout.addWidget(self.python)
        advanced_layout.addWidget(QLabel(tr('Carpeta del modelo:')))
        advanced_layout.addWidget(self.model)
        self.add_button(advanced_layout, tr('Elegir modelo local…'), self.choose_model)
        self.add_button(layout, tr('Comprobar OCR'), self.probe)
        self.activity = QLabel(tr('Sin operación en curso'))
        self.activity.setWordWrap(True)
        layout.addWidget(self.activity)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        self.status = QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setMaximumBlockCount(250)
        self.status.setStyleSheet('font-size: 12px;')
        self.status.setMinimumHeight(95)
        layout.addWidget(self.status)
        extras = QLabel(tr('<b>Después, solo si lo necesitas:</b><br>• Traducción: abre la pestaña Traducción, elige idiomas y pulsa Preparar traducción.<br>• Análisis japonés: abre OCR Phrase y acepta preparar sus recursos cuando se solicite.<br>• Diccionarios: importa tus ZIP en Diccionarios.<br>• Anki: sigue la guía de AnkiConnect en la pestaña Anki.<br>Si aparece un error de DLL, instala <a href="https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist">Visual C++ x64 de Microsoft</a> y vuelve a comprobar.'))
        extras.setWordWrap(True)
        extras.setOpenExternalLinks(True)
        layout.addWidget(extras)
        self.add_button(layout, tr('Cancelar preparación en curso'), self.cancel)
        self.add_button(layout, tr('Guardar elecciones y continuar'), self.save)
        self.add_button(layout, tr('Cerrar sin guardar'), self.close)
        self.task = Task(self)
        self.task.result.connect(self.prepared)
        self.task.error.connect(self.failed)
        self.task.progress.connect(self.update_progress)
        self.probe_task = Task(self, program=self.python.text(), module='naatik_next.manga_worker')
        self.probe_task.progress.connect(self.update_progress)
        self.probe_task.result.connect(self.prepared)
        self.probe_task.error.connect(self.failed)
        self.task.busy_changed.connect(self.update_busy)
        self.probe_task.busy_changed.connect(self.update_busy)
        self.engine.currentIndexChanged.connect(self.show_requirements)
        self.show_requirements()

    def add_button(self, layout, title, callback):
        button = QPushButton(title)
        button.clicked.connect(callback)
        layout.addWidget(button)
        if callback.__name__ not in ('cancel', 'close'):
            self.operation_buttons.append(button)

    def update_busy(self, _busy):
        busy = self.task.busy or self.probe_task.busy
        for button in self.operation_buttons:
            button.setEnabled(not busy)
        for field in (self.engine, self.language, self.python, self.model):
            field.setEnabled(not busy)

    def begin(self, operation, message):
        self.operation = operation
        self.activity.setText(message)
        self.progress_bar.setRange(0, 0)
        self.status.setPlainText(message)

    def update_progress(self, value):
        import re
        text = str(value).strip()
        if not text: return
        self.status.appendPlainText(text)
        match = re.search(r'([^\n]+): ([\d,]+) / ([\d,]+) bytes', text)
        if match:
            done, total = (int(match.group(i).replace(',', '')) for i in (2, 3))
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(100, int(100 * done / max(total, 1))))
            self.progress_bar.setFormat(tr('%p% del archivo'))
            self.activity.setText(tr('Descargando ') + match.group(1))
        else:
            self.progress_bar.setRange(0, 0)
            self.activity.setText(tr('Instalando dependencias… Consulta la actividad debajo.') if self.operation == 'install' else text.splitlines()[-1][:180])

    def failed(self, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(tr('Sin completar'))
        self.activity.setText(tr('Operación cancelada') if any(word in message.lower() for word in ('cancelad', 'cancelled')) else tr('No se pudo completar. Revisa el detalle y vuelve a intentar.'))
        self.status.appendPlainText(message)
        self.operation = None

    def show_requirements(self):
        manga = self.engine.currentData() == 'mangaocr'
        self.manga_options.setVisible(manga)
        self.language.setVisible(not manga)
        self.language_label.setVisible(not manga)
        if manga:
            self.guide.setText(tr('MangaOCR reconoce japonés. Necesita instalar el motor y descargar su modelo una sola vez con Internet. Usa los botones 1 y 2; después pulsa <b>Comprobar OCR</b>. Puede tardar varios minutos.'))
            from .manga import complete_model
            missing = []
            if not Path(self.python.text()).is_file() or not (Path(self.python.text()).parent.parent/'windows-runtime.json').is_file(): missing.append(tr('instalar el motor (paso 1)'))
            if not complete_model(self.model.text()): missing.append(tr('descargar el modelo (paso 2)'))
            self.status.setPlainText(tr('Falta: ') + '; '.join(missing) if missing else tr('Recursos encontrados. Pulsa Comprobar OCR para probarlos.'))
        else:
            self.guide.setText(tr('<b>Tesseract se instala fuera de esta aplicación.</b><br>1. Abre <a href="https://github.com/UB-Mannheim/tesseract/wiki">el instalador Windows de UB Mannheim</a> y elige la versión de 64 bits.<br>2. Instálalo en la carpeta predeterminada. Selecciona los idiomas que usarás: Japanese (jpn), Japanese vertical (jpn_vert), English (eng) o Spanish (spa).<br>3. Vuelve aquí, selecciona el idioma y pulsa <b>Comprobar OCR</b>.<br>Si falta un idioma, vuelve a ejecutar el instalador de Tesseract y añade sus datos. Si cambiaste PATH, reinicia Na’atik.'))
            from .ocr import tesseract_executable
            self.status.setPlainText(tr('Tesseract encontrado. Pulsa Comprobar OCR.') if tesseract_executable() else tr('Falta Tesseract. Sigue los pasos de arriba.'))

    def idle(self):
        if self.task.busy or self.probe_task.busy:
            self.status.setPlainText(tr('Espera o cancela la preparación actual antes de iniciar otra.'))
            return False
        return True

    def choose_model(self):
        if not self.idle(): return
        path = QFileDialog.getExistingDirectory(self, tr('Modelo MangaOCR local'), self.model.text())
        if path: self.model.setText(path)

    def runtime(self):
        if not self.idle(): return
        if QMessageBox.question(self, tr('Preparar runtime CPU'),
                tr('Instalar en .venv-mangaocr propio las dependencias del motor CPU con versiones y hashes registrados.\nFuentes: PyPI y download.pytorch.org. Licencias y avisos en docs/THIRD_PARTY_DEPENDENCIES.md.\nLa instalación Windows requiere Python 3.13 x64; el modelo se descarga por separado.\n¿Continuar?'),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        self.python.setText(defaults()['manga_python'])
        self.begin('install', tr('Instalando MangaOCR. La barra animada indica actividad; el instalador no proporciona un porcentaje total.'))
        self.task.start({'action': 'prepare_runtime'}, 960000)

    def download(self):
        if not self.idle(): return
        spec = catalogue()
        size = sum(item['bytes'] for item in spec['files'])
        if QMessageBox.question(self, tr('Confirmar descarga de modelo'),
                tr('{p0}\nRevisión: {p1}\n{p2} bytes\n{p3}\nFuente/licencia: {p4}\nDestino propio: {p5}\nNo se envía texto ni imágenes. Los parciales se conservan para reintentar.\n¿Descargar?', p0=f"{spec['id']}", p1=f"{spec['revision']}", p2=f'{size:,}', p3=f"{spec['license']}", p4=f"{spec['license_source']}", p5=f"{defaults()['manga_model']}"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        self.begin('download', tr('Conectando para descargar el modelo. Se mostrará el porcentaje de cada archivo.'))
        self.task.start({'action': 'prepare_model'}, 1800000)

    def prepared(self, result):
        operation = self.operation
        self.operation = None
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat('%p%')
        self.activity.setText(tr('Operación terminada'))
        if isinstance(result, dict) and 'model' in result:
            self.model.setText(result['model'])
        if isinstance(result, list):
            result = next((item for item in result if item.get('id') == self.engine.currentData()), {})
        if isinstance(result, dict) and 'status' in result:
            languages = result.get('languages', [])
            if self.engine.currentData() == 'tesseract' and self.language.currentData() not in languages:
                self.status.setPlainText(tr('Falta el idioma seleccionado. Añade sus datos con el instalador de Tesseract y vuelve a comprobar.\n') + result.get('detail', ''))
            else:
                self.status.setPlainText(status_text(result.get('status', '')) + ': ' + result.get('detail', ''))
        else:
            message = (tr('Motor instalado. Siguiente paso: Descargar modelo japonés.') if operation == 'install' else tr('Modelo descargado y verificado. Siguiente paso: Comprobar OCR.'))
            self.activity.setText(message)
            self.status.appendPlainText(message)
        if isinstance(result, dict) and result.get('status') not in (None, 'listo'):
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(tr('Requiere atención'))
            self.activity.setText(tr('Comprobación terminada: revisa los requisitos pendientes.'))

    def probe(self):
        if not self.idle(): return
        self.begin('probe', tr('Comprobando carga y reconocimiento de texto…'))
        if self.engine.currentData() == 'mangaocr':
            self.probe_task.program = self.python.text().strip()
            self.probe_task.start({'action': 'detect', 'model': self.model.text().strip()}, 180000)
        else:
            self.task.start({'action': 'detect'}, 120000)

    def save(self):
        if not self.idle(): return
        owner = self.owner
        if any(task.busy for task in (owner.ocr_task, owner.manga_task, owner.detect_task)):
            self.status.setPlainText(tr('Espera a que termine la detección/OCR principal antes de guardar.'))
            return
        owner.settings.update(manga_python=self.python.text().strip(), manga_model=self.model.text().strip(),
                              ocr_language=self.language.currentData(), ocr_engine=self.engine.currentData(), setup_completed=True)
        owner.manga_python_field.setText(owner.settings['manga_python'])
        owner.manga_model_field.setText(owner.settings['manga_model'])
        owner.persist()
        owner.redetect()
        self.close()

    def cancel(self):
        self.task.cancel()
        self.probe_task.cancel()

    def closeEvent(self, event):
        self.task.close()
        self.probe_task.close()
        event.accept()
