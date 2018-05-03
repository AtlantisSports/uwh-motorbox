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
import serial
import array
from time import sleep, time

def cleanup():
    xboxdrv.send_signal(signal.SIGINT)
    exit()


configFile = "config.ini"

# Start xboxdrv
xboxdrv = subprocess.Popen(shlex.split("sudo xboxdrv -c /home/pi/uwh-motorbox/xboxdrvconfig.ini"))
print("xboxdrv started")

JS = joyStick.JoyStick()
servoController = servoController.ServoController(None, None)

print("Entering Main Loop in running mode")
mode = "Running"

ser = serial.Serial(
            port='/dev/ttyAMA0',
            baudrate = 115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1)

lastSlideSendTime = time()
sentPan = False
sentTilt = False
oldPan = ''
oldTilt = ''
oldSlide = ''

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
            #faultTolerantSerial('L')
            ser.write(array.array('B', [ord('L')]).tostring())
            JS.backBtn = False
            JS.xBtn = False

        if JS.backBtn and JS.yBtn:
            #faultTolerantSerial('H')
            ser.write(array.array('B', [ord('H')]).tostring())
            JS.backBtn = False
            JS.yBtn = False

        if JS.backBtn and JS.bBtn:
            #faultTolerantSerial('R')
            ser.write(array.array('B', [ord('R')]).tostring())
            JS.backBtn = False
            JS.bBtn = False

        if JS.xBtn:
            #faultTolerantSerial('l')
            ser.write(array.array('B', [ord('l')]).tostring())
            JS.xBtn = False

        if JS.yBtn:
            #faultTolerantSerial('h')
            ser.write(array.array('B', [ord('h')]).tostring())
            JS.yBtn = False

        if JS.bBtn:
            #faultTolerantSerial('r')
            ser.write(array.array('B', [ord('r')]).tostring())
            JS.bBtn = False

        servoController.move(JS.panAxis, JS.tiltAxis)

        if ((time() - lastSlideSendTime) > 0.01 and not sentPan):
            toSendPan = array.array('B', [ord('p'), min(255, max(0, int(servoController.pan * 0.0128)))]).tostring()
            if toSendPan != oldPan:
                ser.write(toSendPan)
                oldPan = toSendPan
            sentPan = True

        if ((time() - lastSlideSendTime) > 0.02 and not sentTilt):
            toSendTilt = array.array('B', [ord('t'), min(255, max(0, int(servoController.tilt * 0.0128)))]).tostring()
            if toSendTilt != oldTilt:
                ser.write(toSendTilt)
                oldTilt = toSendTilt
            sentTilt = True

        if ((time() - lastSlideSendTime) > 0.03):
            toSendSlide = array.array('B', [ord('s'), min(255, max(0, int(JS.slideAxis/2 + 128)))]).tostring()
            if toSendSlide != oldSlide:
                ser.write(toSendSlide)
                oldSlide = toSendSlide
            #print('p: {}   t: {}   s: {}'.format(toSendPan, toSendTilt, toSendSlide))
            lastSlideSendTime = time()
            sentPan = False
            sentTilt = False

        sleep(0.0005)
