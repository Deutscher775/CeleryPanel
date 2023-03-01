import os
import flask
import conf
import zenora

try:
    oauth_client = zenora.APIClient(token=conf.OAUTH_TOKEN, client_secret=conf.OAUTH_CLIENT_SECRET)
except:
    print("Failed to connect to Discord API")

dash = flask.Flask("CeleryPanel", template_folder="./webpanel")
dash.config["SECRET_KEY"] = conf.SESSION_SECRET_KEY


@dash.route("/", methods=["POST", "GET"])
def route_index():
    try:
        if "oauth_access_token" in flask.session:
            oauth_bearer_client = zenora.APIClient(flask.session["oauth_access_token"], bearer=True)
            user = oauth_bearer_client.users.get_current_user().username
            return flask.render_template("index.html", user=user)
        else:
            return flask.redirect("/login")
    except zenora.exceptions.BadTokenError:
        flask.session["invalid access token"] = True
        return flask.redirect("/login")

@dash.route("/dev/webserver/shutdown")
def shutdown():
    os.abort()

@dash.route("/administrator")
def admin_panel():
    return flask.render_template("admin.html")

@dash.route("/administrator/log/login")
def show_login_log():
    return flask.render_template("log/login_log.html", logs=open("log/login_log.txt", "r").read())

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
                                         invalid_access_token="Your access token seems to be invalid")
        else:
            return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                         invalid_access_token="")
    except KeyError:
        flask.session["invalid access token"] = False
        return flask.render_template("login.html", oauth_url=conf.OAUTH_URL,
                                     invalid_access_token="Please login!")


@dash.route("/oauth/callback", methods=["POST", "GET"])
def login_callback():
    code = flask.request.args["code"]
    oauth_response = oauth_client.oauth.get_access_token(code, conf.AFTER_OAUTH_REDIRECT_URL)
    oauth_access_token = oauth_response.access_token
    flask.session["oauth_access_token"] = oauth_access_token
    flask.session["invalid access token"] = False
    return flask.redirect("/")


dash.run(host=conf.HOST_IP, port=conf.PORT, debug=conf.DEBUGGING)
