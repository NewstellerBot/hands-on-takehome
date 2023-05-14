from dotenv import load_dotenv
import threading
import os
import time

from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod

from flaskr import socketio
from flask_socketio import emit
from flask import current_app

# load the environment variables
load_dotenv()

CONNECTION_STRING = os.getenv("CONNECTION_STRING")
DEVICE_ID = os.getenv("DEVICE_ID")

registry_manager = None
thread = None


def send_update(method, payload):
    try:
        global registry_manager
        # build the method request
        device_method = CloudToDeviceMethod(method_name=method, payload=payload)
        # invoke the direct method on the device
        res = registry_manager.invoke_device_method(DEVICE_ID, device_method)
        # on success emit the response to the user
        if method == "temperature":
            print(res.payload.get("result"))
        emit(method, {"status": res.status, "payload": res.payload.get("result")})

    except Exception as ex:
        print("Unexpected error {0}".format(ex))
        emit(method, {"status": "500", "payload": "Internal Server Error"})


def telemetry():
    while True:
        try:
            # build the method request
            device_method = CloudToDeviceMethod(method_name="telemetry")
            # invoke the direct method on the device
            res = registry_manager.invoke_device_method(DEVICE_ID, device_method)
            # on success emit the response to the user
            socketio.emit(
                "telemetry",
                {"status": res.status, "payload": res.payload.get("result")},
            )

        except Exception as ex:
            print("Unexpected error {0}".format(ex))
            socketio.emit(
                "telemetry", {"status": "500", "payload": "Internal Server Error"}
            )

        time.sleep(1)


@socketio.on("connect")
def connect():
    print("Connected")
    # when connecting to the socket, create the registry manager
    global registry_manager
    # Create IoTHubRegistryManager
    registry_manager = IoTHubRegistryManager.from_connection_string(CONNECTION_STRING)
    socketio.emit("message", {"data": "Connected"})
    # start the telemetry thread
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=telemetry)


@socketio.on("speed")
def speed(req):
    send_update("speed", req.get("data"))


@socketio.on("direction")
def direction(req):
    send_update("direction", req.get("data"))


@socketio.on("temperature")
def temperature():
    send_update("temperature", "")
