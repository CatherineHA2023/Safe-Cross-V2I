from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
                '/camera/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image',
                '/barricade/joint_angle@std_msgs/msg/Float64]ignition.msgs.Double',
                '/barrier_msg@std_msgs/msg/Bool]ignition.msgs.Boolean',
            ],
            output='screen',
        ),
        Node(
            package='v2i_vision_pkg',
            executable='yolo_detector_node',
            name='yolo_detector_node',
            output='screen',
        ),
        Node(
            package='v2i_vision_pkg',
            executable='barricade_control_node',
            name='barricade_control_node',
            output='screen',
        ),
        Node(
            package='v2i_vehicle_pkg',
            executable='v2i_soft_stop_node',
            name='v2i_soft_stop_node',
            output='screen',
        ),
    ])
