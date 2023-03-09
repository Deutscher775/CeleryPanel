import socket
from urllib import parse
import colorama

# the following code gets the ip of the server automatically
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    HOST_IP = s.getsockname()[0]
except:
    print(colorama.Fore.CYAN + "----\nYour server doesn't seem to be connected to the internet or blocks "
                                 f"ips.\nRunning {colorama.Fore.LIGHTBLUE_EX}localhost.\n{colorama.Fore.CYAN}----" + colorama.Style.RESET_ALL)
    HOST_IP = "localhost"

# Please enter your os the panel is runnig on, just type "windows" or "linux"

OS = "windows"

# webserver config

DEBUGGING = True
PORT = 80
SESSION_SECRET_KEY = "kurumi_stinkt"

# OAuth config

OAUTH_CLIENT_SECRET = "6oYTQcpoP3d6rj-LZjloylYqzOBdC5zX"
OAUTH_TOKEN = "MTA2MzM4NjY0MzM1NDExMjAxMA.GwwK34.qlhCeJut9NlDqt5Oc7CuRDyDIPezWwvT9kqaxc"
OAUTH_CLIENT_ID = "1063386643354112010"
AFTER_OAUTH_REDIRECT_URL = f"http://{HOST_IP}:{PORT}/oauth/callback" # if you change this, make sure to change it in the discord developer portal too
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={OAUTH_CLIENT_ID}&redirect_uri={parse.quote(AFTER_OAUTH_REDIRECT_URL)}&response_type=code&scope=identify%20guilds"

# Discord bot config

DISCORD_BOT_TOKEN = "OTkxNjM3NDgzMDA1Njg5ODY2.GJHMjd.dlkfPItAiVQmak4WcVZLQVT0r_G1qX91EWa598"

# Discord server config

DISCORD_SERVER_ID = 980516886536142958

# Discord allowed IDs config

DISCORD_ACCESS_ROLE_ID = 991358196142850089
DISCORD_PANEL_ADMINISTRATOR_ID = 980539098295058453
DISCORD_PANEL_FULL_ACCESS_USER_IDS = [690123872674119710]

# notification config

NOTIFICATION_ON_DENIED_ACCESS = False
NOTIFICATION_CHANNEL_ID = 6
NOTIFICATION_WEBHOOK_URL = ""
