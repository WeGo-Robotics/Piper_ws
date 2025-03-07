cmake_minimum_required(VERSION 3.22)
project(piper_moveit_config)

find_package(ament_cmake REQUIRED)

ament_package()

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# 올바른 파일명 사용
install(FILES launch/setup_assistant.launch.py DESTINATION share/${PROJECT_NAME}/launch)

