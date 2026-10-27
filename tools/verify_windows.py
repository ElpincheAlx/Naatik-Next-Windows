"""Isolated verification; offscreen never certifies interactive Windows capture."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
with tempfile.TemporaryDirectory(prefix='naatik-windows-validation-') as profile:
    os.environ['NAATIK_WINDOWS_PROFILE']=profile
    os.environ['QT_QPA_PLATFORM']='offscreen'
    os.environ['PYTHONUTF8']='1'
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
