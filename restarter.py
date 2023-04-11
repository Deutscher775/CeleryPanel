import json
import subprocess
import time
import pathlib
import psutil
import conf

while True:
    f_json = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/data/webpanel-data.json", "r"))
    if f_json["restart"] is True:
        pid = f_json["process-id"]
        try:
            process = psutil.Process(pid)
            process.kill()
            print(f"Killed {pid}")
        except psutil.NoSuchProcess:
            pass
        if conf.OS == "windows":
            subprocess.Popen(f"py {pathlib.Path(__file__).parent.resolve()}/main_instance.py")
        if conf.OS == "linux":
            subprocess.Popen(["python3", f"{pathlib.Path(__file__).parent.resolve()}/main_instance.py"])
    time.sleep(5)
