from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    sim_launch = PathJoinSubstitution(
        [FindPackageShare("unoq_braccio_sim"), "launch", "gazebo.launch.py"]
    )
    return LaunchDescription([IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch))])
