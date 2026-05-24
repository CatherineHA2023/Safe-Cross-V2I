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

        # 3. 퍼블리셔: 차량 완전 정지 신호 → barricade_control_node로 전달
        # 속도가 0에 도달하면 True, 재출발 시 False 발행
        self.stopped_pub = self.create_publisher(Bool, '/v2i/vehicle_stopped', 10)

        # 4. 제어 루프 타이머 (10Hz = 0.1초 주기로 차량 제어)
        self.timer = self.create_timer(0.1, self.control_loop)

        # 5. 주행 프로파일 변수 세팅
        self.is_stopping = False
        self.current_speed = 0.0       # 처음엔 정지 상태
        self.target_speed = 15.0       # 목표 속도
        self.decel_step = 3.0         # 0.1초당 감소할 속도 변화량 (선형 감속)
        self.stop_triggered = False   # 감속 트리거 상태 플래그
        self.stopped_published = False  # 정지 신호를 이미 발행했는지 여부 (중복 발행 방지)
        self.startup_ticks = 0         # 시작 후 카운터 (50틱 = 5초 대기)

        self.get_logger().info("🚗 주행 제어 노드 시작: 5초 후 출발합니다.")

    def alert_callback(self, msg):
        """차단기 로봇의 신호 수신"""
        if self.startup_ticks < 50:  # 출발 전이면 무시
            return
        if msg.data == True and not self.is_stopping:
            self.get_logger().info("🛑 [안전 통제] v2i 정지 메세지 수신. Soft Stop을 시작합니다.")
            self.is_stopping = True

        elif msg.data == False and self.is_stopping:
            self.get_logger().info("🟢 [통제 해제] 어린이(보행자) 횡단 완료. 주행을 재개합니다.")
            self.is_stopping = False
            # 다시 목표 속도로 엑셀을 밟기 위한 초기화
            self.target_speed = 15.0
            self.stopped_published = False  # 다음 정지 시 다시 신호 보낼 수 있도록 초기화

            # 차량이 다시 움직임 → barricade_control_node에 알림
            stopped_msg = Bool()
            stopped_msg.data = False
            self.stopped_pub.publish(stopped_msg)

    def control_loop(self):
        """0.1초마다 자동차 속도 제어"""
        twist = Twist()

        # 시작 후 5초 대기 (50틱)
        if self.startup_ticks < 50:
            self.startup_ticks += 1
            if self.startup_ticks == 50:
                self.get_logger().info("🚗 출발!")
            twist.linear.y = 0.0
            self.cmd_pub.publish(twist)
            return

        if self.is_stopping:
            # 브레이크 밟기 (속도를 서서히 0으로)
            if self.current_speed > 0.0:
                self.current_speed -= self.decel_step
            if self.current_speed < 0.0:
                self.current_speed = 0.0

            # 완전 정지 도달 시 barricade_control_node로 신호 1회 발행
            if self.current_speed <= 0.0 and not self.stopped_published:
                self.get_logger().info("🔴 차량 완전 정지. 차단기 노드에 정지 신호 전송.")
                stopped_msg = Bool()
                stopped_msg.data = True
                self.stopped_pub.publish(stopped_msg)
                self.stopped_published = True
        else:
            # 엑셀 밟기 (출발 신호를 받으면 서서히 목표 속도까지 가속)
            if self.current_speed < self.target_speed:
                self.current_speed += 0.5 # 0.1초당 가속
        
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