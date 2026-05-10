cmake_minimum_required(VERSION 3.10)
project(actor_control_plugin)

# C++17 표준 사용
set(CMAKE_CXX_STANDARD 17)

# Ignition Fortress (버전 6) 라이브러리 찾기
find_package(ignition-gazebo6 REQUIRED)
find_package(ignition-transport11 REQUIRED)
find_package(ignition-msgs8 REQUIRED)

# 플러그인 라이브러리(.so) 생성
add_library(actor_control_plugin SHARED ActorControlPlugin.cc)

# 필요한 헤더 및 라이브러리 링크
target_link_libraries(actor_control_plugin
  ignition-gazebo6::core
  ignition-transport11::ignition-transport11
  ignition-msgs8::ignition-msgs8
)