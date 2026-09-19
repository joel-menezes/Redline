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
    return render_template("index.html")


@socketio.on("connect")
def on_connect():
    is_active = client.get_record_status().output_active

    # Update the client with the current recording status upon connection
    socketio.emit("obs_update", {
            "message": "REC..." if is_active else "STOPPED"
        })

    return render_template("index.html")

@app.route("/record", methods=["POST"])
def record():
    is_active = client.get_record_status().output_active
    socketio.emit("obs_update", {
        "message": "REC..." if not is_active else "STOPPED"
    })
    if  is_active:
        # Uploads the recorded video to Dropbox after stopping the recording
        response = client.stop_record()
        video_path = response.output_path
        dropbox_path = f"/Homily/{os.path.basename(video_path)}"

        with open(video_path, "rb") as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )

        return jsonify({"success": True})
    else:
        client.start_record()
        return jsonify({"success": True})


@app.route("/change_scene", methods=["POST"])
def change_scene():
    client.set_current_program_scene("Scene 3") # Placeholder
    return jsonify({"success": True})



if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0')