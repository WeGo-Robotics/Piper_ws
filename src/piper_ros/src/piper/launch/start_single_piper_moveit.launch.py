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
    # piper_moveit_config_path = os.path.join(
    #     get_package_share_directory('piper_moveit_config'),
    #     'config',
    #     'moveit_rviz_config.rviz'
    # )
    # display_moveit_config = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(piper_moveit_config_path)
    # )

    # 런치 인자들
    can_port_arg = DeclareLaunchArgument(
        'can_port',
        default_value='can0',
        description='PiPER 노드에서 사용할 CAN 포트.'
    )

    # 노드 정의
    piper_states_node = Node(
        package='piper',
        executable='piper_single_states_node.py',
        output='screen',
        parameters=[
            {'can_port': LaunchConfiguration('can_port')}
        ]
    )

    piper_moveit_node = Node(
        package='piper',
        executable='piper_single_moveit_node.py'        
    )

    # LaunchDescription 반환
    return LaunchDescription([
        can_port_arg,
        display_moveit_launch,
        # display_moveit_config,        
        piper_states_node,
        piper_moveit_node
    ])