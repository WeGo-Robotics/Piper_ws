#!/usr/bin/env python3

import sys
import termios
import tty
import select
import time
import rclpy
from rclpy.node import Node
from piper_msgs.msg import PosCmd
from std_msgs.msg import Bool

msg = """
ROS2 Teleop Keyboard Controller (Position Control)
---------------------------------------------------
이동 옵션 (XYZ 위치 조정 및 RPY 회전):
    Q - X 증가 (+)
    A - X 감소 (-)
    W - Y 증가 (+)
    S - Y 감소 (-)
    E - Z 증가 (+)
    D - Z 감소 (-)
    T - Roll 증가 (+)
    G - Roll 감소 (-)
    Y - Pitch 증가 (+)
    H - Pitch 감소 (-)
    U - Yaw 증가 (+)
    J - Yaw 감소 (-)

그리퍼 제어:
    Space - 열기/닫기 토글

기타:
    Enter - 초기 위치로 이동
    Esc - 종료
"""


class WegoPublisher(Node):
    def __init__(self):
        super().__init__("wego_pub_position_node")
        print(msg)
        self.settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        self.pub = self.create_publisher(PosCmd, "pos_cmd", 10)
        self.init_pos_pub = self.create_publisher(Bool, "init_pos", 10)
        self.gripper_pub = self.create_publisher(Bool, "gripper_ctrl", 10)

        self.msg = PosCmd()
        self.waypoint = [55.0, 0.0, 203.0, 0.0, 90.0, 0.0, 0.0]  # 초기 위치
        self.mode = [0x01, 0x00]  # 모드 설정 (고정값)

        self.step = 10.0  # 위치 이동 단위
        self.angle_step = 5.0  # 회전 각도 이동 단위
        self.gripper_flag = True  # 그리퍼 상태

    def get_key(self):
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if rlist:
            return sys.stdin.read(1)
        return ""

    def update_and_publish(self):
        combined = self.waypoint + self.mode
        self.msg.x, self.msg.y, self.msg.z = combined[0], combined[1], combined[2]
        self.msg.roll, self.msg.pitch, self.msg.yaw = combined[3], combined[4], combined[5]
        self.msg.gripper = combined[6]
        self.msg.mode1, self.msg.mode2 = combined[7], combined[8]

        self.pub.publish(self.msg)
        print(
            f"\r현재 위치: X={self.msg.x:.1f}, Y={self.msg.y:.1f}, Z={self.msg.z:.1f}, Roll={self.msg.roll:.1f}, Pitch={self.msg.pitch:.1f}, Yaw={self.msg.yaw:.1f}",
            flush=True,
        )

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()
                if key:
                    sys.stdout.flush()
                    if key == "\x1b":  # ESC 키 종료
                        print("\r종료 중...", flush=True)
                        break

                    elif key == "\r":  # Space 키 (그리퍼 열기/닫기)
                        self.gripper_flag = not self.gripper_flag
                        print(f"\r그리퍼 상태: {'열림' if self.gripper_flag else '닫힘'}", flush=True)
                        self.gripper_pub.publish(Bool(data=self.gripper_flag))

                    elif key == " ":  # Enter 키 (초기 위치 이동)
                        print("\r초기 위치로 이동", flush=True)
                        self.init_pos_pub.publish(Bool(data=True))
                        self.waypoint = [55.0, 0.0, 203.0, 0.0, 90.0, 0.0, 0.0]
                        self.update_and_publish()

                    elif key in "qawsedrftgyhuj":
                        direction = {
                            "q": (0, 1, self.step),
                            "a": (0, -1, self.step),  # X 이동
                            "w": (1, 1, self.step),
                            "s": (1, -1, self.step),  # Y 이동
                            "e": (2, 1, self.step),
                            "d": (2, -1, self.step),  # Z 이동
                            "r": (3, 1, self.angle_step),
                            "f": (3, -1, self.angle_step),  # Roll 회전
                            "t": (4, 1, self.angle_step),
                            "g": (4, -1, self.angle_step),  # Pitch 회전
                            "y": (5, 1, self.angle_step),
                            "h": (5, -1, self.angle_step),  # Yaw 회전
                        }
                        idx, sign, step = direction[key]
                        self.waypoint[idx] += sign * step
                        self.update_and_publish()

                time.sleep(0.05)

        except Exception as e:
            print(f"\r오류 발생: {e}", flush=True)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print("\r텔레오프 키보드 컨트롤러 종료", flush=True)
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WegoPublisher()
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
