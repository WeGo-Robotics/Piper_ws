#!/usr/bin/env python3
# -*-coding:utf8-*-

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from piper_sdk import *
from piper_sdk import C_PiperInterface
from rclpy.qos import *
import time

class C_PiperRosNode(Node):
    def __init__(self) -> None:
        super().__init__('piper_single_states_node')

        # 파라미터 선언
        self.declare_parameter('can_port', 'can0')

        # 파라미터 값 가져오기
        self.can_port = self.get_parameter('can_port').get_parameter_value().string_value

        # QoS 설정
        qos_profile = QoSProfile(
            history=QoSHistoryPolicy.KEEP_ALL,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Publisher 생성
        self.joint_pub = self.create_publisher(JointState, 'joint_states_single', qos_profile)
        self.joint_states = JointState()
        self.joint_states.name = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7']
        self.joint_states.position = [0.0] * 7

        # Subscribing to joint control
        self.create_subscription(JointState, 'joint_ctrl_single', self.joint_state_callback, qos_profile)

        # Piper 인터페이스 초기화
        self.piper = C_PiperInterface(can_name=self.can_port)
        self.piper.ConnectPort()
        time.sleep(1)
        self.piper.EnableArm(7)

        # 타이머를 통한 주기적인 데이터 발행 (10Hz로 주기적 발행)
        self.create_timer(1 / 10, self.publish_joint_data)

    def publish_joint_data(self):
        """ 주기적으로 로봇 팔 상태를 퍼블리시 """
        self.PublishArmJointAndGripper()

    def joint_state_callback(self, msg: JointState):
        """ JointState 메시지를 받아 웨이포인트로 저장하고, 제어를 위한 함수 호출 """
        waypoints = [{'positions': msg.position[:7]}]  # 7개 조인트 저장
        self.execute_waypoints(waypoints)

    def execute_waypoints(self, waypoints):
        """ 저장된 웨이포인트들을 순차적으로 실행 """
        for waypoint in waypoints:
            self.move_to_waypoint(waypoint)

    def move_to_waypoint(self, waypoint):
        """ 주어진 웨이포인트로 이동 """
        factor = 57324.840764  # 1000*180/3.14
        positions = [round(pos * factor) for pos in waypoint['positions']]

        gripper = round(waypoint['positions'][6] * 1000 * 1000)
        gripper = min(max(gripper, 0), 70 * 1000)  # Gripper 범위 제한

        self.piper.MotionCtrl_2(0x01, 0x01, 100)
        self.piper.JointCtrl(*positions[:6])  # Gripper 제외
        self.piper.GripperCtrl(abs(gripper), 1000, 0x01, 0)

    def PublishArmJointAndGripper(self):
        """ 로봇 팔 상태 퍼블리시 """
        joint_data = self.piper.GetArmJointMsgs().joint_state
        gripper = self.piper.GetArmGripperMsgs().gripper_state.grippers_angle / 1000000

        self.joint_states.position = [
            joint_data.joint_1 / 1000 * 0.017444,
            joint_data.joint_2 / 1000 * 0.017444,
            joint_data.joint_3 / 1000 * 0.017444,
            joint_data.joint_4 / 1000 * 0.017444,
            joint_data.joint_5 / 1000 * 0.017444,
            joint_data.joint_6 / 1000 * 0.017444,
            gripper
        ]
        self.joint_pub.publish(self.joint_states)

def main(args=None):
    rclpy.init(args=args)
    piper_single_node = C_PiperRosNode()
    try:
        rclpy.spin(piper_single_node)
    except KeyboardInterrupt:
        pass
    finally:
        piper_single_node.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
