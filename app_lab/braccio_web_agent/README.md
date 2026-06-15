# Braccio Web Agent

Run this single App Lab app on the UNO Q for the web dashboard.

It combines:

- TCP arm control on port `8765`
- USB camera MJPEG stream on port `8080`

Use this app instead of running `braccio_remote_agent` and
`usb_camera_streamer` separately.

Endpoints:

```text
tcp://<UNO_Q_IP_ADDRESS>:8765
http://<UNO_Q_IP_ADDRESS>:8080/stream
```

