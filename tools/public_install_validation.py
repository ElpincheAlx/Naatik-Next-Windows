"""Copy source without environments, private profiles or generated artifacts."""
from pathlib import Path
import shutil

def copy_source(root, destination):
    root,destination=Path(root),Path(destination)
    destination.mkdir()
    for name in ('naatik_next','tests','tools','locks','examples'):
        shutil.copytree(root/name,destination/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*-report.json'))
    for name in ('launch.cmd','launch.ps1','install.cmd','install.ps1'):
        shutil.copy2(root/name,destination/name)
