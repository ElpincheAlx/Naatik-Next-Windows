from naatik_next.i18n import tr, language
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_processes import APP
from naatik_next.translation_runtime import run_progress
from naatik_next.setup_dialog import SetupDialog
from naatik_next.app import Window

class SetupProgressTests(unittest.TestCase):
    def test_installer_output_arrives_before_process_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp)/'received'
            code="import pathlib,time,sys; print('downloading',flush=True); p=pathlib.Path(sys.argv[1]); deadline=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<deadline: time.sleep(.02)\nassert p.exists(), 'Output was buffered until exit'"
            seen=[]
            def progress(text):
                seen.append(text)
                marker.touch()
            run_progress([sys.executable,'-u','-c',code,str(marker)],progress,timeout=5)
            self.assertIn('downloading',''.join(seen))

    def test_setup_progress_success_error_and_control_state(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,NAATIK_WINDOWS_PROFILE=tmp):
            with patch('naatik_next.app.QTimer.singleShot'):
                owner=Window()
            dialog=SetupDialog(owner)
            try:
                dialog.begin('download','Conectando')
                self.assertEqual(dialog.progress_bar.maximum(),0)
                dialog.update_progress('model.safetensors: 500 / 1,000 bytes')
                self.assertEqual(dialog.progress_bar.value(),50)
                dialog.task.busy=True
                dialog.update_busy(True)
                self.assertFalse(dialog.engine.isEnabled())
                dialog.task.busy=False
                dialog.update_busy(False)
                self.assertTrue(dialog.engine.isEnabled())
                dialog.prepared({'model':tmp})
                self.assertEqual(dialog.progress_bar.value(),100)
                self.assertIn(tr('Comprobar OCR'),dialog.activity.text())
                dialog.begin('install',tr('Preparando'))
                dialog.failed('Error de conexión')
                self.assertEqual(dialog.progress_bar.value(),0)
                self.assertIn('Error de conexión',dialog.status.toPlainText())
            finally:
                dialog.close()
                owner.close()

class MangaProbeLifecycleTests(unittest.TestCase):
    def test_one_shot_probe_finishes_without_waiting_for_stdin_close(self):
        from naatik_next.processes import Task
        from tests.test_processes import spin_until
        task=Task(module='naatik_next.manga_worker')
        answers=[]; errors=[]; progress=[]
        task.result.connect(answers.append)
        task.error.connect(errors.append)
        task.progress.connect(progress.append)
        try:
            task.start({'action':'detect','model':'missing-model-for-test'},timeout=5000)
            spin_until(lambda:bool(answers or errors),timeout=7)
            self.assertFalse(errors)
            self.assertEqual(answers[0]['status'],'recursos faltantes')
            self.assertFalse(task.busy)
            self.assertTrue(progress)
        finally:task.close()

    def test_persistent_probe_accepts_a_second_request(self):
        from naatik_next.processes import Task
        from tests.test_processes import spin_until
        task=Task(persistent=True,module='naatik_next.manga_worker')
        answers=[]; errors=[]
        task.result.connect(answers.append);task.error.connect(errors.append)
        try:
            for count in (1,2):
                task.start({'action':'detect','model':'missing-model-for-test'},timeout=5000)
                spin_until(lambda:len(answers)==count or bool(errors),timeout=7)
                self.assertFalse(errors)
                self.assertEqual(len(answers),count)
        finally:task.close()
