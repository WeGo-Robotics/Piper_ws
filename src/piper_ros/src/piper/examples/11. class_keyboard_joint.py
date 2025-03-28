#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import termios
import tty
import select
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

msg = """
ROS2 Teleop Keyboard Controller
---------------------------
이동 옵션 (관절 각도 제어 [j1, j2, j3, j4, j5, j6]):
    Q - 관절 1 오른쪽으로 (j1+)
    A - 관절 1 왼쪽으로 (j1-)
    W - 관절 2 위로 (j2+)
    S - 관절 2 아래로 (j2-)
    E - 관절 3 아래로 (j3+)
    D - 관절 3 위로 (j3-)
    T - 관절 4 오른쪽으로 (j4+)
    G - 관절 4 왼쪽으로 (j4-)
    Y - 관절 5 아래로 (j5+)
    H - 관절 5 위로 (j5-)
    U - 관절 6 오른쪽으로 (j6+)
    J - 관절 6 왼쪽으로 (j6-)

그리퍼 제어:
    Space - 열기/닫기 토글

기타:
    Enter - 초기 자세로 이동
    Esc - 종료
"""


class WegoPublisher(Node):
    def __init__(self):
        super().__init__("wego_pub_keyboard_node")
        print(msg)
        self.settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())  # 원시 모드로 설정

        self.joint_pub = self.create_publisher(JointState, "joint_states", 10)
        self.init_pos_pub = self.create_publisher(Bool, "init_pos", 10)
        self.gripper_pub = self.create_publisher(Bool, "gripper_ctrl", 10)

        self.msg = JointState()
        self.msg.name = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]
        self.msg.position = [0.0] * 7  # 초기 각도 설정
        self.step = 0.1  # 이동 단위

        self.gripper_flag = True

    def get_key(self):
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)  # 0.1초 대기
        if rlist:
            return sys.stdin.read(1)
        return ""

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()
                if key:
                    sys.stdout.flush()
                    if key == "\x1b":  # ESC 키
                        print("\r종료 중...", flush=True)
                        break

                    elif key == "\r":
                        self.gripper_flag = not self.gripper_flag  # 그리퍼 상태 토글
                        print(f"\r그리퍼 상태: {'닫힘' if self.gripper_flag else '열림'}", flush=True)
                        self.gripper_pub.publish(Bool(data=self.gripper_flag))  # 그리퍼 상태 퍼블리시

                    elif key == " ":  # Space 키
                        print("\r초기 자세로 이동", flush=True)
                        self.init_pos_pub.publish(Bool(data=True))
                        self.msg.position = [0.0] * 7

                    elif key in "qawsedrftgyhuj":
                        direction = {
                            "q": (0, 1),
                            "a": (0, -1),
                            "w": (1, 1),
                            "s": (1, -1),
                            "e": (2, 1),
                            "d": (2, -1),
                            "r": (3, 1),
                            "f": (3, -1),
                            "t": (4, 1),
                            "g": (4, -1),
                            "y": (5, 1),
                            "h": (5, -1),
                        }
                        idx, sign = direction[key]
                        self.msg.position[idx] += sign * self.step
                        self.joint_pub.publish(self.msg)
                        print(f"\r{self.msg.name[idx]}: {self.msg.position[idx]:.2f}", flush=True)

                time.sleep(0.05)  # 0.1초 대기하여 입력을 안정적으로 받음
        except Exception as e:
            print(f"\r오류 발생: {e}", flush=True)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print("\r텔레오프 키보드 컨트롤러 종료", flush=True)
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)  # ROS 2 초기화
    node = WegoPublisher()  # 노드 생성
    node.run()  # run()을 호출하여 동작 시작
    node.destroy_node()  # 노드 종료
    rclpy.shutdown()  # ROS 2 종료


if __name__ == "__main__":
    main()
