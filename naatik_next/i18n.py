"""Shared UTF-8 catalogs. UI language is independent of resource preferences.

The tiny per-profile language file is also readable before Python is installed.
Reading it never creates settings.json, so new-profile onboarding stays intact.
Language changes take effect on the next process start, including module labels.
"""
import json
import os
from pathlib import Path
import tempfile

LANGUAGES = ('es', 'en')


def language_path():
    profile = Path(os.environ.get('NAATIK_WINDOWS_PROFILE') or
                   str(Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))/'NaatikNextWindows'))
    if not profile.is_absolute():
        raise ValueError('NAATIK_WINDOWS_PROFILE must be absolute')
    return profile/'config'/'ui-language.txt'


def saved_language():
    try:
        value = language_path().read_text(encoding='utf-8-sig').strip()
        return value if value in LANGUAGES else 'es'
    except (OSError, ValueError):
        return 'es'


_language = os.environ.get('NAATIK_UI_LANGUAGE')
if _language not in LANGUAGES:
    _language = saved_language()
_catalogs = {code: json.loads((Path(__file__).with_name('locales')/(code+'.json')).read_text(encoding='utf-8'))
             for code in LANGUAGES}


def language():
    return _language


def tr(source, **values):
    value = _catalogs[_language].get(source, source)
    return value.format(**values) if values else value


def save_language(code):
    """Atomic, language-only write; do not create or rewrite resource preferences."""
    if code not in LANGUAGES:
        raise ValueError('Unsupported interface language')
    path = language_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.ui-language-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(code+'\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def status_text(value):
    # Protocol values stay stable; translate only at presentation boundaries.
    return tr({'listo':'Listo', 'detectado':'Detectado', 'recursos faltantes':'Recursos faltantes',
               'incompatible':'Incompatible', 'error':'Error'}.get(value, value))


def install_qt_translator(app):
    """Translate Qt-owned standard buttons/dialog controls using our catalogs."""
    from PySide6.QtCore import QTranslator, QLocale, QLibraryInfo, Qt
    # Native OS dialogs follow the Windows language, not this profile's choice.
    app.setAttribute(Qt.AA_DontUseNativeDialogs, True)
    for previous in getattr(app, '_naatik_translators', ()):
        app.removeTranslator(previous)
    translators = []
    if language() == 'es':
        base = QTranslator(app)
        if base.load('qtbase_es', QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
            app.installTranslator(base)
            translators.append(base)
    class StandardTranslator(QTranslator):
        def translate(self, context, source, disambiguation=None, n=-1):
            key = 'qt:'+source
            return _catalogs[_language].get(key, '')
        def isEmpty(self):
            return False
    QLocale.setDefault(QLocale('es_ES' if language()=='es' else 'en_US'))
    translator = StandardTranslator(app)
    app.installTranslator(translator)
    app._naatik_translators = [*translators, translator]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-language', choices=LANGUAGES, required=True)
    save_language(parser.parse_args().set_language)
