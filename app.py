import logging

import requests
import werkzeug.exceptions
import requests.auth
import flask

import api


settings = api.config.Settings()
app = flask.Flask(__name__, static_folder="static", static_url_path="/")
app.config["GITHUB_CLIENT_ID"] = settings.github_client_id
app.config["GITHUB_CLIENT_SECRET"] = settings.github_client_secret.get_secret_value()
app.config["SECRET_KEY"] = settings.secret_key.get_secret_value()


@app.route("/")
def index():
    if "github_token" in flask.session:
        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": "token %s" % flask.session["github_token"],
                "Accept": "application/json",
            },
        )
        if not user_response.ok:
            if user_response.status_code == 401:
                flask.session.pop("github_token", None)
                return flask.redirect(flask.url_for("index"))
            return werkzeug.exceptions.InternalServerError(
                description="unable to get user info"
            )
        org_response = requests.get(
            "https://api.github.com/user/orgs",
            headers={
                "Authorization": "token %s" % flask.session["github_token"],
                "Accept": "application/json",
            },
        )
        if not org_response.ok:
            if org_response.status_code == 401:
                flask.session.pop("github_token", None)
                return flask.redirect(flask.url_for("index"))
            return werkzeug.exceptions.InternalServerError(
                description="unable to get org info"
            )

        user_response_json = user_response.json()
        org_response_json = org_response.json()

        user_login = user_response_json["login"]
        org_membership_ok = {}

        for org in org_response_json:
            org_login = org["login"]
            membership_response = requests.get(
                f"https://api.github.com/orgs/{org_login}/memberships/{user_login}",
                headers={
                    "Authorization": "token %s" % flask.session["github_token"],
                    "Accept": "application/json",
                },
            )
            org_membership_ok[org_login] = "unknown"
            if membership_response.status_code == 200:
                org_membership_ok[org_login] = "ok"
            if membership_response.status_code == 403:
                org_membership_ok[org_login] = "forbidden"
        return flask.render_template(
            "index.html",
            login=user_response_json["login"],
            orgs=org_response.json(),
            org_membership_ok=org_membership_ok,
        )
    else:
        return flask.render_template("index.html")


@app.route("/logout")
def logout():
    if "github_token" in flask.session:
        res = requests.delete(
            f"https://api.github.com/applications/{app.config['GITHUB_CLIENT_ID']}/grant",
            json={
                "access_token": flask.session["github_token"],
            },
            headers={"Accept": "application/vnd.github.v3+json"},
            auth=requests.auth.HTTPBasicAuth(
                app.config["GITHUB_CLIENT_ID"], app.config["GITHUB_CLIENT_SECRET"]
            ),
        )
        if not res.ok:
            logging.warning("could not revoke token at logout")
        flask.session.pop("github_token", None)
    return flask.redirect(flask.url_for("index"))


@app.route("/oauth")
def oauth():
    code = flask.request.args.get("code")
    if not code:
        return flask.redirect(
            "https://github.com/login/oauth/authorize?client_id=%s&scope=%s&access_type=offline"
            % (
                app.config["GITHUB_CLIENT_ID"],
                "read:org",
            )
        )
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": app.config["GITHUB_CLIENT_ID"],
            "client_secret": app.config["GITHUB_CLIENT_SECRET"],
            "code": code,
        },
        headers={"Accept": "application/json"},
    )
    if not token_response.ok:
        return werkzeug.exceptions.InternalServerError()
    if "error" in token_response.json():
        return werkzeug.exceptions.BadRequest()
    flask.session["github_token"] = token_response.json()["access_token"]
    return flask.redirect(flask.url_for("index"))
