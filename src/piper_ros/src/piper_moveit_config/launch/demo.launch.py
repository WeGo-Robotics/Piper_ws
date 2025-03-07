from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_demo_launch
from launch import LaunchDescription

def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("piper", package_name="piper_moveit_config").to_moveit_configs()
      
    return LaunchDescription([
        generate_demo_launch(moveit_config),  # MoveIt! 설정을 로드하는 데모 런치
    ])
