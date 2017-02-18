'''
Created on February 18, 2017

@author: Tristan Debrunner
'''

import subprocess
from evdev import InputDevice, categorize, ecodes, list_devices
from time import sleep


class JoyStick():
    '''
    Interfaces with an xbox driver coneected through xboxdrv
    '''

    def __init__(self):
        '''
        Constructor
        '''

        self.JS = None
        loopCount = 0

        while self.JS == None and loopCount < 5000:
            devices = [InputDevice(fn) for fn in list_devices()]
            for dev in devices:
                if dev.name == 'Xbox Gamepad (userspace driver)':
                    JS = InputDevice(dev.fn)
                    break
            sleep(0.001)
            loopCount += 1

        if loopCount >= 5000:
            print("ERROR: Could not connect to Joystick")

        JS.grab()

        self.backBtn = False
        self.startBtn = False
        self.aBtn = False
        slef.bBtn = False
        self.xBtn = False
        self.yBtn = False
        self.panAxis = 0.
        self.tiltAxis = 0.
        self.slideAxis = 0.


    def getJSEvents(self):
        JSEvents = self.JS.read()
        try:
            for event in JSEvents:
                if event.type == ecodes.EV_ABS:
                    if even.code == ecodes.ABS_X:
                        self.panAxis = event.value
                    elif event.code == ecodes.ABS_Y:
                        self.tiltAxis = event.value
                    elif event.code == ecodes.ABS_Z:
                        self.slideAxis = event.value * self.slideDir
                elif event.type == ecodes.EV_KEY:
                    if event.value == True:
                        if event.code == ecodes.BTN_SELECT:
                            self.backBtn = True
                        elif event.code == ecodes.BTN_START:
                            self.startBtn = True
                        elif event.code == ecodes.BTN_A:
                            self.aBtn = True
                        elif event.code == ecodes.BTN_B:
                            self.bBtn = True
                        elif event.code == ecodes.BTN_X:
                            self.xBtn = True
                        elif event.code == ecodes.BTN_Y:
                            self.yBtn = True
                    elif event.value == False:
                        if event.code == ecodes.BTN_SELECT:
                            self.backBtn = False
                        elif event.code == ecodes.BTN_START:
                            self.startBtn = False
                        elif event.code == ecodes.BTN_A:
                            self.aBtn = False
                        elif event.code == ecodes.BTN_B:
                            self.bBtn = False
                        elif event.code == ecodes.BTN_X:
                            self.xBtn = False
                        elif event.code == ecodes.BTN_Y:
                            self.yBtn = False
        except IOError:
            pass

