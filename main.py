import obsws_python as obs
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import dropbox
from obsws_python.error import OBSSDKError, OBSSDKRequestError
from dotenv import load_dotenv
import os

load_dotenv()

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


# OBS Event Handlers, These are used to update the client with the current live data
def on_current_program_scene_changed(data):
    scene = data.scene_name
    socketio.emit("scene_update", {
                    "message": scene
                })
    socketio.emit("notif", {
                    "message": f"Success: Scene changed to {scene}",
                    "status": "success"
                })

def on_record_state_changed(data):
    is_active = data.output_active

    # Uploads the recorded video to Dropbox after stopping the recording
    try:
        if data.output_state == "OBS_WEBSOCKET_OUTPUT_STOPPED":
            video_path = data.output_path
            dropbox_path = f"/Homily/{os.path.basename(video_path)}"

            chunk_size = 8 * 1024 * 1024
            file_size = os.path.getsize(video_path)

            # For Larger files, chunk the upload to avoid loading the whole file into memory
            with open(video_path, "rb") as f:
                if file_size <= chunk_size:
                    dbx.files_upload(
                                    f.read(),
                                    dropbox_path,
                                    mode=dropbox.files.WriteMode.overwrite
                                )
                    socketio.emit("notif", {
                        "message": f"Success: Video uploaded to Dropbox at {dropbox_path}",
                        "status": "success"
                    })
                else:
                    upload_session = dbx.files_upload_session_start(f.read(chunk_size))
                    cursor = dropbox.files.UploadSessionCursor(session_id=upload_session.session_id, offset=f.tell())
                    commit = dropbox.files.CommitInfo(path=dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= chunk_size:
                            dbx.files_upload_session_finish(f.read(chunk_size), cursor, commit)
                            break
                        else:
                            dbx.files_upload_session_append_v2(f.read(chunk_size), cursor)
                            cursor.offset = f.tell()
                    socketio.emit("notif", {
                                        "message": f"Success: Video uploaded to Dropbox at {dropbox_path}",
                                        "status": "success"
                                    })
    except Exception as e:
        socketio.emit("notif", {
            "message": f"Error: Failed to upload video to Dropbox. {str(e)}",
            "status": "error"
        })

    socketio.emit("obs_update", {
                "message": "REC..." if is_active else "STOPPED"
        })

event_handler.callback.register([
    on_current_program_scene_changed,
    on_record_state_changed,
])


@app.route("/")
def main():
    return render_template("index.html")


@socketio.on("connect")
def on_connect(auth=None):
    is_active = client.get_record_status().output_active

    # Update the client with the current recording status and scene name upon connection
    socketio.emit("obs_update", {
            "message": "REC..." if is_active else "STOPPED"
        })
    socketio.emit("scene_update", {
                    "message": client.get_current_program_scene().scene_name
                })

@app.route("/record", methods=["POST"])
def record():
    is_active = client.get_record_status().output_active
    socketio.emit("obs_update", {
        "message": "REC..." if not is_active else "STOPPED"
    })
    try:
        if  is_active:
            client.stop_record()
            return jsonify({"success": True})
        else:
            client.start_record()
            return jsonify({"success": True})
    except OBSSDKRequestError as e:
        socketio.emit("notif", {
            "message": f"Error: Failed to toggle recording. {str(e)}",
            "status": "error"
        })
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        socketio.emit("notif", {
            "message": f"Error: An unexpected error occurred. {str(e)}",
            "status": "error"
        })
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/change_scene", methods=["POST"])
def change_scene():
    try:
        client.set_current_program_scene("Scene 3") # Placeholder
        return jsonify({"success": True})
    except Exception as e:
        socketio.emit("notif", {
            "message": f"Error: Failed to change scene. {str(e)}",
            "status": "error"
        })
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0')