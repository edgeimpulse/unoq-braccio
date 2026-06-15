from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    stream_url = LaunchConfiguration("stream_url")
    runner_command = LaunchConfiguration("runner_command")
    workflow_file = LaunchConfiguration("workflow_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument("stream_url", default_value="http://unoq.local:8080/stream"),
            DeclareLaunchArgument("runner_command", default_value=""),
            DeclareLaunchArgument(
                "workflow_file",
                default_value="edge_impulse/pick_place_workflows.yaml",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="mjpeg_camera_node",
                name="unoq_braccio_mjpeg_camera",
                parameters=[{"stream_url": stream_url}],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="edge_impulse_vision",
                name="unoq_braccio_edge_impulse_vision",
                parameters=[{"runner_command": runner_command}],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="pick_place_executor",
                name="unoq_braccio_pick_place_executor",
                parameters=[{"workflow_file": workflow_file}],
                output="screen",
            ),
        ]
    )
