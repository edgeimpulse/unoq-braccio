# Edge Impulse Integration

Use Edge Impulse to turn classifier labels into Braccio poses.

Public project:

```text
https://studio.edgeimpulse.com/studio/1029890
```

Project: `Block Color Detection - braccio unoq`

Labels currently used by the public object detection project:

- `Blue Block`
- `Red Block`
- `Yellow Block`

Recommended flow:

1. Build and train an Edge Impulse project.
2. Export the model for the device that will run inference.
3. Publish the top label as a ROS 2 string on `/edge_impulse/label`.
4. Run `edge_impulse_mapper` with `label_to_pose.yaml`.

Example:

```bash
ros2 run unoq_braccio_driver edge_impulse_mapper \
  --ros-args -p mapping_file:=edge_impulse/label_to_pose.yaml
```

Publish a simulated label:

```bash
ros2 topic pub --once /edge_impulse/label std_msgs/msg/String "{data: wave}"
```

For recording Braccio command and robot-status data as CSV, see
[data_capture.md](data_capture.md).

## Camera Object Detection to Pick and Place

Use `edge_impulse_vision` when your USB camera is publishing ROS images and you
have an Edge Impulse object detection model exported as a Python/Linux runner.

The runner command receives a JPEG path as `{image}` and must print one JSON
object on stdout:

```json
{"label": "red_block", "confidence": 0.92, "bbox": {"x": 120, "y": 80, "width": 60, "height": 50}}
```

Start the UNO Q camera stream, hardware bridge, inference, and pick/place
executor:

```bash
source ros2_ws/install/setup.bash
ros2 launch unoq_braccio_bringup remote.launch.py host:=192.168.1.64 port:=8765
ros2 launch unoq_braccio_bringup edge_impulse_pick_place.launch.py \
  stream_url:=http://192.168.1.64:8080/stream \
  runner_command:="python3 edge_impulse/runner_template.py --image {image}" \
  workflow_file:=edge_impulse/pick_place_workflows.yaml
```

Replace `runner_template.py` with your Edge Impulse model runner when ready.
Edit `pick_place_workflows.yaml` so labels from your model match the item names
and drop locations you want.

For Linux `.eim` model testing, see [linux_setup.md](linux_setup.md).

## Alternative backend: `edgeimpulse_ros`

If you prefer the maintained [`edgeimpulse_ros`](https://github.com/edgeimpulse/edgeimpulse-ros)
package instead of the runner-command node, use
`edge_impulse_ros_pick_place.launch.py`. It runs the `edgeimpulse_ros` detector
on `/braccio/camera/image_raw` and a `detection_label_bridge` node that maps the
detector's `vision_msgs/Detection2DArray` output to the `/edge_impulse/label`
string the executor already consumes, so the pick/place workflow is unchanged.

Clone `edgeimpulse_ros` into the same workspace and build it, then:

```bash
source ros2_ws/install/setup.bash
ros2 launch unoq_braccio_bringup remote.launch.py host:=192.168.1.64 port:=8765
ros2 launch unoq_braccio_bringup edge_impulse_ros_pick_place.launch.py \
  stream_url:=http://192.168.1.64:8080/stream \
  model_path:=/absolute/path/to/model.eim \
  workflow_file:=edge_impulse/pick_place_workflows.yaml
```

The bridge picks the highest-scoring detection and publishes its class label
when the score clears `min_confidence` (default `0.65`). It reads detections
from `detections_topic` (default `/edgeimpulse_detector/detections`).

## Test on macOS with a ROS 2 container

You do not need a Linux machine to validate the build and the ROS 2 graph. On
macOS, run the workspace inside a `ros:jazzy` Docker container. On Apple Silicon
the image runs natively (arm64), so no emulation is required.

> **Note:** Docker Desktop on macOS cannot pass USB serial devices (`/dev/tty*`)
> into a container, so a directly wired arm is not reachable from the container.
> The Braccio path here is network-based (the UNO Q web endpoint on port `8765`
> and the camera stream on port `8080`), so a container reaches real hardware
> over your LAN through those URLs. For pure wiring tests, inject a synthetic
> detection as shown below.

Start a container with this repository and `edgeimpulse_ros` mounted into the
same workspace, building into `/tmp` so the host checkout stays clean:

```bash
docker run -it --name braccio-test \
  -v ~/git/ros2-docs-repos/unoq-braccio:/root/unoq-braccio \
  -v ~/git/ros2-docs-repos/edgeimpulse-ros:/root/unoq-braccio/ros2_ws/src/edgeimpulse_ros \
  -w /root/unoq-braccio/ros2_ws \
  ros:jazzy bash
```

Inside the container, install the dependencies and build:

```bash
apt update && apt install -y \
  ros-jazzy-vision-msgs ros-jazzy-diagnostic-msgs \
  python3-opencv python3-numpy portaudio19-dev python3-pip
pip install --break-system-packages edge_impulse_linux pyaudio requests

colcon build --symlink-install --build-base /tmp/build --install-base /tmp/install
source /tmp/install/setup.bash
```

Open more shells into the same container with `docker exec -it braccio-test bash`,
then `source /tmp/install/setup.bash` in each. To exercise `detection_label_bridge`
without any hardware, run the bridge in one shell:

```bash
ros2 run unoq_braccio_driver detection_label_bridge
```

Publish a synthetic detection in a second shell:

```bash
ros2 topic pub --once /edgeimpulse_detector/detections vision_msgs/msg/Detection2DArray \
  '{detections: [{results: [{hypothesis: {class_id: "red_block", score: 0.92}}], bbox: {center: {position: {x: 100.0, y: 80.0}}, size_x: 40.0, size_y: 40.0}}]}'
```

Confirm the outputs in a third shell:

```bash
ros2 topic echo /edge_impulse/label      # data: "red_block"
ros2 topic echo /edge_impulse/detection  # {"label":"red_block","confidence":0.92,"bbox":{...}}
```

Re-publish with `score: 0.4` to confirm the bridge stays silent below its
`min_confidence` (default `0.65`). To test the full chain, run
`pick_place_executor` with a `workflow_file` and watch `/braccio/joint_command`
while publishing labels.

## Run on the UNO Q itself (Docker)

You can also skip the external host/VM entirely and run the whole
`edgeimpulse_ros` pipeline in a Docker container **on the 4 GB UNO Q**. The
container runs the ROS 2 graph; the UNO Q's own App Lab agents keep providing
the camera MJPEG stream (`127.0.0.1:8080`) and arm control (`127.0.0.1:8765`).
The repo root ships a `Dockerfile` and `docker-compose.yml` for this.

Because the container uses `network_mode: host`, `localhost` reaches those
agents and DDS discovery works. This is what makes the on-device route simpler
than Docker Desktop on macOS, where host networking is unavailable.

1. Install Docker on the UNO Q's App Lab Linux OS (arm64).
2. **Start the App Lab agent that provides the camera and arm endpoints.** Run
   the `app_lab/braccio_web_agent` app on the UNO Q. It serves the camera MJPEG
   stream on `127.0.0.1:8080` and arm control on `127.0.0.1:8765`, which the
   container connects to. Verify both ports are published to the host:

   ```bash
   docker ps --format 'table {{.Names}}\t{{.Ports}}'   # expect 0.0.0.0:8080-> and 0.0.0.0:8765->
   ```

3. Copy your **aarch64** `.eim` model to `./models/model.eim` in the repo (see
   [models/README.md](../models/README.md)). Its labels must match the item
   names in [pick_place_workflows.yaml](pick_place_workflows.yaml).
4. Build and start (the arm64 `ros:jazzy` image runs natively):

   ```bash
   cd ~/unoq-braccio
   docker compose up -d --build
   docker compose logs -f ros2
   ```

The container's default command launches
`onboard_edge_impulse_pick_place.launch.py`, which starts the `tcp_bridge`
(`host:=127.0.0.1`), `mjpeg_camera_node`
(`stream_url:=http://127.0.0.1:8080/stream`), the `edgeimpulse_ros` detector,
`detection_label_bridge`, and `pick_place_executor` — the same
`/edge_impulse/label` contract and workflow YAML as every other backend.

### Runtime flags

Both are set in `docker-compose.yml` (or override inline, e.g.
`USE_CAMERA=false docker compose up -d`):

| Variable       | Default  | Effect                                                              |
| -------------- | -------- | ------------------------------------------------------------------ |
| `USE_HARDWARE` | `"true"` | Start `tcp_bridge` to the real arm. `false` = sim-only (no arm).   |
| `USE_CAMERA`   | `"true"` | Start camera + detector + pick-place. `false` = arm-only (no cam). |

With `USE_CAMERA=false` you get just the arm bridge — useful for driving the
Braccio directly without a camera or model. The `mjpeg_camera_node` also
retries rather than crashing if the stream is not up yet, so the container
stays running while you start the web agent.

> **Rebuild after code changes.** The ROS 2 source is copied into the image at
> build time, so after `git pull` you must run `docker compose up -d --build`.
> A plain `docker compose up -d` reuses the old image (symptom: a fixed error
> still appears in the logs).

The Braccio packages and `edgeimpulse_ros` are pure `ament_python`, so the
in-container `colcon build` is light. It is pinned to a sequential executor
(`--executor sequential --parallel-workers 1`) to stay within RAM on smaller
UNO Q variants; add swap if you hit memory pressure while building.
