import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    gazebo_world_path = os.path.join(
        get_package_share_directory('piper_description'), 'worlds', 'empty.world')

    gazebo_options_dict = {
        'world': gazebo_world_path,
        'verbose': 'true'
    }

    gazebo_simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ]),
        launch_arguments=gazebo_options_dict.items()
    )

    piper_sim_options = {
        'start_x': '0.055',
        'start_y': '0',
        'start_z': '0.2',
        'start_roll': '0',
        'start_yaw': '0.85',
        'start_pitch': '0',        
        'pub_tf': 'true',
        'tf_freq': '100.0',
    }

    spawn_piper = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                         get_package_share_directory('piper_description'),
                         'launch', 'piper_spawn.launch.py')
        ]),
        launch_arguments=piper_sim_options.items()
    )

    return LaunchDescription([
        gazebo_simulator,
        spawn_piper
    ])
