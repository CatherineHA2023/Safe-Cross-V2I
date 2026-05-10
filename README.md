# Safe-Cross-V2I 🤖🚗

## 1. 주제
Safe-Cross: 비전 AI 기반 스마트 횡단보도 로봇과 자율주행 차량의 Vehicle-to-Infrastructure(V2I) 협력 제어 시스템

## 2. 목표
매년 스쿨존 및 아파트 단지 내 교차로에서 발생하는 어린이 등하굣길 교통사고는 심각한 사회적 문제로 대두되고 있습니다. 특히, 현재의 자율주행 차량은 자체 탑재된 센서에 전적으로 의존하므로, 체구가 작은 어린이가 물리적 사각지대에서 갑자기 나타나는 돌발 상황에 대처하기 매우 어렵습니다. 이에 본 프로젝트는 횡단보도 인프라(스마트 차단기 로봇)와 모빌리티(자율주행 차량)가 실시간으로 데이터를 교환하며 위험을 사전에 차단하는 V2I(Vehicle-to-Infrastructure) Multi-Agent 협력 시스템을 구축합니다. 이를 통해 센서의 한계를 극복하고 어린이들의 안전한 등굣길을 보장하는 스마트 시티 교통망의 축소판을 구현하는 것을 목표로 합니다.

## 3. 진행 방법
Safe-Cross는 ROS2 및 Gazebo Fortress 시뮬레이션 환경에서 다음 5단계의 파이프라인으로 동작합니다.

1. 시뮬레이션 환경 구축: Gazebo Fortress를 이용해 실제 등굣길과 유사한 가상 환경을 설계합니다. 환경은 크게 도로 인프라, 동적 에이전트, 배경 요소로 구성됩니다.
* Gazebo의 기본 도형 모델을 이용해 아스팔트 도로와 횡단보도 배치.
* 스마트 차단기 로봇 1: 횡단보도 입구에 고정된 형태로 배치되며, 기둥(Link)과 차단바(Joint)를 1자유도 회전 관절로 연결하여 모델링. 카메라 센서 플러그인을 부착하여 시야 확보.
* 자율주행 차량 1: 차동 구동형 모터 제어 플러그인이 적용된 차량 모델을 배치하여, ROS2를 통해 물리적인 주행과 정지가 가능하도록 구성.
* 보행자(어린이) 1: 횡단보도 대기 구역에 배치.
* 간단한 환경 렌더링: Gazebo Fuel의 오픈소스 3D 에셋(스쿨존 표지판, 안전 펜스, 주변 건물 등)을 활용하여 시뮬레이션의 시각적 현실감을 극대화.

2. 인프라의 선제적 인지: 스마트 차단기 로봇이 물리적인 차단바(Joint)를 내린 채로 대기 중에 보행자(어린이)가 횡단보도에 접근하면, 탑재된 카메라 영상과 YOLO v8 모델을 통해 객체(person, car)를 실시간으로 인식합니다. 

3. V2I 통신: 보행자(어린이) 인지와 동시에, 스마트 차단기 로봇은 ROS2 DDS 통신망을 통해 주변 차량에 긴급 감속을 요청하는 경고 메시지를 즉각적으로 전송합니다.

4. 자율주행 차량의 협력 제어: 일정한 초기 속도(v)로 주행 중인 자율주행 자동차는 자체 비전 센서의 보행자 식별 여부와 무관하게, 수신된 V2I 경고 메시지를 최우선 제어 명령으로 처리합니다. 메시지 수신 즉시 속도를 일정한 변화량(예: 0.2 m/s)만큼 선형적으로 감소시키는 Soft Stop Linear Deceleration Profile을 적용하여, 횡단보도 앞에 부드럽게 정차합니다.
   
5. 안전 안내 및 상황 해제: 자율주행 차량의 완전 정차가 확인되면, 스마트 차단기 로봇이 차단바(Joint)를 올리고 보행자(어린이)에게 횡단 안내를 제공합니다. 횡단이 완료되면 V2I 경고 상태를 해제하고 차단바(Joint)를 다시 내려, 전체 교통 흐름을 정상적으로 재개합니다.

## 주요 파일 설명
가제보 시뮬레이션 환경 구축 파일: v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_pkg/worlds/school_zone.sdf

자율주행 자동차 주행 및 제어 (감속, 다시 시작 등) 파일: v2i_ws/src/Safe-Cross-V2I/v2i_vehicle_pkg/v2i_vehicle_pkg/v2i_soft_stop_node.py

보행자 (actor) 애니메이션 및 제어 파일: v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_plugins/ActorControlPlugin.cc 
👉🏻 C++ 플러그인 빌드 필요
$ cd ~/v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_plugins
$ mkdir build
$ cd build
$ cmake ..
$ make

## 실행
✅터미널 1: 가제보 실행 
$ export IGN_GAZEBO_RESOURCE_PATH=~/v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_pkg/models:$IGN_GAZEBO_RESOURCE_PATH

$ export IGN_GAZEBO_SYSTEM_PLUGIN_PATH=$IGN_GAZEBO_SYSTEM_PLUGIN_PATH:~/v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_plugins/build

$ QT_QPA_PLATFORM=xcb ign gazebo -v 4 --render-engine ogre ~/v2i_ws/src/Safe-Cross-V2I/v2i_gazebo_pkg/worlds/school_zone.sdf

→ 재생 버튼 클릭

✅터미널 2: 가제보 - ros 브릿지
$ ros2 run ros_gz_bridge parameter_bridge /cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist /camera/image_raw@sensor_msgs/msg/Image@ignition.msgs.Image /barrier_msg@std_msgs/msg/Bool]ignition.msgs.Boolean

✅터미널 3: rviz2로 자동차 운전석 시야 확인 
$ rviz2

(실행 후 Rviz 화면에서 Add -> By topic -> camera/image_raw/Image 플러그인을 추가하고, Topic을 /camera/image_raw, QoS를 Best Effort로 설정하세요.)

✅터미널 4: 자동차 주행 노드
$ cd ~/v2i_ws

$ colcon build --symlink-install --packages-select v2i_vehicle_pkg

$ source install/setup.bash

$ ros2 run v2i_vehicle_pkg v2i_soft_stop_node

✅터미널 5: 자동차 신호
정지: $ ros2 topic pub --once /v2i_alert std_msgs/msg/Bool "{data: true}"

다시 출발: $ ros2 topic pub --once /v2i_alert std_msgs/msg/Bool "{data: false}"

✅터미널 6: 보행자 출발 신호 쏘기
$ ros2 topic pub --once /barrier_msg std_msgs/msg/Bool "{data: true}"

👉🏻완성하면 한 번에 launch 파일로 만들면 될 듯

👉🏻터미널 1~4 명령어 차례로 실행 -> [차단기 로봇이 보행자 인식 즉시] 자동차에게 터미널 5 메세지(정지) 전송 -> 자동차 멈추면, 차단기 로봇이 보행자에게 터미널 6 메세지 전송 -> [보행자가 다 건너가면] 차단기 로봇이 자동차에게 터미널 5 메세지(다시 출발) 전송

## 남은 작업
1. school_zone.sdf - 차단기 로봇 횡단보도 앞에 배치 
2. yolo 보행자 인식
3. 메세지 전송
4. 차단기 관절 제어
5. (시간이 된다면) 차단기 로봇이 "건너가세요" 음성 안내가 나와도 좋을 듯!
