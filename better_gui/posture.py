# -*- coding: future_fstrings -*-
import qi
import config
import time 

STIFFNESS = 0.6
TIME = 1.5

session = qi.Session()
url = f"tcp://{config.IP}:{config.PORT}"
print(f"Attempting to connect to: {url}")
session.connect(url)
posture = session.service("ALRobotPosture")
motion = session.service("ALMotion")
tts = session.service("ALTextToSpeech")

posture.goToPosture("StandInit", 0.8)
time.sleep(1)


motion.setStiffnesses("Arms", STIFFNESS)

tts.say("Watch my dance moves")

left_arm_joints = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]
right_arm_joints = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]

print("Move 1: Extending arms...")
motion.angleInterpolation(
    left_arm_joints + right_arm_joints,
    [0.0, 0.5, 0.0, -0.1, 0.0] + [0.0, -0.5, 0.0, 0.1, 0.0],
    [TIME, TIME, TIME, TIME, TIME] + [TIME, TIME, TIME, TIME, TIME],
    True
)

print("Move 2: Crossing arms...")
motion.angleInterpolation(
    left_arm_joints + right_arm_joints,
    [1.0, -0.3, 0.0, -1.5, 0.0] + [1.0, 0.3, 0.0, 1.5, 0.0],
    [TIME, TIME, TIME, TIME, TIME] + [TIME, TIME, TIME, TIME, TIME],
    True
)

print("Move 3: Y-shape pose...")
motion.angleInterpolation(
    left_arm_joints + right_arm_joints,
    [-0.5, 1.2, -0.5, -0.3, 0.0] + [-0.5, -1.2, 0.5, 0.3, 0.0],
    [TIME, TIME, TIME, TIME, TIME] + [TIME, TIME, TIME, TIME, TIME],
    True
)

print("Move 4: Wave motion...")
motion.angleInterpolation(
    left_arm_joints[0:2] + right_arm_joints[0:2],
    [-1.0, 0.3] + [1.0, -0.3],
    [TIME, TIME] + [TIME, TIME],
    True
)
motion.angleInterpolation(
    left_arm_joints[0:2] + right_arm_joints[0:2],
    [1.0, -0.3] + [-1.0, 0.3],
    [TIME, TIME] + [TIME, TIME],
    True
)
motion.angleInterpolation(
    left_arm_joints[0:2] + right_arm_joints[0:2],
    [-1.0, 0.3] + [1.0, -0.3],
    [TIME, TIME] + [TIME, TIME],
    True
)

print("Move 5: Hand movements...")
# Open both hands
motion.openHand('LHand')
motion.openHand('RHand')
time.sleep(0.5)

motion.angleInterpolation(
    left_arm_joints + right_arm_joints,
    [0.2, 0.8, -1.5, -0.5, 0.0] + [0.2, -0.8, 1.5, 0.5, 0.0],
    [TIME, TIME, TIME, TIME, TIME] + [TIME, TIME, TIME, TIME, TIME],
    True
)

motion.closeHand('LHand')
motion.closeHand('RHand')

print("Final pose...")
motion.angleInterpolation(
    left_arm_joints + right_arm_joints,
    [0.4, 0.4, 0.0, -0.6, 0.0] + [0.4, -0.4, 0.0, 0.6, 0.0],
    [TIME, TIME, TIME, TIME, TIME] + [TIME, TIME, TIME, TIME, TIME],
    True
)

print("Returning to initial position...")
posture.goToPosture("StandInit", 0.8)

print("Performance complete!")
