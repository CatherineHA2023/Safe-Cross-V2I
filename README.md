# Safe-Cross-V2I 🤖🚗

## 1. 주제
Safe-Cross: 비전 AI 기반 스마트 횡단보도 로봇과 자율주행 차량의 Vehicle-to-Infrastructure(V2I) 협력 제어 시스템

## 2. 목표
매년 스쿨존 및 아파트 단지 내 교차로에서 발생하는 어린이 등하굣길 교통사고는 심각한 사회적 문제로 대두되고 있습니다. 특히, 현재의 자율주행 차량은 자체 탑재된 센서에 전적으로 의존하므로, 체구가 작은 어린이가 물리적 사각지대에서 갑자기 나타나는 돌발 상황에 대처하기 매우 어렵습니다. 

이에 본 프로젝트는 횡단보도 인프라(스마트 차단기 로봇)와 모빌리티(자율주행 차량)가 실시간으로 데이터를 교환하며 위험을 사전에 차단하는 **V2I(Vehicle-to-Infrastructure) Multi-Agent 협력 시스템**을 구축합니다. 이를 통해 센서의 한계를 극복하고 어린이들의 안전한 등굣길을 보장하는 스마트 시티 교통망의 축소판을 구현하는 것을 목표로 합니다.

## 3. 진행 방법
Safe-Cross는 ROS2 및 Gazebo Fortress 시뮬레이션 환경에서 다음 5단계의 파이프라인으로 동작합니다.

1. **시뮬레이션 환경 구축**: Gazebo Fortress를 이용해 실제 등굣길과 유사한 가상 환경을 설계합니다. 환경은 크게 도로 인프라, 동적 에이전트(스마트 차단기 로봇, 자율주행 차량, 보행자(어린이) 모델), 배경 요소로 구성됩니다.

2. **인프라의 선제적 인지**: 스마트 차단기 로봇이 물리적인 차단바(Joint)를 내린 채로 대기 중에 보행자(어린이)가 횡단보도에 접근하면, 탑재된 카메라 영상과 YOLO v8 모델을 통해 객체(person, car)를 실시간으로 인식합니다. 

3. **V2I 실시간 통신**: 보행자(어린이) 인지와 동시에, 스마트 차단기 로봇은 ROS2 DDS 통신망을 통해 주변 차량에 긴급 감속을 요청하는 경고 메시지를 즉각적으로 전송합니다.

4. **자율주행 차량의 협력 제어**: 일정한 초기 속도(v)로 주행 중인 자율주행 자동차는 자체 비전 센서의 보행자 식별 여부와 무관하게, 수신된 V2I 경고 메시지를 최우선 제어 명령으로 처리합니다. 메시지 수신 즉시 속도를 일정한 변화량만큼 선형적으로 감소시키는 Soft Stop Linear Deceleration Profile을 적용하여, 횡단보도 앞에 부드럽게 정차합니다.
   
5. **안전 횡단 및 흐름 재개**: 자율주행 차량의 완전 정차가 확인되면, 스마트 차단기 로봇이 차단바(Joint)를 올리고 보행자(어린이)에게 횡단 음성 안내를 제공합니다. 횡단이 완료되면 V2I 경고 상태를 해제하고 차단바(Joint)를 다시 내려, 전체 교통 흐름을 정상적으로 재개합니다.

## 팀원 역할 분담
🙋🏻‍♀️이지현 팀원: 스마트 차단기 로봇의 YOLO 객체 탐지와 제어 및 통합 실행 / 데모 동영상 촬영을 담당했습니다.

🙋🏻‍♀️하정연 팀원: Gazebo 시뮬레이션 환경 구축 및 자율주행 차량 제어 및 보행자 Plugin / 발표 동영상 촬영을 담당했습니다.

## AI 사용
Gemini와 Claude로 코드 구현에 도움을 받았습니다. 

## 참고자료
- 객체 인식(YOLOv8 & ROS2): https://github.com/mgonzs13/yolo_ros
- 시뮬레이션 환경 구축: https://gazebosim.org/docs/fortress/building_robot/, https://gazebosim.org/docs/fortress/ros2_integration/
- 환경 렌더링: https://gazebosim.org/docs/latest/fuel_insert/
- V2I 통신망: https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html
- Kenny City Kit: https://kenney.nl/assets/city-kit-suburban
- 보행자 모델: https://www.mixamo.com/#/

## YouTube 발표 영상


## Safe-Cross Github 링크
https://github.com/CatherineHA2023/Safe-Cross-V2I

## 주요 코드 설명
💡Gazebo 시뮬레이션 환경 구축 파일: v2i_gazebo_pkg/worlds/school_zone.sdf

💡자율주행 자동차 주행 및 제어 (감속, 다시 시작 등) 파일: v2i_vehicle_pkg/v2i_vehicle_pkg/v2i_soft_stop_node.py

💡보행자 (actor) 애니메이션 및 제어 파일: v2i_gazebo_plugins/ActorControlPlugin.cc

💡스마트 차단기 YOLO 객체 탐지 및 제어 파일: v2i_vision_pkg/v2i_vision_pkg/yolo_detector_node.py

💡전체 노드 일괄 실행 파일: v2i_vision_pkg/launch/v2i_all_nodes.launch.py

