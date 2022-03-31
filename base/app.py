from flask import Flask
from flask_socketio import SocketIO, emit

from base.base_application import BaSeApplication

# pip install flask flask-socketio eventlet==0.30.2

# Run config:
# Script path: path/to/miniconda3/envs/<env-name>/bin/gunicorn
# Parameters: --workers 2 --bind 127.0.0.1:8000 -k eventlet app:app
# Working directory: /path/to/base-bcu/base


class FlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


app = FlaskApp(__name__)
app.config["SECRET_KEY"] = "secret!"

socketio = SocketIO(app)


base_application = BaSeApplication()


@socketio.on("my event")
def handle_my_custom_event(json):
    status = base_application.status
    print("received json: " + str(json))
    emit("my response", {"text": "Welcome!"})


@app.route("/")
def hello_world():
    return """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js" integrity="sha512-q/dWJ3kcmjBLU4Qc47E4A9kTB4m3wuTY7vkFJDTZKjTs8jhyGQnaUrxa0Ytd0ssMZhbNua9hE+E7Qv1j+DyZwA==" crossorigin="anonymous"></script>
    <script type="text/javascript" charset="utf-8">
        var socket = io();
        socket.on('connect', function() {
            socket.emit('my event', {data: 'Connected!'});
        });
        socket.on('my response', function(response) {
            console.log(response);
        });
    </script>
    Hello BaSe!
    """
