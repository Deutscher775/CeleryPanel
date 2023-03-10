import socket
from urllib import parse
import colorama
import platform

os_get = platform.system().lower()
if os_get == "windows":
    OS = "windows"
elif os_get == "linux":
    OS = "linux"
else:
    print(colorama.Fore.RED + "Your operating system couldn't be detected or is not supported yet" + colorama.Style.RESET_ALL)

# webserver config

DEBUGGING = True
PORT = 80
SESSION_SECRET_KEY = "S0me_K3y"

# OAuth config

DOMAIN_NAME = ""
DOMAIN_PORT = 80

if DOMAIN_NAME is str:
    if DOMAIN_PORT is int:
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


OAUTH_CLIENT_SECRET = "
OAUTH_TOKEN = ""
OAUTH_CLIENT_ID = 
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={OAUTH_CLIENT_ID}&redirect_uri={parse.quote(AFTER_OAUTH_REDIRECT_URL)}&response_type=code&scope=identify%20guilds"

# Discord bot config

DISCORD_BOT_TOKEN = ""

# Discord server config

DISCORD_SERVER_ID = 

# Discord allowed IDs config

DISCORD_ACCESS_ROLE_ID = 
DISCORD_PANEL_ADMINISTRATOR_ID =
DISCORD_PANEL_FULL_ACCESS_USER_IDS = []

# notification config (soon)

NOTIFICATION_ON_DENIED_ACCESS = False
NOTIFICATION_CHANNEL_ID = 
NOTIFICATION_WEBHOOK_URL = ""
