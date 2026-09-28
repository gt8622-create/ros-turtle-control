import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from std_srvs.srv import Empty

# 명령 이름 -> (직진 속도, 회전 속도)
MOVES = {
    'up': (2.0, 0.0),
    'down': (-2.0, 0.0),
    'left': (0.0, 2.0),
    'right': (0.0, -2.0),
}


class TurtleBridge(Node):
    def __init__(self):
        super().__init__('turtle_bridge')
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.reset_client = self.create_client(Empty, '/reset')
        self.create_subscription(String, '/turtle_command', self.on_command, 10)
        self.get_logger().info('turtle_bridge 시작: /turtle_command 대기 중')

    def on_command(self, msg):
        cmd = msg.data
        if cmd in MOVES:
            twist = Twist()
            twist.linear.x, twist.angular.z = MOVES[cmd]
            self.cmd_pub.publish(twist)
            self.get_logger().info(f'이동: {cmd}')
        elif cmd == 'reset':
            if self.reset_client.service_is_ready():
                self.reset_client.call_async(Empty.Request())
                self.get_logger().info('거북이 리셋')
            else:
                self.get_logger().warn('/reset 서비스가 없습니다. turtlesim_node가 실행 중인가요?')
        else:
            self.get_logger().warn(f'알 수 없는 명령: {cmd}')


def main(args=None):
    rclpy.init(args=args)
    node = TurtleBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
