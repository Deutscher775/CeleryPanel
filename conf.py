import socket
from urllib import parse
import colorama
import platform
import json
import pathlib

config = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json"))

os_get = platform.system().lower()
if os_get == "windows":
    OS = "windows"
elif os_get == "linux":
    OS = "linux"
else:
    print(
        colorama.Fore.RED + "Your operating system couldn't be detected or is not supported yet" + colorama.Style.RESET_ALL)

# webserver config

DEBUGGING = config["debugging"]
PORT = config["port"]
SESSION_SECRET_KEY = config["session-key"]

# OAuth config

DOMAIN_NAME = config["domain-name"]
DOMAIN_PORT = config["domain-port"]

if DOMAIN_NAME and not DOMAIN_NAME is False:
    if DOMAIN_PORT and not DOMAIN_PORT is False:
        AFTER_OAUTH_REDIRECT_URL = f"http://{DOMAIN_NAME}:{DOMAIN_PORT}/oauth/callback"  # if you change this, make sure to change it in the discord developer portal too
        HOST_IP = DOMAIN_NAME
    else:
        AFTER_OAUTH_REDIRECT_URL = f"http://{DOMAIN_PORT}:{PORT}/oauth/callback"  # if you change this, make sure to change it in the discord developer portal too

else:
    # the following code gets the ip of the server automatically
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        HOST_IP = s.getsockname()[0]
    except:
        print(colorama.Fore.CYAN + "----\nYour server doesn't seem to be connected to the internet or blocks "
                                   f"ips.\nRunning {colorama.Fore.LIGHTBLUE_EX}localhost.\n{colorama.Fore.CYAN}----" + colorama.Style.RESET_ALL)
        HOST_IP = "localhost"
    AFTER_OAUTH_REDIRECT_URL = f"http://{HOST_IP}:{PORT}/oauth/callback"  # if you change this, make sure to change it in the discord developer portal too

OAUTH_CLIENT_SECRET = config["discord-oauth-secret"]
OAUTH_TOKEN = config["discord-oauth-token"]
OAUTH_CLIENT_ID = config["discord-oauth-id"]
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={OAUTH_CLIENT_ID}&redirect_uri={parse.quote(AFTER_OAUTH_REDIRECT_URL)}&response_type=code&scope=identify%20guilds"

# Discord bot config

DISCORD_BOT_TOKEN = config["discord-bot-token"]

# Discord server config

DISCORD_SERVER_ID = config["discord-server-id"]

# Discord allowed IDs config

DISCORD_ACCESS_ROLE_ID = config["discord-access-role-id"]
DISCORD_PANEL_ADMINISTRATOR_ID = config["discord-administrator-id"]
full_access_id = []
full_access_id.clear()
for aid in config["discord-full-access-user-ids"]:
    full_access_id.append(aid)

DISCORD_PANEL_FULL_ACCESS_USER_IDS = full_access_id

# notification config

NOTIFICATION_ON_DENIED_ACCESS = False
NOTIFICATION_CHANNEL_ID = 6
NOTIFICATION_WEBHOOK_URL = ""
