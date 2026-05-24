import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge
from ultralytics import YOLO


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')

        # YOLOv8 nano 모델 로드
        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()

        # 상태 변수
        self.alert_sent = False
        self.detect_count = 0    # 연속 감지 프레임 수
        self.no_detect_count = 0 # 연속 미감지 프레임 수
        self.CONFIRM_FRAMES = 5  # N프레임 연속 감지/미감지 시 확정

        # 가제보 카메라 이미지 구독
        # 영상이 들어올 때마다 image_callback 함수 자동 실행
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',    # 가제보 카메라 토픽
            self.image_callback,
            10                      # 큐 사이즈
        )

        # 차량에게 정지/출발 신호 발행 (v2i_soft_stop_node로 전달)
        self.v2i_alert_pub = self.create_publisher(Bool, '/v2i_alert', 10)

        # 차단기 노드에 보행자 존재 여부 실시간 전달
        # → 차단기 노드가 이 신호로 차단바 내릴 타이밍을 판단함
        self.pedestrian_pub = self.create_publisher(Bool, '/detection/pedestrian_detected', 10)

        self.get_logger().info('YoloDetectorNode 시작!')

    def image_callback(self, msg):
        # ROS 이미지 → OpenCV 변환
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # YOLOv8 추론
        results = self.model(frame, verbose=False, conf=0.1)

        person_in_frame = False
        for result in results:
            for box in result.boxes:
                if self.model.names[int(box.cls[0])] == 'person':
                    person_in_frame = True
                    break
            if person_in_frame:
                break

        # 연속 N프레임 확인 후 확정
        if person_in_frame:
            self.detect_count += 1
            self.no_detect_count = 0
        else:
            self.no_detect_count += 1
            self.detect_count = 0

        confirmed_present = self.detect_count >= self.CONFIRM_FRAMES
        confirmed_absent  = self.no_detect_count >= self.CONFIRM_FRAMES

        # 차단기 노드에 안정화된 상태 전달
        ped_msg = Bool()
        ped_msg.data = confirmed_present
        self.pedestrian_pub.publish(ped_msg)

        # 보행자 확정 감지 → 차량 정지 신호 1회
        if confirmed_present and not self.alert_sent:
            self.get_logger().info('보행자 감지! 차량 정지 신호 전송.')
            alert = Bool()
            alert.data = True
            self.v2i_alert_pub.publish(alert)
            self.alert_sent = True

        # 보행자 확정 사라짐 → 횡단 완료, 차량 출발 신호
        elif confirmed_absent and self.alert_sent:
            self.get_logger().info('보행자 통과 완료. 차량 출발 신호 전송.')
            alert = Bool()
            alert.data = False
            self.v2i_alert_pub.publish(alert)
            self.alert_sent = False


def main(args=None):
    rclpy.init(args=args)           # ROS2 초기화
    node = YoloDetectorNode()       # 노드 생성
    try:
        rclpy.spin(node)            # 노드 계속 실행
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()         # 노드 종료
        rclpy.shutdown()            # ROS2 종료


if __name__ == '__main__':
    main()
