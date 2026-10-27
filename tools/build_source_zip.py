"""Export source for Windows without environments, private data or model caches."""
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT.parent/'Naatik-next-windows-source.zip'
with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or path.is_symlink():continue
        if relative.parts[0] not in ('.github','packaging','docs','examples','locks','naatik_next','tests','tools','README.md','AGENTS.md','install.cmd','install.ps1','launch.cmd','launch.ps1','.gitignore'):continue
        if any(part.startswith(('.venv','.profile','.wheelhouse','.python')) or part=='__pycache__' for part in relative.parts):continue
        if path.name.endswith('-install.txt') or path.name=='validation-run.txt':continue
        if path.suffix in ('.pyc','.log'):continue
        archive.write(path,'Naatik-next-windows/'+relative.as_posix())
print(str(TARGET))
print('SHA256 '+hashlib.sha256(TARGET.read_bytes()).hexdigest())
