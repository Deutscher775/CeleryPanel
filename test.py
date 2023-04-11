import subprocess
import pathlib

subprocess.run(f"py {pathlib.Path(__file__).parent.resolve()}\main_instance.py")
