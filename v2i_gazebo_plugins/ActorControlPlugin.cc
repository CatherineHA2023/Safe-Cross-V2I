#include <ignition/gazebo/System.hh>
#include <ignition/gazebo/components/Actor.hh>
#include <ignition/gazebo/components/Pose.hh>          
#include <ignition/gazebo/components/Name.hh>         
#include <ignition/transport/Node.hh>
#include <ignition/msgs/boolean.pb.h>
#include <ignition/plugin/Register.hh>
#include <ignition/common/Console.hh>

using namespace ignition;

class ActorControlPlugin
    : public gazebo::System,
      public gazebo::ISystemConfigure,
      public gazebo::ISystemPreUpdate
{
public:
  void Configure(const gazebo::Entity &_entity,
                 const std::shared_ptr<const sdf::Element> &,
                 gazebo::EntityComponentManager &_ecm,
                 gazebo::EventManager &) override
  {
    this->actorEntity = _entity;

    auto poseComp = _ecm.Component<gazebo::components::Pose>(_entity);
    if (poseComp)
      this->initialPose = poseComp->Data();

    // ⭐ actor를 똑바로 세우는 회전 (Mixamo Y-up → Gazebo Z-up)
    const double ROLL_FIX  = 1.5707;  
    const double PITCH_FIX = 0.0;
    const double YAW_FIX   = -1.5707;      

    math::Pose3d trajInitial(this->initialPose.Pos().X(),
                              this->initialPose.Pos().Y(),
                              this->initialPose.Pos().Z(),
                              ROLL_FIX, PITCH_FIX, YAW_FIX);

    this->fixRoll  = ROLL_FIX;
    this->fixPitch = PITCH_FIX;
    this->fixYaw   = YAW_FIX;

    if (!_ecm.Component<gazebo::components::TrajectoryPose>(_entity))
    {
      _ecm.CreateComponent(_entity,
        gazebo::components::TrajectoryPose(trajInitial));
    }

    if (!_ecm.Component<gazebo::components::AnimationName>(_entity))
    {
      _ecm.CreateComponent(_entity,
        gazebo::components::AnimationName("walking"));
    }

    if (!_ecm.Component<gazebo::components::AnimationTime>(_entity))
    {
      _ecm.CreateComponent(_entity,
        gazebo::components::AnimationTime());
    }

    this->node.Subscribe("/barrier_msg",
      &ActorControlPlugin::OnMoveCommand, this);

    ignmsg << "============================================\n";
    ignmsg << "[Actor Plugin] 🟢 어린이 (보행자) 두뇌 장착 완료\n";
    ignmsg << "[Actor Plugin] 초기 위치: " << this->initialPose.Pos() << "\n";
    ignmsg << "[Actor Plugin] 🧍 안내 대기 중\n";
    ignmsg << "============================================\n";
  }

  void OnMoveCommand(const msgs::Boolean &_msg)
  {
    this->shouldMove = _msg.data();
    ignmsg << "[Actor Plugin] 🚦 스마트 차단기 로봇의 안내 수신: "
           << (_msg.data() ? "🚶 전진" : "정지") << "\n";
  }

  void PreUpdate(const gazebo::UpdateInfo &_info,
                 gazebo::EntityComponentManager &_ecm) override
  {
    if (_info.paused) return;

    // === 1. 애니메이션: shouldMove일 때만 시간 누적 (= 걷기 모션 재생) ===
    //    shouldMove가 false면 AnimationTime을 그대로 두므로
    //    actor는 첫 프레임 자세(보통 차렷 자세)로 정지!
    if (this->shouldMove)
    {
      auto animTimeComp =
          _ecm.Component<gazebo::components::AnimationTime>(this->actorEntity);
      if (animTimeComp)
      {
        auto newTime = animTimeComp->Data() + _info.dt;
        *animTimeComp = gazebo::components::AnimationTime(newTime);
        _ecm.SetChanged(this->actorEntity,
          gazebo::components::AnimationTime::typeId,
          gazebo::ComponentState::PeriodicChange);
      }
 
      // === 2. 이동 신호 시 X 오프셋 누적 (월드 X축 방향으로 전진) ===
      this->offset_x -= 0.002;
    }

    // === 3. TrajectoryPose 갱신 (위치 + 자세 보정 회전 유지) ===
    auto trajPoseComp =
        _ecm.Component<gazebo::components::TrajectoryPose>(this->actorEntity);
    if (trajPoseComp)
    {
      math::Pose3d newPose(
        this->initialPose.Pos().X() + this->offset_x,
        this->initialPose.Pos().Y(),
        this->initialPose.Pos().Z(),
        this->fixRoll, this->fixPitch, this->fixYaw);  // ⭐ 자세 회전 매번 유지

      *trajPoseComp = gazebo::components::TrajectoryPose(newPose);
      _ecm.SetChanged(this->actorEntity,
        gazebo::components::TrajectoryPose::typeId,
        gazebo::ComponentState::OneTimeChange);
    }
  }

private:
  gazebo::Entity actorEntity;
  transport::Node node;
  std::atomic<bool> shouldMove{false};
  math::Pose3d initialPose{math::Pose3d::Zero};
  double offset_x = 0.0;
  double fixRoll = 0.0;
  double fixPitch = 0.0;
  double fixYaw = 0.0;
};

IGNITION_ADD_PLUGIN(
    ActorControlPlugin,
    ignition::gazebo::System,
    ActorControlPlugin::ISystemConfigure,
    ActorControlPlugin::ISystemPreUpdate)
IGNITION_ADD_PLUGIN_ALIAS(ActorControlPlugin, "ActorControlPlugin")