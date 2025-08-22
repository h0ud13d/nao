# -*- coding: future_fstrings -*-
import qi
import config
from robot_agent import NaoActions
from robot_environment import NaoEnvironment
from robot_gui import NaoControlGUI


if __name__ == "__main__":
    print(f"Robot IP: {config.IP}, Port: {config.PORT}")
    nao_brain = NaoEnvironment(config.IP, config.PORT)

    if not nao_brain.init_robot():
        print(exit)

    nao_actions = NaoActions(nao_brain)
    nao_gui = NaoControlGUI(nao_actions)
    nao_actions.speak("Hello Friends")
    nao_actions.change_posture("StandInit", 0.5)
    nao_gui.run()
