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

# webserver config

DEBUGGING = False
PORT = 80
SESSION_SECRET_KEY = "SOME_KEY"

# OAuth config

OAUTH_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
OAUTH_TOKEN = "YOUR_CLIENT_TOKEN"
OAUTH_CLIENT_ID = "YOUR_CLIENT_ID"
AFTER_OAUTH_REDIRECT_URL = f"http://{HOST_IP}/oauth/callback" # if you change this, make sure to change it in the discord developer portal too
OAUTH_URL = f"https://discord.com/api/oauth2/authorize?client_id={OAUTH_CLIENT_ID}&redirect_uri={parse.quote(AFTER_OAUTH_REDIRECT_URL)}&response_type=code&scope=identify%20guilds"

# Discord bot config

DISCORD_BOT_TOKEN = ""

# Discord server config

DISCORD_SERVER_ID = 1

# Discord allowed IDs config

DISCORD_ACCESS_ROLE_ID = 2
DISCORD_PANEL_ADMINISTRATOR_ID = 3
DISCORD_PANEL_FULL_ACCESS_USER_IDS = [4, 5]

# notification config

NOTIFICATION_ON_DENIED_ACCESS = True
NOTIFICATION_CHANNEL_ID = 6
NOTIFICATION_WEBHOOK_URL = ""
