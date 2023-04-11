import subprocess
import psutil
import os
import json
import pathlib
import time
import conf

if conf.OS == "linux":
    while True:
        try:
            f = open(f"{pathlib.Path(__file__).parent.resolve()}/grep.txt", "r")
            os.remove(f)
        except:
            pass
        os.system(f"pgrep python3 > {pathlib.Path(__file__).parent.resolve()}/pgrep.txt")

        processes = []

        with open("pgrep.txt") as pgrep:
            processes.clear()
            for p in pgrep:
                processes.append(int(p))

        for p in processes:
            try:
                bot_path = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "r"))
                webpanel_proc = json.load(
                    open(f"{pathlib.Path(__file__).parent.resolve()}/data/webpanel-data.json", "r"))
                try:
                    bot_proc = json.load(
                        open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "r"))
                except FileNotFoundError:
                    bot_proc = {"process-id": False}
                if webpanel_proc["process-id"] == p:
                    print(f"{p} is main process of webpanel")
                elif bot_proc["process-id"] == p:
                    print(f"{p} is main process of discord worker")
                elif webpanel_proc["restarter-pid"] == p:
                    print(f"{p} is main process of restarter")
                elif webpanel_proc["error-correction-pid"] == p:
                    print(f"{p} is main process of error corrector")
                elif "discord_worker" in psutil.Process(p).cmdline()[1]:
                    psutil.Process(p).kill()
                    print(f"Killed {p} because of duplicate of discord worker")
                elif "restarter" in psutil.Process(p).cmdline()[1]:
                    psutil.Process(p).kill()
                    print(f"Killed {p} because of duplicate of restarter")
                elif "main_instance" in psutil.Process(p).cmdline()[1]:
                    psutil.Process(p).kill()
                    print(f"Killed {p} because of duplicate of webpanel")
                elif "error-correction" in psutil.Process(p).cmdline()[1]:
                    psutil.Process(p).kill()
                    print(f"Killed {p} because of duplicate of error corrector")
                elif bot_path["start-command-command"] in psutil.Process(p).cmdline()[1]:
                    psutil.Process(p).kill()
                    print(f"Killed {p} because of duplicate of discord bot")
            except IndexError:
                continue
        print("----------------------------------------------------")
        time.sleep(300)

if conf.OS == "windows":
    print("Error correction isn't supported in windows yet.")