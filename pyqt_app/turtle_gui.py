import os
import sys
import threading

import pymysql
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from turtlesim.msg import Pose
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QApplication, QGridLayout, QLabel, QMessageBox,
                             QPushButton, QWidget)

DB_CONFIG = {
    'host': os.environ.get('ROS_DB_HOST', 'localhost'),
    'user': os.environ.get('ROS_DB_USER', 'rosuser'),
    'password': os.environ.get('ROS_DB_PASSWORD', 'rospass'),
    'database': 'rosdb',
    'charset': 'utf8mb4',
}


class GuiNode(Node):
    """PyQt 앱이 쓰는 ROS 노드: 명령 발행 + 거북이 위치 구독"""

    def __init__(self):
        super().__init__('turtle_gui_node')
        self.cmd_pub = self.create_publisher(String, '/turtle_command', 10)
        self.create_subscription(Pose, '/turtle1/pose', self.on_pose, 10)
        self.pose = None

    def on_pose(self, msg):
        self.pose = msg

    def send(self, cmd):
        self.cmd_pub.publish(String(data=cmd))


class TurtleWindow(QWidget):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.setWindowTitle('Turtle Control')

        layout = QGridLayout(self)

        self.pose_label = QLabel('위치: 수신 대기 중...')
        layout.addWidget(self.pose_label, 0, 0, 1, 3)

        # 방향키 버튼 4개
        self.btn_up = QPushButton('↑')
        self.btn_left = QPushButton('←')
        self.btn_down = QPushButton('↓')
        self.btn_right = QPushButton('→')
        layout.addWidget(self.btn_up, 1, 1)
        layout.addWidget(self.btn_left, 2, 0)
        layout.addWidget(self.btn_down, 2, 1)
        layout.addWidget(self.btn_right, 2, 2)

        # 리셋 버튼, 저장 버튼
        self.btn_reset = QPushButton('Reset')
        self.btn_save = QPushButton('위치 저장 (DB)')
        layout.addWidget(self.btn_reset, 3, 0, 1, 3)
        layout.addWidget(self.btn_save, 4, 0, 1, 3)

        self.btn_up.clicked.connect(lambda: self.node.send('up'))
        self.btn_down.clicked.connect(lambda: self.node.send('down'))
        self.btn_left.clicked.connect(lambda: self.node.send('left'))
        self.btn_right.clicked.connect(lambda: self.node.send('right'))
        self.btn_reset.clicked.connect(lambda: self.node.send('reset'))
        self.btn_save.clicked.connect(self.save_pose)

        # 0.2초마다 현재 위치 표시 갱신
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(200)

    def update_label(self):
        p = self.node.pose
        if p is not None:
            self.pose_label.setText(
                f'위치: x={p.x:.2f}, y={p.y:.2f}, theta={p.theta:.2f}')

    def save_pose(self):
        p = self.node.pose
        if p is None:
            QMessageBox.warning(self, '저장 실패',
                                '거북이 위치를 아직 받지 못했습니다.\nturtlesim_node가 실행 중인지 확인하세요.')
            return
        try:
            conn = pymysql.connect(**DB_CONFIG)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO turtlepos (x, y, theta) VALUES (%s, %s, %s)',
                        (p.x, p.y, p.theta))
                conn.commit()
            finally:
                conn.close()
            QMessageBox.information(
                self, '저장 완료',
                f'x={p.x:.2f}, y={p.y:.2f}, theta={p.theta:.2f} 저장했습니다.')
        except Exception as e:
            QMessageBox.critical(self, 'DB 오류', str(e))


def main():
    rclpy.init()
    node = GuiNode()
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    app = QApplication(sys.argv)
    win = TurtleWindow(node)
    win.show()
    code = app.exec_()

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
