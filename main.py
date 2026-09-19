import obsws_python as obs
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import dropbox
from obsws_python.error import OBSSDKError, OBSSDKRequestError
import os


HOST = "localhost"
PORT = 4455
PASSWORD = os.getenv("obs_password")
DBXPASSWORD = os.getenv("app_key")
app_key = os.getenv("app_secret")
app_secret = os.getenv("authorization_code")
authorization_code = os.getenv("refresh_token")
refresh_token = os.getenv("DBXPASSWORD")