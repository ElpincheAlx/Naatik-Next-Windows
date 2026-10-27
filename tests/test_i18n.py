"""Language persistence, catalog integrity and real per-language GUI processes."""
import ast
import json
import os
from pathlib import Path
import string
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent


class LanguageTests(unittest.TestCase):
    def run_python(self, code, profile, language=None):
        env=dict(os.environ, NAATIK_WINDOWS_PROFILE=str(profile), QT_QPA_PLATFORM='offscreen', PYTHONUTF8='1')
        env.pop('NAATIK_UI_LANGUAGE',None)
        if language:env['NAATIK_UI_LANGUAGE']=language
        result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        return result.stdout

    def test_catalogs_have_same_keys_and_placeholders(self):
        catalogs=[json.loads((ROOT/'naatik_next/locales'/f'{c}.json').read_text(encoding='utf-8')) for c in ('es','en')]
        self.assertEqual(catalogs[0].keys(),catalogs[1].keys())
        for key in catalogs[0]:
            if key.startswith('qt:'):continue
            def fields(value):
                return {field for _,field,_,_ in string.Formatter().parse(value) if field is not None}
            self.assertEqual(fields(catalogs[0][key]),fields(catalogs[1][key]),key)
            self.assertTrue(catalogs[1][key],key)
        # Every literal translation call is backed by both catalogs.
        for file in (ROOT/'naatik_next').glob('*.py'):
            for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='tr' and node.args and isinstance(node.args[0],ast.Constant):
                    self.assertIn(node.args[0].value,catalogs[0],str(file))

    def test_new_install_keeps_new_profile_tutorial(self):
        for code in ('es','en'):
            with self.subTest(language=code),tempfile.TemporaryDirectory() as profile:
                self.run_python(f'from naatik_next.i18n import save_language; save_language({code!r})',profile)
                self.run_python(f'''
from naatik_next.i18n import language
from naatik_next.storage import load_settings, paths
from naatik_next.tutorial import initial_state, automatic
assert language()=={code!r}
assert load_settings()=={{}}
assert not (paths()['config']/'settings.json').exists()
assert automatic(initial_state({{}}))
''',profile)

    def test_repair_and_explicit_change_preserve_every_other_preference(self):
        for code in ('es','en'):
            with self.subTest(language=code),tempfile.TemporaryDirectory() as profile:
                config=Path(profile)/'config';config.mkdir()
                settings=config/'settings.json'
                original=b'{"ocr_language":"jpn_vert","translation_route":["ja","en","es"],"tutorial":{"status":"in_progress","step":3},"manga_model":"D:/keep/model","custom":42}'
                settings.write_bytes(original)
                self.run_python(f'from naatik_next.i18n import save_language; save_language({code!r}); save_language({code!r})',profile)
                self.assertEqual(settings.read_bytes(),original)
                other='en' if code=='es' else 'es'
                self.run_python(f'from naatik_next.i18n import save_language; save_language({other!r})',profile)
                self.assertEqual(settings.read_bytes(),original)
                self.assertEqual((config/'ui-language.txt').read_text().strip(),other)

    def test_language_save_failure_preserves_previous_file(self):
        from naatik_next.i18n import save_language, saved_language
        with tempfile.TemporaryDirectory() as profile,patch.dict(os.environ,NAATIK_WINDOWS_PROFILE=profile):
            save_language('es')
            with patch('naatik_next.i18n.os.replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):save_language('en')
            self.assertEqual(saved_language(),'es')
            with self.assertRaises(ValueError):save_language('xx')
            self.assertEqual(saved_language(),'es')

    def test_saved_choice_waits_for_restart_and_workers_keep_active_language(self):
        with tempfile.TemporaryDirectory() as profile:
            self.run_python('''
from naatik_next.i18n import language, save_language
assert language()=='es'
save_language('en')
assert language()=='es'
''',profile,'es')
            self.run_python("from naatik_next.i18n import language; assert language()=='en'",profile)

    def test_both_languages_real_widgets_and_tutorial_flow(self):
        for code in ('es','en'):
            with self.subTest(language=code),tempfile.TemporaryDirectory() as profile:
                self.run_python('''
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QPushButton
from naatik_next.i18n import tr, install_qt_translator
from naatik_next.app import Window
from naatik_next.storage import load_settings
from naatik_next.tutorial import automatic
app=QApplication([]); install_qt_translator(app)
with patch.object(Window,'prepare_selected'):
    w=Window(); app.processEvents()
    assert w.tutorial_dialog.isVisible()
    assert w.tutorial_dialog.windowTitle()==tr('Tutorial y configuración inicial')
    assert w.tabs.tabText(0)==tr('Captura y resultado')
    assert tr('Configuración') in [a.text() for a in w.menuBar().actions()]
    assert w.dictionary_setup_btn.text()==tr('Importar o activar diccionarios…')
    w.tutorial_dialog.move(1); w.tutorial_dialog.close()
    w.show_tutorial(); assert w.tutorial_dialog.step==1
    w.tutorial_dialog.skip(); w.close()
    w=Window(); app.processEvents()
    assert not hasattr(w,'tutorial_dialog')
    actions=w.menuBar().actions()
    help_action=next(a for a in actions if a.text()==tr('Ayuda'))
    help_menu=help_action.menu()
    help_entries=help_menu.actions()
    help_entries[0].trigger()
    assert w.tutorial_dialog.isVisible()
    w.close()
    saved=load_settings()['tutorial'].copy()
    w=Window(startup_action='capture'); app.processEvents()
    assert not hasattr(w,'tutorial_dialog')
    assert w.settings['tutorial']==saved
    w.close()
''',profile,code)
