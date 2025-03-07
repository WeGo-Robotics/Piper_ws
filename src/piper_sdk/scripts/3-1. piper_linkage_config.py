#!/usr/bin/env python3
# -*-coding:utf8-*-

"""
해당 파일을 실행하기 전에 로봇팔을 안전한 위치로 이동시키고, Disable() 함수를 사용하여 PiPER를 비활성화해야 합니다.
Python SDK에서도 모드 전환이 가능하지만, 사용을 권장하지 않습니다.
"""

from typing import Optional
from piper_sdk import *
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
if __name__ == "__main__":
    piper = C_PiperInterface()
    piper.ConnectPort()  
    # piper.MasterSlaveConfig(0xFA, 0, 0, 0) # Mater
    piper.MasterSlaveConfig(0xFC, 0, 0, 0) # Slave
