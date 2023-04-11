import os
import platform
import signal
import sys
import time
import traceback
import nextcord
import aiohttp
import flask
import requests
import conf
import zenora
import datetime
import json
import psutil
import pathlib
import subprocess

dash = flask.Flask("CeleryPanel", template_folder=f"{pathlib.Path(__file__).parent.resolve()}/webpanel",
                   static_folder=f"{pathlib.Path(__file__).parent.resolve()}/webpanel")

try:
    oauth_client = zenora.APIClient(token=conf.OAUTH_TOKEN, client_secret=conf.OAUTH_CLIENT_SECRET)
except:
    print("Failed to connect to Discord API")
dash.config["SECRET_KEY"] = conf.SESSION_SECRET_KEY


try:
    pid = os.getpid()
    global f
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/webpanel-data.json", "x")
    except FileExistsError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/webpanel-data.json", "w")
    finally:
        f.truncate(0)
        data = {"process-id": pid, "restart": False}
        json.dump(data, f)
        f.close()
except:
    traceback.print_exc()


def set_restart():
    global f
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/webpanel-data.json", "r+")
    except FileNotFoundError:
        print("The webpanel data file couldn't be found. Please restart the program manually.")
    finally:
        f_json = json.load(f)
        f.seek(0)
        f_json["restart"] = True
        json.dump(f_json, f)
        f.truncate()
        f.close()




def check_if_access(member_id):
    communicator_file = open("communicator.json", "r+")
    communicator = json.load(communicator_file)
    communicator["com"][0]["access"]["check"] = True
    communicator["com"][0]["access"]["id"] = member_id
    communicator_file.seek(0)
    json.dump(communicator, communicator_file)
    communicator_file.truncate()
    communicator_file.close()
    time.sleep(1)
    communicator_file_updated = open("communicator.json", "r+")
    communicator_updated = json.load(communicator_file_updated)
    if communicator_updated["com"][0]["access"]["is-response"] is True:
        response = communicator_updated["com"][0]["access"]["response"]
        communicator_updated["com"][0]["access"]["check"] = False
        communicator_updated["com"][0]["access"]["id"] = None
        communicator_updated["com"][0]["access"]["response"] = None
        communicator_updated["com"][0]["access"]["is-response"] = False
        communicator_file_updated.seek(0)
        json.dump(communicator_updated, communicator_file_updated)
        communicator_file_updated.truncate()
        return response


def get_bot_stats(info):
    communicator_file = open("communicator.json", "r+")
    communicator = json.load(communicator_file)
    communicator["com"][1]["getinfo"]["request"] = True
    communicator["com"][1]["getinfo"]["args"] = info
    communicator_file.seek(0)
    json.dump(communicator, communicator_file)
    communicator_file.truncate()
    communicator_file.close()
    time.sleep(1.2)
    communicator_file_updated = open("communicator.json", "r+")
    communicator_updated = json.load(communicator_file_updated)
    if communicator_updated["com"][1]["getinfo"]["response"] is not None:
        response = communicator_updated["com"][1]["getinfo"]["response"]
        communicator_updated["com"][1]["getinfo"]["response"] = None
        communicator_updated["com"][1]["getinfo"]["request"] = False
        communicator_updated["com"][1]["getinfo"]["args"] = None
        communicator_file_updated.seek(0)
        json.dump(communicator_updated, communicator_file_updated)
        communicator_file_updated.truncate()
        return response


def bot_action(action):
    flask.session["bot_action_response"] = ""
    communicator_file = open("communicator.json", "r+")
    communicator = json.load(communicator_file)
    communicator["com"][2]["action"]["action-request"] = True
    communicator["com"][2]["action"]["action"] = action
    communicator_file.seek(0)
    json.dump(communicator, communicator_file)
    communicator_file.truncate()
    communicator_file.close()
    time.sleep(1.2)
    communicator_file_updated = open("communicator.json", "r+")
    communicator_updated = json.load(communicator_file_updated)
    if communicator_updated["com"][2]["action"]["response"] is not None:
        response = communicator_updated["com"][2]["action"]["response"]
        communicator_updated["com"][2]["action"]["response"] = None
        communicator_updated["com"][2]["action"]["action-request"] = False
        communicator_updated["com"][2]["action"]["action"] = None
        communicator_file_updated.seek(0)
        json.dump(communicator_updated, communicator_file_updated)
        communicator_file_updated.truncate()
        flask.session["bot_action_response"] = response
        return True


def check_login():
    try:
        if flask.session["logout"] is True:
            flask.session["logout"] = False
            return False
        elif "oauth_access_token" in flask.session:
            return True
        else:
            return False
    except zenora.exceptions.BadTokenError:
        flask.session["invalid access token"] = True
        return False
    except KeyError:
        return False


@dash.route("/", methods=["POST", "GET"])
def route_index():
    if check_setup():
        return flask.redirect("/setup")
    try:
        open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "r")
    except FileNotFoundError:
        return flask.redirect("/setup")
    if check_login():
        oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
        user = oauth_bearer_client.users.get_current_user().username
        return flask.render_template("index.html", user=user)
    else:
        return flask.redirect("/login")


@dash.route("/user/logout")
def logout():
    flask.session["oauth_access_token"] = None
    flask.session["invalid access token"] = False
    flask.session["logout"] = True
    return flask.redirect("/")


@dash.route("/dev/webserver/shutdown")
def shutdown():
    os.abort()


@dash.route("/administrator")
def admin_panel():
    if check_login():
        if "oauth_access_token" in flask.session:
            oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
            user_id = oauth_bearer_client.users.get_current_user().id
            if user_id in conf.DISCORD_PANEL_FULL_ACCESS_USER_IDS:
                try:
                    iframe_src = flask.session["admin_if_src"]
                    return flask.render_template("admin.html",
                                                 iframe_src=f"http://{conf.HOST_IP}:{conf.PORT}{iframe_src}")
                except KeyError:
                    flask.session["admin_if_src"] = "/server/stats/call"
                    iframe_src = flask.session["admin_if_src"]
                    return flask.render_template("admin.html",
                                                 iframe_src=f"http://{conf.HOST_IP}:{conf.PORT}{iframe_src}")
            else:
                return "You do not have access to this panel"
    else:
        return flask.redirect("/login")


@dash.route("/administrator/log/login")
def show_login_log():
    if "oauth_access_token" in flask.session:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/log/login_log.txt", "r").read()
        oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
        user_id = oauth_bearer_client.users.get_current_user().id
        if user_id in conf.DISCORD_PANEL_FULL_ACCESS_USER_IDS:
            return flask.render_template("log/login_log.html", logs=f)
        else:
            return "You do not have access to this panel"


@dash.route("/dev")
def development_panel():
    if check_login():
        return flask.render_template("dev.html")
    else:
        return flask.redirect("/login")


@dash.route("/dev/session/clear")
def clear_session():
    if check_login():
        flask.session.clear()
        return flask.redirect("/")
    else:
        return flask.redirect("/login")


@dash.route("/login", methods=["POST", "GET"])
async def login_request():
    try:
        if not "oauth_access_token":
            return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                         notification="Please login.")

        elif flask.session["invalid access token"] is True:
            return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                         notification="Your access token seems to be invalid")
        else:
            return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                         notification=flask.session["login_site_notification"])
    except KeyError:
        flask.session["invalid access token"] = False
        return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                     notification="Login to continue!")


@dash.route("/oauth/callback", methods=["POST", "GET"])
async def login_callback():
    code = flask.request.args["code"]
    oauth_response = oauth_client.oauth.get_access_token(code, conf.AFTER_OAUTH_REDIRECT_URL)
    oauth_access_token = oauth_response.access_token
    flask.session["oauth_access_token"] = oauth_access_token
    flask.session["invalid access token"] = False
    oauth_bearer_client = zenora.APIClient(oauth_access_token, bearer=True)
    user = oauth_bearer_client.users.get_current_user()
    print(user.id)
    if check_if_access(user.id) is None:
        flask.session["login_site_notification"] = "An error occurred"
        if conf.NOTIFICATION_ON_ACCESS:
            session = aiohttp.ClientSession()
            webhook = nextcord.Webhook.from_url(url=conf.NOTIFICATION_WEBHOOK_URL, session=session)
            await webhook.send(f"<@{user.id}> tried to access the panel.\n**Access:** null (error)\n**Is bot:** {user.is_bot}",
                               avatar_url="https://raw.githubusercontent.com/Deutscher775/CeleryPanel/master/webpanel/assets/CeleryPanel.png", username="CelerPanel | Login")
            await session.close()
        return flask.redirect("/login")
    elif check_if_access(user.id):
        open(f"{pathlib.Path(__file__).parent.resolve()}/log/login_log.txt", "a").write(
            f"[{datetime.datetime.now()}] {user.id} | {user.username} | Granted\n")
        flask.session["logout"] = False
        flask.session["login_site_notification"] = ""
        if conf.NOTIFICATION_ON_ACCESS:
            session = aiohttp.ClientSession()
            webhook = nextcord.Webhook.from_url(url=conf.NOTIFICATION_WEBHOOK_URL, session=session)
            await webhook.send(f"<@{user.id}> tried to access the panel.\n**Access:** true (granted)\n**Is bot:** {user.is_bot}",
                               avatar_url="https://raw.githubusercontent.com/Deutscher775/CeleryPanel/master/webpanel/assets/CeleryPanel.png", username="CelerPanel | Login")
            await session.close()
        return flask.redirect("/")
    else:
        open(f"{pathlib.Path(__file__).parent.resolve()}/log/login_log.txt", "a").write(
            f"[{datetime.datetime.now()}] {user.id} | {user.username} | Refused\n")
        flask.session["oauth_access_token"] = None
        flask.session["logout"] = False
        flask.session["login_site_notification"] = "You are not allowed to access this panel."
        if conf.NOTIFICATION_ON_ACCESS:
            session = aiohttp.ClientSession()
            webhook = nextcord.Webhook.from_url(url=conf.NOTIFICATION_WEBHOOK_URL, session=session)
            await webhook.send(f"<@{user.id}> tried to access the panel.\n**Access:** false (denied)\n**Is bot:** {user.is_bot}",
                               avatar_url="https://raw.githubusercontent.com/Deutscher775/CeleryPanel/master/webpanel/assets/CeleryPanel.png", username="CelerPanel | Login")
            await session.close()
        return flask.redirect("/login")


@dash.route("/server/stats/call", methods=["POST", "GET"])
async def server_stats_iframe():
    if check_login():
        cores = f"Core count: {psutil.cpu_count(logical=False)}"
        cpu_usage = f"CPU usage: {psutil.cpu_percent()}%"
        ram_usage = f"RAM usage: {psutil.virtual_memory().percent}%"
        operating_system = f"Operating system: {platform.system()}"
        return flask.render_template("server_stats_iframe.html", cpu_cores=cores,
                                     cpu_use=cpu_usage, ram_use=ram_usage, os=operating_system)
    else:
        return flask.redirect("/login")


@dash.route("/administrator/log/login/clear", methods=["POST", "GET"])
async def clear_login_logs():
    if "oauth_access_token" in flask.session:
        f = open("log/login_log.txt", "r+")
        oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
        user_id = oauth_bearer_client.users.get_current_user().id
        if user_id in conf.DISCORD_PANEL_FULL_ACCESS_USER_IDS:
            f.truncate()
            return flask.redirect("/administrator/log/login")
        else:
            return "You do not have access to this panel"


@dash.route("/bot", methods=["POST", "GET"])
async def bot_home():
    if check_login():
        global is_running
        try:
            bot_total_server = get_bot_stats("total server")
            bot_user_name = get_bot_stats("bot user name")

            def check_run(pid):
                try:
                    os.kill(pid, 0)
                except OSError:
                    return False
                else:
                    return True

            try:
                f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "r")
                f_json = json.load(f)
                pid = f_json["process-id"]
                if check_run(pid) is True:
                    is_running = "Running"
                else:
                    is_running = "Not running"
            except FileNotFoundError:
                is_running = "Not running"
            finally:
                return flask.render_template("bot.html", bot_total_servers=bot_total_server,
                                             bot_user_name=bot_user_name, is_running=is_running,
                                             action_response=flask.session["bot_action_response"])
        except KeyError:
            flask.session["bot_action_response"] = ""
            return flask.redirect("/bot")
    else:
        return flask.redirect("/login")


@dash.route("/assets/logo", methods=["GET"])
async def get_logo():
    return flask.send_file(f"{pathlib.Path(__file__).parent.resolve()}/webpanel/assets/CeleryPanel.png")


@dash.route("/bot/shutdown", methods=["POST", "GET"])
async def bot_shutdown():
    if check_login():
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "r")
        f_json = json.load(f)
        pid = f_json["process-id"]
        psutil.Process(pid).kill()
        bot_action("shutdown")
        time.sleep(1)
        return flask.redirect("/bot")
    else:
        return flask.redirect("/login")


@dash.route("/log/server", methods=["POST", "GET"])
async def server_logs():
    if check_login():
        return flask.render_template("/log/server_log.html", s_logs=sys.stdout)
    else:
        return flask.redirect("/login")


@dash.route("/bot/start", methods=["POST", "GET"])
async def bot_start():
    if check_login():
        flask.session["bot_action_response"] = ""
        communicator_file = open("communicator.json", "r+")
        communicator = json.load(communicator_file)
        communicator["com"][2]["action"]["action-request"] = False
        communicator["com"][2]["action"]["action"] = None
        communicator["com"][2]["action"]["response"] = None
        communicator_file.seek(0)
        json.dump(communicator, communicator_file)
        communicator_file.truncate()
        communicator_file.close()
        start_command_file = open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json")
        start_command_json = json.load(start_command_file)
        if conf.OS == "windows":
            subprocess.Popen(f"py {pathlib.Path(__file__).parent.resolve()}/discord_worker.py")
            if start_command_json["start-command-set"] is True:
                try:
                    process = subprocess.Popen(f'py {start_command_json["start-command-command"]}')
                    try:
                        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "x")
                        data = {"process-id": process.pid}
                        json.dump(data, f)
                    except FileExistsError:
                        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "w")
                        f.truncate(0)
                        data = {"process-id": process.pid}
                        json.dump(data, f)
                except Exception as e:
                    flask.session["bot_action_response"] = str(e)
            else:
                flask.session["bot_action_response"] = "No discord bot start set."
            time.sleep(3)
            return flask.redirect("/bot")
        elif conf.OS == "linux":
            subprocess.Popen(["python3", f"{pathlib.Path(__file__).parent.resolve()}/discord_worker.py"])
            if start_command_json["start-command-set"] is True:
                try:
                    process = subprocess.Popen(["python3", f"{start_command_json['start-command-command']}"])
                    try:
                        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "x")
                        data = {"process-id": process.pid}
                        json.dump(data, f)
                    except FileExistsError:
                        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/discord-bot-process.json", "w")
                        f.truncate(0)
                        data = {"process-id": process.pid}
                        json.dump(data, f)
                except Exception as e:
                    flask.session["bot_action_response"] = str(e)
            else:
                flask.session["bot_action_response"] = "No discord bot start set."
            time.sleep(3)
            return flask.redirect("/bot")
    else:
        return flask.redirect("/login")


@dash.route("/iframe/administrator/log/login")
async def render_iframe_login_log():
    if check_login():
        flask.session["admin_if_src"] = "/administrator/log/login"
        return flask.redirect("/administrator")
    else:
        return flask.redirect("/login")


@dash.route("/iframe/administrator/log/notification")
async def render_iframe_notif_log():
    if check_login():
        flask.session["admin_if_src"] = "/log/notification"
        return flask.redirect("/administrator")
    else:
        return flask.redirect("/login")


@dash.route("/iframe/server")
async def render_iframe_server():
    if check_login():
        flask.session["admin_if_src"] = "/server/stats/call"
        return flask.redirect("/administrator")
    else:
        return flask.redirect("/login")


def check_setup():
    try:
        config = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r"))
    except FileNotFoundError:
        config = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "x"))
    try:
        script = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "r"))
    except FileNotFoundError:
        script = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "x"))
    if not config["port"]:
        return "port"
    elif not config["domain-name"] and not config["domain-name"] is False:
        return "domain-name"
    elif not config["domain-port"] and not config["domain-port"] is False:
        return "domain-port"
    elif not config["discord-oauth-secret"]:
        return "discord-oauth-secret"
    elif not config["discord-oauth-token"]:
        return "discord-oauth-token"
    elif not config["discord-oauth-id"]:
        return "discord-oauth-id"
    elif not config["discord-bot-token"]:
        return "discord-bot-token"
    elif not config["discord-server-id"]:
        return "discord-server-id"
    elif not config["discord-access-role-id"]:
        return "discord-access-role-id"
    elif not config["discord-administrator-id"]:
        return "discord-administrator-id"
    elif not config["discord-full-access-user-ids"]:
        return "discord-full-access-user-ids"
    elif not script["start-command-set"] is True:
        return "script"
    elif not config["discord-webhook-notification-on-access"]:
        return "discord-webhook-notification-on-access"
    elif not config["discord-webhook-url"] and config["discord-webhook-notification-on-access"] is True:
        return "discord-webhook-url"
    else:
        return False
@dash.route("/setup", methods=["GET"])
async def setup():
    try:
        if flask.session["RESTART"] is True:
            flask.session["RESTART"] = False
            config = json.load(open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json"))
            time.sleep(2)
            set_restart()
            return f"The webserver is restarting now due to changed configuration e.g. port or domain changes. It will be reachable here: <br>" \
                   f"<a href='http://{conf.HOST_IP}:{config['port']}'>http://{conf.HOST_IP}:{config['port']}</a>"
        else:
            pass
    except KeyError:
        flask.session["RESTART"] = False
    if not check_setup():
        return flask.redirect("/")
    else:
        try:
            msg = flask.session["setup-msg"]
            flask.session["setup-msg"] = ""
            return flask.render_template(f"setup/setup-{check_setup()}.html", msg=msg,
                                         action=f"/setup/{check_setup()}/set",
                                         name=check_setup())
        except KeyError:
            flask.session["setup-msg"] = ""
            return flask.render_template(f"setup/setup-{check_setup()}.html", msg=flask.session["setup-msg"],
                                         action=f"/setup/{check_setup()}/set",
                                         name=check_setup())


@dash.route(f"/setup/port/set", methods=["POST"])
async def setup_conf_set_port():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        flask.session["RESTART"] = True
        return flask.redirect("/setup")


@dash.route(f"/setup/domain-name/set", methods=["POST"])
async def setup_conf_set_domain_name():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        if not val:
            val = False
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        flask.session["RESTART"] = True
        return flask.redirect("/setup")


@dash.route(f"/setup/domain-port/set", methods=["POST"])
async def setup_conf_set_domain_port():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        if config["domain-name"] is False:
            config[check_setup()] = False
        else:
            val = flask.request.form[check_setup()]
            config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        flask.session["RESTART"] = True
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-oauth-secret/set", methods=["POST"])
async def setup_conf_set_oauth_secret():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-oauth-token/set", methods=["POST"])
async def setup_conf_set_oauth_token():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-oauth-id/set", methods=["POST"])
async def setup_conf_set_oauth_id():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-bot-token/set", methods=["POST"])
async def setup_conf_set_dc_bot():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-server-id/set", methods=["POST"])
async def setup_conf_set_dc_server():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-access-role-id/set", methods=["POST"])
async def setup_conf_set_dc_access():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-administrator-id/set", methods=["POST"])
async def setup_conf_set_dc_admin():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-full-access-ids/set", methods=["POST"])
async def setup_conf_set_dc_full_access():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val_raw = flask.request.form[check_setup()]
        val = val_raw.split(",")
        config[check_setup()] = int(val)
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route("/setup/script/set", methods=["POST"])
async def setup_script_set():
    command = flask.request.form["script"]
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "x")
        f_json = {
            "start-command-set": True,
            "start-command-command": command
        }
        json.dump(f_json, f)
    except FileExistsError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/data/setup-start.json", "w")
        f.truncate(0)
        f_json = {
            "start-command-set": True,
            "start-command-command": command
        }
        json.dump(f_json, f)
    return flask.redirect("/setup")


@dash.route(f"/setup/discord-webhook-notification-on-access/set", methods=["POST"])
async def setup_conf_set_dc_webhook_notify_on_acc():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val_raw = flask.request.form[check_setup()]
        if val_raw == "y":
            val = True
        elif val_raw == "n":
            val = False
        else:
            val = None
            flask.session["setup-msg"] = "Please enter 'y' or 'n'."
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")


@dash.route(f"/setup/discord-webhook-url/set", methods=["POST"])
async def setup_conf_set_dc_webhook_url():
    global f
    global config
    try:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    except FileNotFoundError:
        f = open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+")
        config = json.load(f)
    finally:
        val = flask.request.form[check_setup()]
        config[check_setup()] = val
        open(f"{pathlib.Path(__file__).parent.resolve()}/conf.json", "r+").seek(0)
        f.seek(0)
        json.dump(config, f)
        f.truncate()
        return flask.redirect("/setup")

@dash.route("/iframe/console")
async def render_iframe_console():
    if check_login():
        flask.session["admin_if_src"] = "/server/console"
        return flask.redirect("/administrator")
    else:
        return flask.redirect("/login")

@dash.route("/server/console")
def iframe_console():
    try:
        console = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "r")
    except FileNotFoundError:
        c = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "x")
        c.close()
        console = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "r")
    return flask.render_template("console.html", console=console.read())

@dash.route("/server/console/send", methods=["POST"])
def console_send():
    try:
        console = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "a")
    except FileNotFoundError:
        c = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "x")
        c.close()
        console = open(f"{pathlib.Path(__file__).parent.resolve()}/data/console.txt", "a")
    command = flask.request.form["command-send"]
    command_respone = os.popen(command).read()
    console.write(f"{command_respone}\n")
    return flask.redirect("/server/console")




dash.run(host=conf.HOST_IP, port=conf.PORT, debug=conf.DEBUGGING)
