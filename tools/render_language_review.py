"""Reproducible offscreen visual fixtures; no interactive desktop certification."""
import argparse
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

parser=argparse.ArgumentParser()
parser.add_argument('--language',choices=('es','en'),required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
os.environ['NAATIK_UI_LANGUAGE']=args.language
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))

with tempfile.TemporaryDirectory(prefix='naatik-visual-') as profile:
    os.environ['NAATIK_WINDOWS_PROFILE']=profile
    from PySide6.QtWidgets import QApplication, QGroupBox, QDialog
    from PySide6.QtGui import QFontDatabase, QFont
    from naatik_next.i18n import install_qt_translator, save_language
    save_language(args.language)
    from naatik_next.app import Window
    from naatik_next.setup_dialog import SetupDialog
    from naatik_next.language_dialog import show_language
    app=QApplication([]);install_qt_translator(app)
    # Qt offscreen does not enumerate Windows fonts. Load an existing system
    # font into this test process only; nothing is installed or redistributed.
    fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    for name in ('segoeui.ttf','segoeuib.ttf','YuGothR.ttc','msgothic.ttc'):
        if (fonts/name).is_file():QFontDatabase.addApplicationFont(str(fonts/name))
    app.setFont(QFont('Segoe UI',10))
    # Only suppress startup probes. All layouts are the actual application widgets.
    with patch('naatik_next.app.QTimer.singleShot'):
        window=Window(startup_action='capture')
    window.resize(1080,820);window.show()
    def capture(widget,name):
        app.processEvents();app.processEvents()
        path=args.output/(args.language+'-'+name+'.png')
        assert widget.grab().save(str(path))
    for index in range(window.tabs.count()):
        window.tabs.setCurrentIndex(index)
        capture(window,'tab-'+str(index))
    # Expanded long guidance, including scrollable advanced content.
    for index in range(window.tabs.count()):
        widget=window.tabs.widget(index)
        groups=widget.findChildren(QGroupBox)
        if not any(g.isCheckable() for g in groups):continue
        window.tabs.setCurrentIndex(index)
        for group in groups:
            if group.isCheckable():group.setChecked(True)
        capture(window,'expanded-'+str(index))
        if hasattr(widget,'verticalScrollBar'):
            widget.verticalScrollBar().setValue(widget.verticalScrollBar().maximum())
            capture(window,'expanded-bottom-'+str(index))
    window.show_tutorial()
    for step in range(6):
        window.tutorial_dialog.step=step;window.tutorial_dialog.render()
        capture(window.tutorial_dialog,'tutorial-'+str(step))
    window.tutorial_dialog.close()
    setup=SetupDialog(window);setup.show()
    capture(setup,'ocr-tesseract')
    setup.engine.setCurrentIndex(setup.engine.findData('mangaocr'))
    capture(setup,'ocr-manga')
    setup.close()
    def render_dialog(dialog):
        dialog.show();capture(dialog,'language');dialog.reject();return 0
    with patch.object(QDialog,'exec',render_dialog):show_language(window)
    window.close()
print('Offscreen images:',args.output)
