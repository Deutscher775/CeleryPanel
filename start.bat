@echo off
start "Web dashboard" py ./main_instance.py
start "Discord bot" py ./discord_worker.py