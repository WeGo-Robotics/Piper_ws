from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription  
from launch_ros.actions import Node  
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    piper_moveit_launch_path = os.path.join(
        get_package_share_directory('piper_moveit_config'),
        'launch',
        'demo.launch.py'
    )

    display_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(piper_moveit_launch_path)
    )

    # 노드 정의
    piper_states_node = Node(
        package='piper',
        executable='piper_multi_ctrl_node.py',
        output='screen',
    )

    piper_moveit_node = Node(
        package='piper',
        executable='piper_single_moveit_node.py'        
    )

    # LaunchDescription 반환
    return LaunchDescription([
        display_moveit_launch,    
        piper_states_node,
        piper_moveit_node
    ])
