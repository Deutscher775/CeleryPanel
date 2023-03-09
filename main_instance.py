import os
import sys
import time
import traceback

import flask
import conf
import zenora
import datetime
import json
import psutil
import pathlib
import subprocess

dash = flask.Flask("CeleryPanel", template_folder="./webpanel", static_folder="./webpanel")

try:
    oauth_client = zenora.APIClient(token=conf.OAUTH_TOKEN, client_secret=conf.OAUTH_CLIENT_SECRET)
except:
    print("Failed to connect to Discord API")
dash.config["SECRET_KEY"] = conf.SESSION_SECRET_KEY


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
        print(response)
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
        print(response)
        communicator_updated["com"][2]["action"]["response"] = None
        communicator_updated["com"][2]["action"]["action-request"] = False
        communicator_updated["com"][2]["action"]["action"] = None
        communicator_file_updated.seek(0)
        json.dump(communicator_updated, communicator_file_updated)
        communicator_file_updated.truncate()
        flask.session["bot_action_response"] = response
        return True


@dash.route("/", methods=["POST", "GET"])
def route_index():
    try:
        if flask.session["logout"] is True:
            flask.session["logout"] = False
            return flask.redirect("/login")
        elif "oauth_access_token" in flask.session:
            oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
            user = oauth_bearer_client.users.get_current_user().username
            return flask.render_template("index.html", user=user)
        else:
            return flask.redirect("/login")
    except zenora.exceptions.BadTokenError:
        flask.session["invalid access token"] = True
        return flask.redirect("/login")
    except KeyError:
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
    if "oauth_access_token" in flask.session:
        oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
        user_id = oauth_bearer_client.users.get_current_user().id
        if user_id in conf.DISCORD_PANEL_FULL_ACCESS_USER_IDS:
            return flask.render_template("admin.html")
        else:
            return "You do not have access to this panel"


@dash.route("/administrator/log/login")
def show_login_log():
    if "oauth_access_token" in flask.session:
        f = open("log/login_log.txt", "r").read()
        oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
        user_id = oauth_bearer_client.users.get_current_user().id
        if user_id in conf.DISCORD_PANEL_FULL_ACCESS_USER_IDS:
            return flask.render_template("log/login_log.html", logs=f)
        else:
            return "You do not have access to this panel"


@dash.route("/dev")
def development_panel():
    return flask.render_template("dev.html")


@dash.route("/dev/session/clear")
def clear_session():
    flask.session.clear()
    return flask.redirect("/")


@dash.route("/login", methods=["POST", "GET"])
async def login_request():
    try:
        if "oauth_access_token" is None:
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
    if check_if_access(user.id) is None:
        flask.session["login_site_notification"] = "An error occurred"
        return flask.redirect("/login")
    elif check_if_access(user.id):
        open("./log/login_log.txt", "a").write(f"[{datetime.datetime.now()}] {user.id} | {user.username} | Granted\n")
        flask.session["logout"] = False
        flask.session["login_site_notification"] = ""
        return flask.redirect("/")
    else:
        open("./log/login_log.txt", "a").write(f"[{datetime.datetime.now()}] {user.id} | {user.username} | Refused\n")
        flask.session["oauth_access_token"] = None
        flask.session["logout"] = False
        flask.session["login_site_notification"] = "You are not allowed to access this panel."
        return flask.redirect("/login")


@dash.route("/server", methods=["POST", "GET"])
async def server_stats():
    return flask.render_template("server_stats_front.html")


@dash.route("/server/stats/call", methods=["POST", "GET"])
async def server_stats_iframe():
    cores = f"Core count: {psutil.cpu_count(logical=False)}"
    cpu_usage = f"CPU usage: {psutil.cpu_percent()}%"
    ram_usage = f"RAM usage: {psutil.virtual_memory().percent}%"
    return flask.render_template("server_stats_iframe.html", cpu_cores=cores, cpu_use=cpu_usage, ram_use=ram_usage)


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
    try:
        bot_total_server = get_bot_stats("total server")
        bot_user_name = get_bot_stats("bot user name")
        return flask.render_template("bot.html", bot_total_servers=bot_total_server,
                                     bot_user_name=bot_user_name,
                                     action_log_response=flask.session["bot_action_response"])
    except KeyError:
        flask.session["bot_action_response"] = ""
        return flask.redirect("/bot")


@dash.route("/assets/logo", methods=["GET"])
async def get_logo():
    return flask.send_file("./webpanel/assets/CeleryPanel.png")


@dash.route("/bot/shutdown", methods=["POST", "GET"])
async def bot_shutdown():
    bot_action("shutdown")
    time.sleep(1)
    return flask.redirect("/bot")


@dash.route("/bot/start", methods=["POST", "GET"])
async def bot_start():
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
    if conf.OS == "windows":
        subprocess.Popen(f"py {pathlib.Path(__file__).parent.resolve()}/discord_worker.py")
        time.sleep(3)
        return flask.redirect("/bot")
    elif conf.OS == "linux":
        subprocess.Popen(f"python3 {pathlib.Path(__file__).parent.resolve()}/discord_worker.py")
        time.sleep(3)
        return flask.redirect("/bot")


@dash.route("/iframe/administrator/log/login")
async def render_iframe_login_log():
    return flask.render_template("admin.html", iframe_src=f"http://{conf.HOST_IP}/administrator/log/login")


@dash.route("/iframe/administrator/log/notification")
async def render_iframe_notif_log():
    return flask.render_template("admin.html", iframe_src=f"http://{conf.HOST_IP}/administrator/log/notification")


@dash.route("/iframe/server")
async def render_iframe_server():
    return flask.render_template("admin.html", iframe_src=f"http://{conf.HOST_IP}/server/stats/call")


@dash.route("/setup", methods=["POST", "GET"])
async def setup():
    try:
        msg = flask.session["setup-msg"]
        flask.session["setup-msg"] = ""
        return flask.render_template("setup.html", msg=msg)
    except KeyError:
        flask.session["setup-msg"] = ""
        return flask.render_template("setup.html", msg=flask.session["setup-msg"])


@dash.route("/setup/script/set", methods=["POST", "GET"])
async def setup_set():
    print(flask.request.form["command"])
    if not flask.request.form.get("script-file") and not flask.request.form.get("start-command"):
        flask.session["setup-msg"] = "You must set an option!"
        return flask.redirect("/setup")
    elif flask.request.form.get("script-file") and flask.request.form.get("start-command"):
        flask.session["setup-msg"] = "You cannot set both options!"
        return flask.redirect("/setup")
    elif flask.request.form.get("script-file"):
        if "setup-script-file" in flask.request.files:
            file = flask.request.files["setup-script-file"]
            if file.filename == "":
                flask.session["setup-msg"] = "Your file needs to have a valid name!"
                return flask.redirect("/setup")
            elif file.filename.lower()[:-3].endswith(".py"):
                try:
                    f = open("./data/setup-start.json", "x")
                    f_json = {
                        "start-file-set": True,
                        "start-file-path": None,
                        "start-command-set": False,
                        "start-command-command": None
                    }
                    json.dump(f_json, f)
                except:
                    traceback.print_exc()
                    f = open("./data/setup-start.json", "w")
                    f.truncate(0)
                    f_json = {
                        "start-file-set": True,
                        "start-file-path": None,
                        "start-command-set": False,
                        "start-command-command": None
                    }
                    json.dump(f_json, f)


        return flask.redirect("/setup")
    elif flask.request.form.get("start-command"):
        print(2)
        command = flask.request.form["command"]
        if command.lower().endswith(".py"):
            print(1)
            try:
                f = open("./data/setup-start.json", "x")
                f_json = {
                    "start-file-set": False,
                    "start-file-path": None,
                    "start-command-set": True,
                    "start-command-command": command
                }
                json.dump(f_json, f)
            except:
                traceback.print_exc()
                f = open("./data/setup-start.json", "w")
                f.truncate(0)
                f_json = {
                    "start-file-set": False,
                    "start-file-path": None,
                    "start-command-set": True,
                    "start-command-command": command
                }
                json.dump(f_json, f)
        return flask.redirect("/setup")


dash.run(host=conf.HOST_IP, port=conf.PORT, debug=conf.DEBUGGING)
