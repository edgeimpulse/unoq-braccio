#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../ros2_ws"
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
