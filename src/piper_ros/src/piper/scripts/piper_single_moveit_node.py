#!/usr/bin/env python3
# -*-coding:utf8-*-

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.action import ActionServer
from control_msgs.action import FollowJointTrajectory
from piper_sdk import *
from rclpy.qos import *
import asyncio

class JointTrajectoryModifier(Node):
    def __init__(self):
        super().__init__("piper_single_moveit_node")

        # ARM과 GRIPPER 액션 서버
        self.action_server_arm = ActionServer(
            self, FollowJointTrajectory, "/arm_controller/follow_joint_trajectory", self.execute_callback_arm
        )
        self.action_server_gripper = ActionServer(
            self, FollowJointTrajectory, "/gripper_controller/follow_joint_trajectory", self.execute_callback_gripper
        )

        # 최신 조인트 상태 저장용 변수
        self.current_joint_state = None  
        self.joint_names_full = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7', 'joint8']
        self.target_waypoint = None  # 목표 웨이포인트 추가

        # QoS 설정
        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_ALL,                  # 마지막 메시지만 유지, 큐에서 최대 메시지 수만 유지
            depth=100,                                            # 큐의 깊이: 메시지 버퍼 크기 (100개로 설정)
            reliability=ReliabilityPolicy.RELIABLE,              # 신뢰성 있는 메시지 전송
            durability=DurabilityPolicy.TRANSIENT_LOCAL,                 # 메시지를 수신 후 저장하지 않음 (실시간성 우선)
        )

        # 토픽 구독 (현재 조인트 상태)
        self.subscription = self.create_subscription(
            JointState, "/joint_states_single", self.joint_state_callback, qos_profile)

        # 퍼블리셔
        self.joint_ctrl_single_pub = self.create_publisher(JointState, 'joint_ctrl_single', qos_profile)

    def joint_state_callback(self, msg):
        """/joint_states_single에서 현재 조인트 상태 저장"""
        self.current_joint_state = msg

    async def execute_callback_arm(self, goal_handle):
        """팔(Arm) 조인트(1~6번)만 처리"""
        return await self.process_joint_trajectory(goal_handle)

    async def execute_callback_gripper(self, goal_handle):
        """그리퍼(Gripper) 조인트(7,8번)만 처리"""
        return await self.process_joint_trajectory(goal_handle)

    async def process_joint_trajectory(self, goal_handle):
        """공통 처리 함수, 조인트 업데이트"""
        self.get_logger().info("Processing joint trajectory...")

        if self.current_joint_state is None:
            self.get_logger().warn("No current joint state received yet. Skipping execution.")
            goal_handle.abort()
            return FollowJointTrajectory.Result()

        new_goal = FollowJointTrajectory.Goal()
        new_goal.trajectory = goal_handle.request.trajectory

        joint_names = new_goal.trajectory.joint_names  # 명령받은 조인트 이름

        for values in new_goal.trajectory.points:
            try:
                # 최신 조인트 상태 가져오기
                modified_positions = self.get_current_joint_state('position')
                # modified_velocities = self.get_current_joint_state('velocity')
                # modified_accelerations = self.get_current_joint_state('acceleration')
                
                # 새로 들어온 명령 적용
                updated_positions = self.update_joint_state(modified_positions, values.positions, joint_names)
                # updated_velocities = self.update_joint_state(modified_velocities, values.velocities, joint_names)
                # updated_accelerations = self.update_joint_state(modified_accelerations, values.accelerations, joint_names)

                # JointState 메시지 생성
                joint_state_msg = JointState()
                joint_state_msg.header.stamp = self.get_clock().now().to_msg()
                joint_state_msg.header.frame_id = "piper_single"
                joint_state_msg.name = self.joint_names_full  # 모든 조인트 이름 유지
                joint_state_msg.position = updated_positions
                # joint_state_msg.velocity = updated_velocities
                # joint_state_msg.effort = updated_accelerations 

                # 'joint_ctrl_single' 토픽으로 퍼블리시
                self.joint_ctrl_single_pub.publish(joint_state_msg)
                # self.get_logger().info(f"Published joint positions: {updated_positions}")
                # self.get_logger().info(f"Published joint velocities: {updated_velocities}")                
                # self.get_logger().info(f"Published joint accelerations: {updated_accelerations}")

                await asyncio.sleep(0)  # 이벤트 루프를 양보하여 빠른 처리 가능        

            except IndexError as e:
                self.get_logger().error(f"Invalid joint data received:  {values.positions} (Error: {e})")
                # self.get_logger().error(f"Invalid joint data received:  {values.velocities} (Error: {e})")
                # self.get_logger().error(f"Invalid joint data received:  {values.accelerations} (Error: {e})")

        # 액션 성공 처리
        goal_handle.succeed()
        return FollowJointTrajectory.Result()

    def get_current_joint_state(self, state_type):
        """현재 저장된 조인트 상태를 가져옴 (position, velocity, acceleration)"""
        if self.current_joint_state:
            joint_mapping = {name: idx for idx, name in enumerate(self.current_joint_state.name)}
            
            if state_type == 'position':
                return [self.current_joint_state.position[joint_mapping.get(name, -1)] if name in joint_mapping else 0.0
                        for name in self.joint_names_full]
        #     elif state_type == 'velocity':
        #         return [self.current_joint_state.velocity[joint_mapping.get(name, -1)] if name in joint_mapping else 0.0
        #                 for name in self.joint_names_full]
        #     elif state_type == 'acceleration':
        #         return [self.current_joint_state.effort[joint_mapping.get(name, -1)] if name in joint_mapping else 0.0
        #                 for name in self.joint_names_full]
        # return [0.0] * len(self.joint_names_full)  # 기본값

    def update_joint_state(self, current_values, new_values, joint_names):
        """현재 조인트 상태를 기반으로 새로운 값을 업데이트"""
        joint_mapping = {name: idx for idx, name in enumerate(joint_names)}

        for i, name in enumerate(self.joint_names_full):
            if name in joint_mapping:  # 새로운 값이 들어온 경우
                current_values[i] = new_values[joint_mapping[name]]

        # joint7 = |joint7| + |joint8|
        current_values[6] = abs(current_values[6]) + abs(current_values[7])
        return current_values

def main():
    rclpy.init()
    node = JointTrajectoryModifier()
    executor = rclpy.executors.MultiThreadedExecutor()  # 멀티스레딩 실행
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
