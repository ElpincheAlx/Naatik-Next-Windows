import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QColor
from tests.test_processes import APP, spin_until
from naatik_next import storage, integrations, instance, filelock
from naatik_next.hotkey import combination, GlobalShortcut
from naatik_next.processes import Task
from naatik_next.windows_capture import Selector
from naatik_next.translation_runtime import run_progress

class WindowsPortTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='naatik-windows-test-')
        self.env=patch.dict(os.environ,NAATIK_WINDOWS_PROFILE=self.tmp.name);self.env.start()
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def test_profile_is_independent_of_xdg(self):
        with patch.dict(os.environ,XDG_CONFIG_HOME='/must-not-use'):
            self.assertEqual(storage.paths()['config'],Path(self.tmp.name)/'config')
        storage.save_settings({'word':'日本語'});self.assertEqual(storage.load_settings()['word'],'日本語')
    def test_relative_profile_rejected(self):
        with patch.dict(os.environ,NAATIK_WINDOWS_PROFILE='relative'):
            with self.assertRaises(storage.UserError):storage.paths()
    def test_named_pipe_locator_cannot_redirect_to_other_profile(self):
        state=storage.paths()['state'];name=instance.endpoint(state)
        self.assertTrue(name.startswith('naatik-next-windows-'));self.assertNotIn('/',name)
        record=state/'application.endpoint';record.write_text(json.dumps(dict(v=1,name='other',token='a'*32)))
        with self.assertRaises(storage.UserError):instance.recorded_endpoint(state)
        record.write_text(json.dumps(dict(v=1,name=name,token='a'*32)))
        self.assertEqual(instance.recorded_endpoint(state),name)
    def test_shortcuts_bound_to_windows_key_range(self):
        self.assertEqual(combination('Ctrl+Alt+F24')[1],'F24')
        for value in ('Ctrl+F25','Shift+A','Ctrl+A, Ctrl+B'):
            with self.assertRaises(storage.UserError):combination(value)
    def test_offscreen_does_not_claim_hotkey_registered(self):
        shortcut=GlobalShortcut()
        with self.assertRaises(storage.UserError):shortcut.register('Ctrl+Alt+R')
        self.assertEqual(shortcut.active,'');shortcut.close()
    def test_shortcut_ids_do_not_collide(self):
        a,b=GlobalShortcut(),GlobalShortcut();self.assertNotEqual(a.ident,b.ident)
    def test_integration_literal_unicode_and_metacharacters(self):
        launcher=Path(self.tmp.name)/"日本's $test; (demo)/launch.ps1"
        script=integrations.action_script('translator',launcher)
        decoded=base64.b64decode(script.split('-EncodedCommand ')[1].strip()).decode('utf-16-le')
        self.assertIn("日本''s $test; (demo)",decoded)
        self.assertIn(' --translator',decoded);self.assertNotIn('/bin/sh',script)
    def test_generated_launcher_no_clobber(self):
        target=Path(self.tmp.name)/'capturar.cmd';integrations.write_action_script(target,'capture-copy')
        with self.assertRaises(FileExistsError):integrations.write_action_script(target,'phrase')
        self.assertTrue(target.read_text().startswith('@echo off'))
    def test_installer_rejects_untrusted_hashes_and_platforms(self):
        path=Path(__file__).resolve().parents[1]/'tools/install_windows.py'
        spec=importlib.util.spec_from_file_location('installer',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        item=dict(metadata=dict(name='demo',version='1.0'),download_info=dict(url='https://files.pythonhosted.org/demo-cp313-cp313-win_amd64.whl',archive_info=dict(hashes=dict(sha256='a'*64))))
        self.assertIn('--hash=sha256:',module.validate_report(dict(install=[item])))
        for url in ('http://files.pythonhosted.org/a.whl','https://evil.example/a.whl','https://files.pythonhosted.org/demo-linux.whl'):
            item['download_info']['url']=url
            with self.assertRaises(RuntimeError):module.validate_report(dict(install=[item]))
        item['download_info']['url']='https://files.pythonhosted.org/win32_setctime-1.2.0-py3-none-any.whl'
        self.assertIn('win32_setctime',module.validate_report(dict(install=[item])))
    def test_console_translation_loads_native_dlls_without_qt_import(self):
        code='from naatik_next.translation import package_api; package_api(); import sentencepiece,ctranslate2'
        subprocess.run([sys.executable,'-c',code],check=True,timeout=30)
    def test_progress_reader_handles_windows_style_pipes(self):
        messages=[]
        run_progress([sys.executable,'-c','print("ready",flush=True)'],messages.append,timeout=5)
        self.assertIn('ready',''.join(messages))
        with self.assertRaises(storage.UserError):
            run_progress([sys.executable,'-c','import time;time.sleep(30)'],messages.append,timeout=.1)
    def test_selector_preserves_native_pixels_at_200_percent(self):
        image=QPixmap(400,200);image.fill(QColor('white'));image.setDevicePixelRatio(2)
        screen=Mock();from PySide6.QtCore import QRect
        screen.geometry.return_value=QRect(0,0,200,100)
        finished=[];selector=Selector(screen,image,finished.append,None)
        def event(point):
            value=Mock();value.button.return_value=Qt.LeftButton
            value.position.return_value.toPoint.return_value=point;return value
        selector.mousePressEvent(event(QPoint(10,10)))
        selector.mouseReleaseEvent(event(QPoint(59,39)))
        self.assertEqual((finished[0].width(),finished[0].height()),(100,60))
        selector.deleteLater();APP.processEvents()
    def test_ocr_tools_use_unicode_subprocess_output(self):
        from naatik_next.ocr import run
        self.assertEqual(run([sys.executable,'-c','print("日本語")']).strip(),'日本語')
    @unittest.skipUnless(sys.platform=='win32','Requires real Windows kernel')
    def test_windows_job_terminates_descendant(self):
        from naatik_next.windows_native import Job
        marker=Path(self.tmp.name)/'child.pid'
        code='import subprocess,sys; input(); child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]); print(child.pid,flush=True); input()'
        process=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        job=None
        try:
            job=Job(process.pid)
            process.stdin.write('\n');process.stdin.flush()
            child=int(process.stdout.readline())
            job.close();process.wait(timeout=5)
            import ctypes as C
            from ctypes import wintypes as W
            api=C.WinDLL('kernel32',use_last_error=True)
            api.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];api.OpenProcess.restype=W.HANDLE
            api.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];api.WaitForSingleObject.restype=W.DWORD
            api.CloseHandle.argtypes=[W.HANDLE]
            handle=api.OpenProcess(0x100000,False,child)
            if handle:
                try:self.assertEqual(api.WaitForSingleObject(handle,5000),0)
                finally:api.CloseHandle(handle)
        finally:
            if job:job.close()
            if process.poll() is None:process.kill();process.wait()
            process.stdin.close();process.stdout.close()
