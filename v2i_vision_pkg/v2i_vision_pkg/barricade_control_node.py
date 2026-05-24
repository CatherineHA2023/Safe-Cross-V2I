import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float64
from gtts import gTTS
import pygame


class BarricadeControlNode(Node):
    def __init__(self):
        super().__init__('barricade_control_node')

        # 상태 변수
        self.vehicle_stopped = False    # 차량이 완전히 정지했는지 여부
        self.pedestrian_present = False # 보행자가 현재 감지되고 있는지 여부
        self.barricade_raised = False   # 차단바가 현재 올라가 있는지 여부

        # yolo_detector_node로부터 보행자 감지 상태 구독
        self.ped_sub = self.create_subscription(
            Bool,
            '/detection/pedestrian_detected',
            self.pedestrian_callback,
            10
        )

        # v2i_soft_stop_node로부터 차량 완전 정지 신호 구독
        self.vehicle_sub = self.create_subscription(
            Bool,
            '/v2i/vehicle_stopped',
            self.vehicle_stopped_callback,
            10
        )

        # 차단바 Joint 각도 제어 신호 발행 (가제보로 전달)
        # 0.0 = 내려감 (수평, 대기), 1.57 = 올라감 (90도, 보행자 통행 허용)
        self.joint_pub = self.create_publisher(Float64, '/barricade/joint_angle', 10)

        # 보행자에게 출발/정지 신호 발행 (ActorControlPlugin으로 전달)
        self.barrier_pub = self.create_publisher(Bool, '/barrier_msg', 10)

        # 차량에게 재출발 신호 발행 (v2i_soft_stop_node로 전달)
        # 보행자 횡단 완료 시 False를 보내 차량이 다시 출발하도록 함
        self.v2i_alert_pub = self.create_publisher(Bool, '/v2i_alert', 10)

        # 음성 안내 초기화
        # 노드 시작 시 한 번만 음성 파일 생성 → 재생 시 지연 없음
        self.audio_path = '/tmp/cross_signal.mp3'
        self._init_audio()

        self.get_logger().info('BarricadeControlNode 시작!')

        # 처음엔 차단바 내린 상태로 시작
        self.set_barricade(False)

    def _init_audio(self):
        """노드 시작 시 음성 파일 미리 생성 (gtts는 인터넷 필요)"""
        try:
            tts = gTTS(text='건너가세요', lang='ko')
            tts.save(self.audio_path)
            # pygame mixer는 화면 없이도 단독 초기화 가능
            pygame.mixer.init()
            self.audio_ready = True
            self.get_logger().info('음성 안내 준비 완료.')
        except Exception as e:
            self.audio_ready = False
            self.get_logger().warn(f'음성 안내 초기화 실패: {e}')

    def _play_audio(self):
        """백그라운드 스레드에서 음성 재생 (ROS2 루프를 막지 않기 위함)"""
        if not self.audio_ready:
            return
        try:
            pygame.mixer.music.load(self.audio_path)
            pygame.mixer.music.play()
            # 재생이 끝날 때까지 이 스레드에서만 대기
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            self.get_logger().warn(f'음성 재생 실패: {e}')

    def vehicle_stopped_callback(self, msg):
        """v2i_soft_stop_node로부터 차량 정지 상태 수신"""
        self.vehicle_stopped = msg.data
        if msg.data:
            self.get_logger().info('차량 완전 정지 확인!')
        # 차단바 올릴 조건 재확인
        self.check_and_open()

    def pedestrian_callback(self, msg):
        """yolo_detector_node로부터 보행자 감지 상태 수신"""
        prev_present = self.pedestrian_present
        self.pedestrian_present = msg.data

        if msg.data and not prev_present:
            self.get_logger().info('보행자 감지!')

        # 보행자가 있다가 사라졌을 때 → 횡단 완료 처리
        if not msg.data and prev_present and self.barricade_raised:
            self.get_logger().info('보행자 횡단 완료. 차단바 내리고 차량 출발 신호 전송.')

            # 차단바 내리기
            self.set_barricade(False)

            # 보행자에게 정지 신호 (더 이상 걷지 않아도 됨)
            barrier_msg = Bool()
            barrier_msg.data = False
            self.barrier_pub.publish(barrier_msg)

            # 차량에게 재출발 신호
            alert_msg = Bool()
            alert_msg.data = False
            self.v2i_alert_pub.publish(alert_msg)

            # 차량 정지 상태 초기화 (다음 보행자를 위해)
            self.vehicle_stopped = False

        # 차단바 올릴 조건 재확인
        self.check_and_open()

    def check_and_open(self):
        """차량 정지 + 보행자 존재 → 차단바 올리고 보행자 출발 안내"""
        if self.vehicle_stopped and self.pedestrian_present and not self.barricade_raised:
            self.get_logger().info('차량 정지 + 보행자 확인. 차단바 올리고 보행자 출발 신호 전송.')

            # 차단바 올리기
            self.set_barricade(True)

            # 보행자에게 출발 신호
            barrier_msg = Bool()
            barrier_msg.data = True
            self.barrier_pub.publish(barrier_msg)

            # "건너가세요" 음성 안내 (백그라운드 스레드에서 재생)
            threading.Thread(target=self._play_audio, daemon=True).start()

    def set_barricade(self, raise_bar):
        """차단바 Joint 각도 발행"""
        # raise_bar = True  → 1.57 (90도, 올라감) 보행자 통행 허용
        # raise_bar = False → 0.0 (0도, 내려감) 대기 상태
        angle_msg = Float64()
        angle_msg.data = 1.57 if raise_bar else 0.0
        self.joint_pub.publish(angle_msg)
        self.barricade_raised = raise_bar

        state = '올림 (보행자 통행 허용)' if raise_bar else '내림 (대기)'
        self.get_logger().info(f'차단바 {state}')


def main(args=None):
    rclpy.init(args=args)               # ROS2 초기화
    node = BarricadeControlNode()       # 노드 생성
    rclpy.spin(node)                    # 노드 계속 실행
    node.destroy_node()                 # 노드 종료
    rclpy.shutdown()                    # ROS2 종료


if __name__ == '__main__':
    main()
