import os
import flask
import conf
import zenora
import datetime

try:
    oauth_client = zenora.APIClient(token=conf.OAUTH_TOKEN, client_secret=conf.OAUTH_CLIENT_SECRET)
except:
    print("Failed to connect to Discord API")

dash = flask.Flask("CeleryPanel", template_folder="./webpanel")
dash.config["SECRET_KEY"] = conf.SESSION_SECRET_KEY


def check_if_access():
    oauth_access_token = flask.session["oauth_access_token"]
    discord_server_client = zenora.APIClient(oauth_access_token, bearer=True)
    guilds = discord_server_client.users.get_my_guilds()
    user_roles = discord_server_client.users



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
def login_request():
    try:
        if flask.session["invalid access token"] is True:
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
def login_callback():
    code = flask.request.args["code"]
    oauth_response = oauth_client.oauth.get_access_token(code, conf.AFTER_OAUTH_REDIRECT_URL)
    oauth_access_token = oauth_response.access_token
    flask.session["oauth_access_token"] = oauth_access_token
    flask.session["invalid access token"] = False
    oauth_bearer_client = zenora.APIClient(oauth_access_token, bearer=True)
    user = oauth_bearer_client.users.get_current_user()
    open("./log/login_log.txt", "a").write(f"[{datetime.datetime.now()}] {user.id} | {user.username}\n")
    flask.session["logout"] = False
    return flask.redirect("/")


dash.run(host=conf.HOST_IP, port=conf.PORT, debug=conf.DEBUGGING)
