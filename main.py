import obsws_python as obs
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import dropbox
from obsws_python.error import OBSSDKError, OBSSDKRequestError
import os


HOST = "localhost"
PORT = 4455
PASSWORD = os.getenv("obs_password")
APP_KEY = os.getenv("app_key")
APP_SECRET = os.getenv("app_secret")
REFRESH_TOKEN = os.getenv("refresh_token")


# Clients and Event Handlers
dbx = dropbox.Dropbox(app_secret=APP_SECRET, app_key=APP_KEY, oauth2_refresh_token=REFRESH_TOKEN)
client = obs.ReqClient(host=HOST, port=PORT, password=PASSWORD)
event_handler = obs.EventClient(host=HOST, port=PORT, password=PASSWORD)


app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
def main():
    pass


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0')