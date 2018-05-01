'''
Created on Feb 18, 2017

@author: Tristan Debrunner

Runs the motor box in Underwater Hockey mode
'''

import os
import pigpio
import motorController
import servoController
import joyStick
import subprocess
import shlex
import signal
import configparser

def cleanup():
    motorController.softStop()
    pi.stop()
    xboxdrv.send_signal(signal.SIGINT)
    atemController.send_signal(signal.SIGINT)
    os.system("shutdown -h now")


configFile = "config.ini"

config = configparser.ConfigParser()
config.read(configFile)
useEndLimits = config['Options'].getboolean('useEndLimits')

# Start xboxdrv
xboxdrv = subprocess.Popen(shlex.split("sudo xboxdrv -c /home/pi/uwh-motorbox/xboxdrvconfig.ini"))
print("xboxdrv started")

# Start the ATEM Controller
atemController = subprocess.Popen(shlex.split("sudo python3 {}/ATEMCommunicate.py".format(os.path.abspath(''))), stdin=subprocess.PIPE)

#Connect to pigpiod
pi = pigpio.pi()
retryCount = 0
while not pi.connected and retryCount < 5000:
    sleep(0.001)
    pi = pigpio.pi()
    retryCount += 1
if retryCount >= 5000:
    print("Could not connect to pigpiod. Exiting")
    cleanup()

JS = joyStick.JoyStick()
motorController = motorController.MotorController(pi, configFile)
servoController = servoController.ServoController(pi, configFile)

print("Entering Main Loop in slide limit setup mode")
mode = "SlideLimitSetup" if useEndLimits else "Running"

while True:
    JS.update()

    if JS.startBtn and JS.backBtn: #  This is the signal to quit
        cleanup()
    
    if mode == "SlideLimitSetup":
        motorController.setSpeed(JS.slideAxis)

        if JS.yBtn:
            motorController.setLimit()
            JS.yBtn = False

        if JS.startBtn and JS.xBtn:
            motorController.switchDirection()
            JS.startBtn = False
            JS.xBtn = False

        if motorController.limitsSet:
            if not servoController.limitsSet:
                print("Entering servo limit setup mode")
                mode = "ServoLimitSetup"
            else:
                print("Entering Running Mode")
                mode = "Running"

    elif mode == "ServoLimitSetup":
        servoController.move(JS.panAxis, JS.tiltAxis, ignoreLimits = True)

        if JS.yBtn:
            servoController.setLimit()
            JS.yBtn = False

        if servoController.limitsSet:
            print("Entering Running Mode from servo limit setup mode")
            mode = "Running"

    else:
        if JS.startBtn and JS.xBtn:
            mode = "SlideLimitSetup"
            JS.startBtn = False
            JS.xBtn = False

        elif JS.startBtn and JS.bBtn:
            mode = "ServoLimitSetup"
            servoController.limitsSet = False
            JS.startBtn = False
            JS.bBtn = False

        if JS.yBtn:
            atemController.stdin.write("CAM1")
            JS.yBtn = False

        if JS.aBtn:
            atemController.stdin.write("CAM2")
            JS.aBtn = False

        motorController.setSpeed(JS.slideAxis)
        servoController.move(JS.panAxis, JS.tiltAxis)
