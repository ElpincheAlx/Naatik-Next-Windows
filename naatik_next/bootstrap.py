"""Explicit Windows installer entry point."""
def main():
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().parent.parent/'tools/install_windows.py'),run_name='__main__')
if __name__ == '__main__': main()
