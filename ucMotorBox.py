'''
Created on Feb 18, 2017

@author: Tristan Debrunner

Runs the motor box in Underwater Hockey mode with an external
microcontroller
'''

import os
import pigpio
import motorController
import servoController
import joyStick
import subprocess
import shlex
import signal

def cleanup():
    motorController.softStop()
    pi.stop()
    xboxdrv.send_signal(signal.SIGINT)
    os.system("shutdown -h now")


configFile = "config.ini"

# Start xboxdrv
xboxdrv = subprocess.Popen(shlex.split("sudo xboxdrv -c /home/pi/uwh-motorbox/xboxdrvconfig.ini"))
print("xboxdrv started")

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
servoController = servoController.ServoController(None, None)

print("Entering Main Loop in running mode")
mode = "Running"

serial = pi.serial_open('/dev/ttyAMA0', 9600)

while True:
    JS.update()

    if JS.startBtn and JS.backBtn: #  This is the signal to quit
        cleanup()

    if mode == "ServoLimitSetup":
        servoController.move(JS.panAxis, JS.tiltAxis, ignoreLimits = True)

        if JS.yBtn:
            servoController.setLimit()
            JS.yBtn = False

        if servoController.limitsSet:
            print("Entering Running Mode from servo limit setup mode")
            mode = "Running"

    else:
        if JS.startBtn and JS.bBtn:
            mode = "ServoLimitSetup"
            servoController.limitsSet = False
            JS.startBtn = False
            JS.bBtn = False

        if JS.backBtn and JS.xBtn:
            pi.serial_write(serial, 'L')
            JS.backBtn = False
            JS.xBtn = False

        if JS.backBtn and JS.yBtn:
            pi.serial_write(serial, 'H')
            JS.backBtn = False
            JS.yBtn = False

        if JS.backBtn and JS.bBtn:
            pi.serial_write(serial, 'R')
            JS.backBtn = False
            JS.bBtn = False

        if JS.xBtn:
            pi.serial_write(serial, 'l')
            JS.xBtn = False

        if JS.yBtn:
            pi.serial_write(serial, 'h')
            JS.yBtn = False

        if JS.bBtn:
            pi.serial_write(serial, 'r')
            JS.bBtn = False

        servoController.move(JS.panAxis, JS.tiltAxis)

        pi.serial_write(serial, ['p', int(servoController.pan * 0.0128) - 128,
                                 't', int(servoController.tilt * 0.0128) - 128,
                                 's', int(JS.slideAxis/2)])
