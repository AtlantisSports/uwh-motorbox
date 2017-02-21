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

def cleanup():
    pi.stop()
    os.system("shutdown -h now")


configFile = "config.ini"

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

mode = "SlideLimitSetup"

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
            if !servoController.limitsSet:
                mode = "ServoLimitSetup"
            else:
                mode = "Running"

    elif mode == "ServoLimitSetup":
        servoController.move(JS.xAxis, JS.yAxis, ignoreLimits = True)

        if JS.yBtn:
            servoController.setLimit()
            JS.yBtn = False

        if servoController.limitsSet:
            mode = "Running"

    else:
        if JS.startBtn and JS.xBtn:
            mode = "SlideLimitSetup"
            JS.startBtn = False
            JS.xBtn = False

        elif JS.startBtn and JS.bBtn:
            mode = "ServoLimitSetup"
            JS.startBtn = False
            JS.bBtn = False

        motorController.setSpeed(JS.slideAxis)
        servoController.move(JS.xAxis, JS.yAxis)
