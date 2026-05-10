import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

class V2ISoftStopController(Node):
    def __init__(self):
        super().__init__('v2i_soft_stop_controller')

        # 1. 퍼블리셔: 가제보의 프리우스 자동차로 속도 명령 전달
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # 2. 서브스크라이버: V2I 신호(보행자 감지 알림) 수신
        # 알림용 토픽 이름은 '/v2i_alert'로 가정 (True가 들어오면 제동 시작)
        self.v2i_sub = self.create_subscription(Bool, '/v2i_alert', self.alert_callback, 10)

        # 3. 제어 루프 타이머 (10Hz = 0.1초 주기로 차량 제어)
        self.timer = self.create_timer(0.1, self.control_loop)

        # 4. 주행 프로파일 변수 세팅
        self.is_stopping = False
        self.current_speed = 8.0      # 초기 정속 주행 속도 (m/s)
        self.target_speed = 8.0       # 이 줄을 꼭 추가해야 에러가 안 납니다.
        self.decel_step = 0.4        # 0.1초당 감소할 속도 변화량 (선형 감속)
        self.stop_triggered = False   # 감속 트리거 상태 플래그

        self.get_logger().info("🚗 주행 제어 노드 시작: 도로를 정속 주행합니다.")

    def alert_callback(self, msg):
        """차단기 로봇의 신호 수신"""
        if msg.data == True and not self.is_stopping:
            self.get_logger().info("🛑 [안전 통제] v2i 정지 메세지 수신. Soft Stop을 시작합니다.")
            self.is_stopping = True
            
        elif msg.data == False and self.is_stopping:
            self.get_logger().info("🟢 [통제 해제] 어린이(보행자) 횡단 완료. 주행을 재개합니다.")
            self.is_stopping = False
            # 다시 목표 속도로 엑셀을 밟기 위한 초기화
            self.target_speed = 8.0 

    def control_loop(self):
        """0.1초마다 자동차 속도 제어"""
        twist = Twist()

        if self.is_stopping:
            # 브레이크 밟기 (속도를 서서히 0으로)
            if self.current_speed > 0.0:
                self.current_speed -= self.decel_step
            if self.current_speed < 0.0:
                self.current_speed = 0.0
        else:
            # 엑셀 밟기 (출발 신호를 받으면 서서히 목표 속도까지 가속)
            if self.current_speed < self.target_speed:
                self.current_speed += 0.2 # 0.1초당 부드럽게 가속
        
        # 프리우스 모델의 축 틀어짐을 보정
        twist.linear.x = 0.0
        twist.linear.y = -self.current_speed
        twist.linear.z = 0.0
 
        # 조향 0 → 직진 유지
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = 0.0

        # 가제보로 명령 전송
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = V2ISoftStopController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("주행 제어를 종료합니다.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()