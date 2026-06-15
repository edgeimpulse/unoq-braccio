from arduino.app_utils import App, Bridge
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
import socket
import threading
import time


CONTROL_PORT = 8765
CAMERA_PORT = 8080
CAMERA_INDEX = 0
START_TIME = time.monotonic()

frame_lock = threading.Lock()
latest_jpeg = None
move_count = 0
last_move_ms = 0
last_command_ms = 0
last_target = [90, 45, 180, 180, 90, 10]


def handle_arm_command(command):
    global move_count, last_move_ms, last_command_ms, last_target

    parts = command.strip().split()
    if len(parts) == 1 and parts[0] == "S":
        uptime_ms = int((time.monotonic() - START_TIME) * 1000)
        target = ",".join(str(value) for value in last_target)
        return (
            f"STAT uptime_ms={uptime_ms} move_count={move_count} "
            f"last_move_ms={last_move_ms} last_command_ms={last_command_ms} "
            f"target={target}"
        )

    if len(parts) != 7 or parts[0] != "M":
        return "ERR"

    try:
        values = [int(value) for value in parts[1:]]
    except ValueError:
        return "ERR"

    start = time.monotonic()
    result = Bridge.call("move_braccio", *values)
    last_move_ms = int((time.monotonic() - start) * 1000)
    last_command_ms = int((time.monotonic() - START_TIME) * 1000)
    move_count += 1
    last_target = values
    return "OK" if result is None or result is True else str(result)


def arm_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", CONTROL_PORT))
        server.listen(4)
        print(f"Braccio control listening on {CONTROL_PORT}")
        while True:
            client, address = server.accept()
            with client:
                data = client.recv(128).decode("ascii", errors="replace")
                response = handle_arm_command(data)
                client.sendall((response + "\n").encode("ascii"))
                print(f"{address[0]}: {data.strip()} -> {response}")


def camera_loop():
    global latest_jpeg
    capture = cv2.VideoCapture(CAMERA_INDEX)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(cv2.CAP_PROP_FPS, 15)

    while True:
        ok, frame = capture.read()
        if not ok:
            time.sleep(0.2)
            continue
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ok:
            with frame_lock:
                latest_jpeg = encoded.tobytes()
        time.sleep(0.02)


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/stream"):
            self.send_error(404)
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"UNO Q Braccio web agent. Use /stream\n")
            return

        self.send_response(200)
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()

        while True:
            with frame_lock:
                frame = latest_jpeg
            if frame is None:
                time.sleep(0.1)
                continue
            try:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n\r\n")
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
                time.sleep(0.07)
            except (BrokenPipeError, ConnectionResetError):
                break

    def log_message(self, format, *args):
        return


def camera_server():
    server = ThreadingHTTPServer(("0.0.0.0", CAMERA_PORT), StreamHandler)
    print(f"USB camera stream listening on {CAMERA_PORT}")
    server.serve_forever()


def loop():
    threading.Thread(target=arm_server, daemon=True).start()
    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=camera_server, daemon=True).start()
    while True:
        time.sleep(1)


App.run(user_loop=loop)
