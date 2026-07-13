FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# Core dev tools + Edge Impulse Linux runtime dependencies.
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    python3-opencv \
    python3-numpy \
    portaudio19-dev \
    git \
 && rm -rf /var/lib/apt/lists/*

# Edge Impulse Linux Python SDK. The SDK imports pyaudio even for image models,
# so install both. The arm64 wheels run natively on the UNO Q (Cortex-A53).
RUN pip install --no-cache-dir --break-system-packages edge_impulse_linux pyaudio

# The base image already ran `rosdep init`.
RUN rosdep update

WORKDIR /braccio_ws

# edgeimpulse_ros is pulled from source; the Braccio packages are copied from
# this repo (build context = repo root).
RUN mkdir -p src && cd src && \
    git clone https://github.com/edgeimpulse/edgeimpulse-ros.git
COPY ros2_ws/src/ /braccio_ws/src/

# Resolve ROS deps (vision_msgs, diagnostic_msgs, ...); skip the pip-only keys
# that are already installed above.
RUN rosdep install --from-paths src --ignore-src -r -y \
    --skip-keys "edge_impulse_linux pyaudio"

# These packages are pure ament_python, so the build is light enough for the
# 4 GB UNO Q. Keep it sequential to stay well within RAM on smaller variants.
RUN . /opt/ros/$ROS_DISTRO/setup.sh && \
    colcon build --symlink-install \
    --executor sequential --parallel-workers 1

SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /braccio_ws/install/setup.bash" >> /root/.bashrc

# Model + workflow are provided by volume mounts (see docker-compose.yml).
ENV MODEL_PATH=/models/model.eim
ENV WORKFLOW_FILE=/config/pick_place_workflows.yaml

# On-device pick-and-place with edgeimpulse_ros. The UNO Q's own App Lab agents
# provide the camera (127.0.0.1:8080) and arm control (127.0.0.1:8765); host
# networking lets the container reach them and lets DDS discovery work.
CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && source /braccio_ws/install/setup.bash && ros2 launch unoq_braccio_bringup onboard_edge_impulse_pick_place.launch.py model_path:=$MODEL_PATH workflow_file:=$WORKFLOW_FILE"]
