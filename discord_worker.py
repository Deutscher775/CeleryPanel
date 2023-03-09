import asyncio
import json
import traceback

import nextcord
from nextcord.ext import commands
import conf
import sys

dc_client = commands.Bot(command_prefix="cp$", intents=nextcord.Intents.all())


@dc_client.event
async def on_ready():
    while True:
        communicator_file = open("communicator.json", "r+")
        communicator = json.load(communicator_file)
        if communicator["com"][0]["access"]["check"] is True:
            id = communicator["com"][0]["access"]["id"]
            response = check_if_access(id)
            communicator["com"][0]["access"]["check"] = False
            communicator["com"][0]["access"]["id"] = None
            communicator["com"][0]["access"]["response"] = response
            communicator["com"][0]["access"]["is-response"] = True
            communicator_file.seek(0)
            json.dump(communicator, communicator_file)
            communicator_file.truncate()
        if communicator["com"][1]["getinfo"]["request"] is True:
            args = communicator["com"][1]["getinfo"]["args"]
            response = get_info(args)
            communicator["com"][1]["getinfo"]["response"] = response
            communicator["com"][1]["getinfo"]["request"] = False
            communicator["com"][1]["getinfo"]["args"] = None
            communicator_file.seek(0)
            json.dump(communicator, communicator_file)
            communicator_file.truncate()
        if communicator["com"][2]["action"]["action-request"] is True:
            action = communicator["com"][2]["action"]["action"]
            response = await actions(action)
            communicator["com"][2]["action"]["response"] = response
            communicator["com"][2]["action"]["action-request"] = False
            communicator["com"][2]["action"]["action"] = None
            communicator_file.seek(0)
            json.dump(communicator, communicator_file)
            communicator_file.truncate()
        await asyncio.sleep(1)


def check_if_access(member_id):
    member = dc_client.get_user(member_id)
    server = dc_client.get_guild(conf.DISCORD_SERVER_ID)
    role = nextcord.utils.get(server.roles, id=conf.DISCORD_ACCESS_ROLE_ID)
    print(member)
    if member in role.members:
        return True
    else:
        return False

def get_info(args):
    if args == "total server":
        total_server = len(dc_client.guilds)
        print(total_server)
        return total_server
    elif args == "bot user name":
        username = dc_client.user.name
        print(username)
        return username


async def actions(action):
    print(action)
    if action == "shutdown":
        await dc_client.close()
        if dc_client.is_closed():
            return "Closed connection to Discord."
        else:
            return "Couldn't close connection to Discord."

if __name__ == "__main__":
    dc_client.run(conf.DISCORD_BOT_TOKEN)
