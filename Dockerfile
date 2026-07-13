FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Core dev tools + audio dev headers. Keep this minimal: OpenCV/numpy come from
# pip below as the headless wheel. The apt `python3-opencv` package drags in
# ~900 MB of Qt/Mesa/X11 GUI dependencies that don't fit on the UNO Q's small
# eMMC and aren't needed on a headless device.
#
# build-essential + python3-dev + portaudio19-dev are required because pyaudio
# has no prebuilt arm64 wheel and is compiled from source against portaudio.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    python3-dev \
    build-essential \
    portaudio19-dev \
    git \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Edge Impulse Linux Python SDK + headless OpenCV (no GUI deps). The SDK imports
# pyaudio even for image models, so install it too. The arm64 wheels run
# natively on the UNO Q (Cortex-A53).
#
# Pin numpy<2 so pip is satisfied by the Debian-managed numpy 1.26 already in the
# ros:jazzy base image; it has no pip RECORD file, so letting pip try to replace
# it with numpy 2.x fails to uninstall.
RUN pip install --no-cache-dir --break-system-packages \
    edge_impulse_linux pyaudio opencv-python-headless "numpy<2"

# The base image already ran `rosdep init`.
RUN rosdep update

WORKDIR /braccio_ws

# edgeimpulse_ros is pulled from source; the Braccio packages are copied from
# this repo (build context = repo root).
RUN mkdir -p src && cd src && \
    git clone https://github.com/edgeimpulse/edgeimpulse-ros.git
COPY ros2_ws/src/ /braccio_ws/src/

# Resolve ROS deps for the inference route only. `apt-get update` is required
# because the earlier layer cleared the apt lists. Skip:
#   * pip-provided keys (opencv/numpy/EI SDK) so the GUI opencv chain isn't pulled
#   * the whole Gazebo / ros2_control simulation stack, which comes from
#     unoq_braccio_sim and is never used on-device. It is huge and won't fit the
#     UNO Q eMMC.
# unoq_braccio_sim is ignored below (not just skipped) so colcon drops it from
# the dependency graph entirely; bringup only needs it at runtime for the sim
# launch, which the inference container never uses.
RUN apt-get update && \
    rosdep install --from-paths src --ignore-src -r -y \
    --skip-keys "edge_impulse_linux pyaudio python3-opencv python3-numpy \
ros_gz_sim gz_ros2_control controller_manager joint_trajectory_controller \
joint_state_broadcaster joint_state_publisher xacro" \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Build only the inference-route packages; ignore the Gazebo sim package so
# colcon removes it from the graph (skip alone still expects its install).
RUN . /opt/ros/$ROS_DISTRO/setup.sh && \
    colcon build --symlink-install --packages-ignore unoq_braccio_sim \
    --executor sequential --parallel-workers 1

SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /braccio_ws/install/setup.bash" >> /root/.bashrc

# Model + workflow are provided by volume mounts (see docker-compose.yml).
ENV MODEL_PATH=/models/model.eim
ENV WORKFLOW_FILE=/config/pick_place_workflows.yaml
# Set USE_HARDWARE=false to skip the arm bridge and drive the sim container only.
ENV USE_HARDWARE=true
# Set USE_CAMERA=false to run arm-only (skips camera, detector and pick-place).
ENV USE_CAMERA=true

# On-device pick-and-place with edgeimpulse_ros. The UNO Q's own App Lab agents
# provide the camera (127.0.0.1:8080) and arm control (127.0.0.1:8765); host
# networking lets the container reach them and lets DDS discovery work.
CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && source /braccio_ws/install/setup.bash && ros2 launch unoq_braccio_bringup onboard_edge_impulse_pick_place.launch.py model_path:=$MODEL_PATH workflow_file:=$WORKFLOW_FILE use_hardware:=$USE_HARDWARE use_camera:=$USE_CAMERA"]
