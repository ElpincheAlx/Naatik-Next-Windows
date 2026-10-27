"""Isolated CPython 3.13 x64 installer; resolve once, then install only hashed artifacts.

Base intentionally uses Argos package/tokenizer APIs without its optional SBD stack.
Linux locks are evidence only. Windows locks and reports are generated per mode,
with exact selected filenames, URLs, versions and SHA256 from pip's report.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

PROJECT=Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from naatik_next.i18n import tr


def validate_report(report):
    lines=[]
    for item in report['install']:
        metadata=item['metadata']; download=item['download_info']
        name,version=metadata['name'],metadata['version']
        url=download['url'];sha=download.get('archive_info',{}).get('hashes',{}).get('sha256')
        from urllib.parse import urlsplit,unquote
        parsed=urlsplit(url)
        if (parsed.scheme!='https' or parsed.hostname not in ('files.pythonhosted.org','download.pytorch.org','download-r2.pytorch.org')
                or parsed.username or parsed.password or not re.fullmatch('[0-9a-f]{64}',sha or '')
                or not re.fullmatch('[A-Za-z0-9_.-]+',name) or not re.fullmatch('[A-Za-z0-9.+_-]+',version)):
            raise RuntimeError(tr('Origen/hash de dependencia no permitido: ')+name)
        filename=unquote(parsed.path.rsplit('/',1)[-1])
        # Inspect the wheel platform tag, not the package name (win32-setctime
        # is a valid pure-Python Windows dependency despite its name).
        if filename.endswith('.whl') and filename.rsplit('-',1)[-1] not in ('win_amd64.whl','any.whl'):
            raise RuntimeError(tr('Artefacto no válido para Windows x64: ')+filename)
        lines.append(f'{name} @ {url} --hash=sha256:{sha}')
    if not lines: raise RuntimeError(tr('Resolución vacía; no se puede generar un lock.'))
    return '\n'.join(sorted(lines,key=str.lower))+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--phrase',action='store_true'); modes.add_argument('--manga-cpu',action='store_true')
    modes.add_argument('--translation',action='store_true')
    parser.add_argument('--target',type=Path)
    args=parser.parse_args()
    if (sys.platform!='win32' or sys.version_info[:2]!=(3,13)
            or platform.machine().lower() not in ('amd64','x86_64')
            or __import__('sysconfig').get_config_var('Py_GIL_DISABLED')):
        parser.error(tr('Se requiere CPython 3.13 estándar x64 en Windows 10/11. Instala desde python.org con Python Launcher.'))
    mode='manga' if args.manga_cpu else 'phrase' if args.phrase else 'translation' if args.translation else 'base'
    target=args.target or PROJECT/({'base':'.venv','phrase':'.venv-phrase','manga':'.venv-mangaocr','translation':'.venv-translation'}[mode])
    if target.is_symlink(): raise RuntimeError(tr('No se admite un entorno enlazado.'))
    target=target.absolute()
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONUTF8='1',PIP_CONFIG_FILE=os.devnull)
    for key in ('PYTHONPATH','PYTHONHOME','PIP_EXTRA_INDEX_URL','PIP_INDEX_URL'):env.pop(key,None)
    def run(argv):
        subprocess.run([str(a) for a in argv],check=True,env=env,cwd=PROJECT)
    python=target/'Scripts/python.exe'
    if not python.is_file(): run([sys._base_executable,'-m','venv',target])
    # pip uses sys.prefix for extraction. Torch's bundled notices can exceed
    # MAX_PATH even in ordinary Documents folders. Extended Win32 paths avoid
    # requiring administrator access to enable system-wide long paths.
    if not str(python).startswith('\\\\?\\'):
        value=str(python)
        python=Path('\\\\?\\UNC\\'+value[2:] if value.startswith('\\\\') else '\\\\?\\'+value)
    run([python,'-c','import sys,pathlib; assert sys.version_info[:2]==(3,13); assert sys.prefix!=sys.base_prefix; assert "include-system-site-packages = false" in (pathlib.Path(sys.prefix)/"pyvenv.cfg").read_text().lower()'])
    # Serialize installing this environment across GUI and command line invocations.
    sys.path.insert(0,str(PROJECT))
    from naatik_next import filelock
    with (target/'.install.lock').open('a',encoding='utf-8') as stream:
        filelock.flock(stream,filelock.LOCK_EX|filelock.LOCK_NB)
        was_ready=(target/'windows-runtime.json').is_file()
        (target/'windows-runtime.json').unlink(missing_ok=True)
        lock=PROJECT/'locks'/f'{mode}-windows.lock'
        seed=PROJECT/'locks'/f'{mode}-windows.in'
        if lock.exists() and lock.is_symlink(): raise RuntimeError(tr('Lock enlazado no permitido.'))
        pip=[python,'-m','pip','--isolated']
        options=['--index-url','https://pypi.org/simple','--no-cache-dir','--timeout','20','--retries','1']
        if mode in ('phrase','manga'):
            run([*pip,'install',*options,'--no-deps','--require-hashes','-r',PROJECT/'locks/build-windows.lock'])
        if not lock.is_file():
            print(tr('Preparando lock Windows: versiones fijadas; se instalarán únicamente los hashes seleccionados.'),flush=True)
            report=target/'resolve-report.json'
            resolve=[*pip,'install','--dry-run','--ignore-installed','--report',report,*options,
                     '--only-binary=:all:','--no-binary=unidic-lite,jaconv,fire','--no-build-isolation','-r',seed]
            # Curated package API: do not resolve Argos' unused sentence splitting models.
            if mode in ('base','translation'):resolve.append('--no-deps')
            # Only Torch comes from the CPU index (direct hashed seed URL).
            # An extra index for all packages can select mirror artifacts without hashes.
            run(resolve)
            data=json.loads(report.read_text(encoding='utf-8'))
            content=validate_report(data)
            lock.parent.mkdir(exist_ok=True)
            fd,name=tempfile.mkstemp(dir=lock.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as output:output.write(content)
                os.replace(name,lock)
            finally:Path(name).unlink(missing_ok=True)
            (lock.parent/f'{mode}-report.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        # pip can leave dist-info after an interrupted/long-path install, and
        # then falsely consider an incomplete Torch installation satisfied.
        repair=[] if was_ready else ['--ignore-installed']
        run([*pip,'install',*options,*repair,'--no-deps','--require-hashes','--no-build-isolation','-r',lock])
        if mode=='base':
            check='from PIL import Image; from naatik_next.translation import package_api; package_api(); import ctranslate2,sentencepiece; from PySide6.QtWidgets import QApplication'
        elif mode=='phrase':
            check='from naatik_next.phrase_worker import Analyzer; assert Analyzer().analyze("日本語です")["tokens"]'
        elif mode=='manga':
            check='import torch; assert torch.version.cuda is None, "Se exige Torch CPU"; from manga_ocr import MangaOcr'
        else:check='from naatik_next.translation import package_api; package_api(); import ctranslate2,sentencepiece'
        # Smoke checks must never initialize the real user's profile.
        with tempfile.TemporaryDirectory(prefix='naatik-install-',dir=target) as profile:
            saved_profile=env.get('NAATIK_WINDOWS_PROFILE')
            env['NAATIK_WINDOWS_PROFILE']=profile
            try:
                run([python,'-c',check])
            except subprocess.CalledProcessError as error:
                raise RuntimeError(tr('Falló la prueba de carga del motor. Si el diagnóstico indica DLL, instala Microsoft Visual C++ Redistributable x64 desde https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist y repite install.cmd. No hacen falta CUDA ni compiladores para las ruedas Windows.')) from error
            finally:
                if saved_profile is None: env.pop('NAATIK_WINDOWS_PROFILE',None)
                else: env['NAATIK_WINDOWS_PROFILE']=saved_profile
        if mode in ('phrase','manga'):run([*pip,'check'])
        runtime_version=subprocess.check_output([str(python),'-c','import sys; print(sys.version)'],env=env,text=True).strip()
        (target/'windows-runtime.json').write_text(json.dumps({'mode':mode,'cpu':True,'lock_sha256':hashlib.sha256(lock.read_bytes()).hexdigest(),'python':runtime_version}),encoding='utf-8')
    print(tr('Entorno preparado. Abre launch.cmd; modelos OCR/traducción se preparan explícitamente desde la interfaz.'),flush=True)

if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,subprocess.CalledProcessError) as error:
        print(tr('Instalación incompleta: ')+str(error),file=sys.stderr);sys.exit(1)
