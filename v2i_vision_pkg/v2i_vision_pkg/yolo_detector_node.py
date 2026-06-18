import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge
from ultralytics import YOLO


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')

        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()

        self.alert_sent = False
        self.detect_count = 0
        self.no_detect_count = 0
        self.car_detect_count = 0
        self.CONFIRM_FRAMES = 3
        self.CONFIRM_ABSENT_FRAMES = 4
        self.stable_pedestrian = False
        self.stable_car = False
        self.car_stopped = False

        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)

        self.road_image_sub = self.create_subscription(
            Image, '/camera/road_raw', self.road_image_callback, 10)

        self.vehicle_stopped_sub = self.create_subscription(
            Bool, '/v2i/vehicle_stopped', self.vehicle_stopped_callback, 10)

        self.v2i_alert_pub = self.create_publisher(Bool, '/v2i_alert', 10)
        self.pedestrian_pub = self.create_publisher(Bool, '/detection/pedestrian_detected', 10)
        self.vehicle_pub = self.create_publisher(Bool, '/detection/vehicle_detected', 10)

        self.get_logger().info('YoloDetectorNode 시작!')

    def vehicle_stopped_callback(self, msg):
        self.car_stopped = msg.data
        if msg.data:
            self.no_detect_count = 0  # 차 정지 시 누적된 미감지 카운트 초기화 (오탐 방지)

    def image_callback(self, msg):
        """횡단보도 카메라 - 보행자 감지"""
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(frame, verbose=False, conf=0.5, classes=[0])  # person만

        person_in_frame = False
        for result in results:
            for box in result.boxes:
                cls_name = self.model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                if cls_name == 'person':
                    self.get_logger().info(
                        f'[crosswalk] {cls_name} conf={conf:.2f} box=({x1},{y1})-({x2},{y2})')
                    person_in_frame = True
                    break

        if person_in_frame:
            self.detect_count += 1
            self.no_detect_count = 0
        else:
            self.no_detect_count += 1
            self.detect_count = 0

        confirmed_present = self.detect_count >= self.CONFIRM_FRAMES
        confirmed_absent  = self.no_detect_count >= self.CONFIRM_ABSENT_FRAMES

        if confirmed_present:
            self.stable_pedestrian = True

        if confirmed_absent and not (self.alert_sent and not self.car_stopped):
            self.stable_pedestrian = False

        ped_msg = Bool()
        ped_msg.data = self.stable_pedestrian
        self.pedestrian_pub.publish(ped_msg)

        self._check_and_alert(confirmed_absent)

    def road_image_callback(self, msg):
        """도로 카메라 - 차량 감지"""
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(frame, verbose=False, conf=0.1, classes=[2, 3, 5, 7])  # car, motorcycle, bus, truck

        car_classes = {'car', 'truck', 'bus', 'motorcycle'}
        car_in_frame = False
        for result in results:
            for box in result.boxes:
                if self.model.names[int(box.cls[0])] in car_classes:
                    car_in_frame = True
                    break

        if car_in_frame:
            self.car_detect_count += 1
        else:
            self.car_detect_count = max(0, self.car_detect_count - 1)

        if self.car_detect_count >= 3:
            self.stable_car = True
        elif self.car_detect_count == 0:
            self.stable_car = False

        vehicle_msg = Bool()
        vehicle_msg.data = self.stable_car
        self.vehicle_pub.publish(vehicle_msg)

        self._check_and_alert(False)

    def _check_and_alert(self, confirmed_absent):
        if self.stable_pedestrian and self.stable_car and not self.alert_sent:
            self.get_logger().info('보행자 + 차량 감지! 차량 정지 신호 전송.')
            alert = Bool()
            alert.data = True
            self.v2i_alert_pub.publish(alert)
            self.alert_sent = True

        elif confirmed_absent and self.alert_sent and self.car_stopped:
            self.get_logger().info('보행자 사라짐 확인. 출발 신호는 barricade_control_node가 전송.')
            self.alert_sent = False
            self.stable_car = False
            self.car_detect_count = 0
            self.stable_pedestrian = False
            self.detect_count = 0
            self.car_stopped = False


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
