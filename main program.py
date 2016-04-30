from evdev import InputDevice, categorize, ecodes, list_devices
from time import sleep
import time
import pigpio
import os
import subprocess
import signal
import shlex
import math
import numpy as np
import pickle

# Options
maxaccel = 2.5
maxdecel = 40
speedLimit = 500  # Motor speed limit near soft limits
speedLimitZoneSize = 12800  # Measured in encoder pulses
slideDir = 1  # Set to 1 or -1 to change direction of slide movement

def stepperCalculator(frequency):
    if frequency != 0:
        PS = math.ceil(math.log((3921.56867 / frequency), 2))
        modulo = 1000000 / (frequency * (2 ** PS))
        ret = [0x00, int(modulo), int(PS)]
    else:
        ret = [0, 0, 0]
    return ret


def setSlideLimits():
    print "Entering slide limit set mode"
    done = False
    global direction, slideAxis, startBtn, xBtn, yBtn
    global upperStepperLimit, lowerStepperLimit, bus, slideDir
    oldslideaxis = 0.
    limit1 = 0
    limit2 = 0
    while not done:
        # Get events from evdev
        getJSEvents()
        # Calculate direction
        if slideAxis != 0:
            if slideAxis > 0:
                direction = 1
            else:
                direction = 0
        # Send the new stepper frequency if changed
        if slideAxis != 0:
            stepperfrequency = max(minStepperHz, min(maxStepperSetupHz, stepperSetupHzConstant * math.fabs(slideAxis)))
        else:
            stepperfrequency = 0
        if slideAxis != oldslideaxis:
            # print "stepperfrequency: " + str(stepperfrequency)
            tosend = stepperCalculator(stepperfrequency)
            if direction == 1:
                tosend[2] |= 0x80
            else:
                tosend[2] &= 0x7F
            try:
                pi.i2c_write_device(bus, tosend)
            except pigpio.error:
                print "i2c write failed"
        oldslideaxis = slideAxis
        # Set a limit if the Y button is pressed
        if yBtn:
            if limit1 == 0:
                try:
                    limit1 = getEncoderCount()
                except IndexError:
                    print "i2c read failed"
                    limit1 = 0
                yBtn = False
                print "limit1 set to: " + str(limit1)
            else:  # If the first limit is already set, set the second, save to global variables, and exit
                try:
                    limit2 = getEncoderCount()
                    print "limit2 set to: " + str(limit2)
                    upperStepperLimit = max(limit1, limit2)
                    lowerStepperLimit = min(limit1, limit2)
                    yBtn = False
                    done = True
                except IndexError:
                    print "i2c read failed"
                    limit2 = 0
        if startBtn and xBtn:
            print "Switching stepper direction"
            slideDir *= -1
            startBtn = 0
            xBtn = 0
        sleep(0.01)
    print "Exiting stepper limit set mode"
    return


def setServoLimits():
    print "Entering servo limit set mode"
    global panAxis, tiltAxis, yBtn, tiltmin, pancenter, tiltcenter, radius
    limit1 = 0
    limit2 = 0
    limit3 = 0
    panpos = 1500
    tiltpos = 1500
    done = False
    while not done:
        # Get events from evdev
        getJSEvents()
        if yBtn:
            if limit1 == 0:
                limit1 = [panpos, tiltpos]
                print "limit1 set to " + str(limit1)
                yBtn = False
            elif limit2 == 0:
                limit2 = [panpos, tiltpos]
                print "limit2 set to " + str(limit2)
                yBtn = False
            elif limit3 == 0:
                limit3 = [panpos, tiltpos]
                print "limit3 set to " + str(limit3)
                yBtn = False
            else:
                tiltmin = tiltpos
                d = 2 * (limit1[0] * (limit2[1] - limit3[1]) + limit2[0] * (limit3[1] - limit1[1]) + limit3[0] * (limit1[1] - limit2[1]))
                pancenter = ((limit1[0] ** 2 + limit1[1] ** 2) * (limit2[1] - limit3[1]) + (limit2[0] ** 2 + limit2[1] ** 2) * (limit3[1] - limit1[1]) + (limit3[0] ** 2 + limit3[1] ** 2) * (limit1[1] - limit2[1])) / d
                tiltcenter = ((limit1[0] ** 2 + limit1[1] ** 2) * (limit3[0] - limit2[0]) + (limit2[0] ** 2 + limit2[1] ** 2) * (limit1[0] - limit3[0]) + (limit3[0] ** 2 + limit3[1] ** 2) * (limit2[0] - limit1[0])) / d
                radius = math.sqrt((limit1[0] - pancenter)**2 + (limit1[1] - tiltcenter)**2)
                yBtn = False
                done = True
        if panAxis != 0:
            panpos -= (1.5 * 10 ** (-8)) * (panAxis * math.fabs(panAxis))
            modvalue = int(panpos * 2)
            try:
                pi.i2c_write_device(bus, [0x01, (modvalue & 0xFF00) >> 8, modvalue & 0xFF])
            except pigpio.error:
                print "i2c write failed"
        if tiltAxis != 0:
            tiltpos += (0.9 * 10 ** (-8)) * (tiltAxis * math.fabs(tiltAxis))
            modvalue = int(tiltpos * 2)
            try:
                pi.i2c_write_device(bus, [0x03, (modvalue & 0xFF00) >> 8, modvalue & 0xFF])
            except pigpio.error:
                print "i2c write failed"
    print "Center coordinates: " + str(pancenter) + "," + str(tiltcenter)
    print "Radius: " + str(radius)
    print "tiltmin: " + str(tiltmin)
    datatosave = [pancenter, tiltcenter, radius, tiltmin]
    output = open('ServoLimitData.pkl', 'w')
    pickle.dump(datatosave, output)
    output.close()
    print "Exiting servo limit set mode"
    return


def getJSEvents():
    global panAxis, tiltAxis, slideAxis, backBtn, startBtn, aBtn, bBtn, xBtn, yBtn, JS
    JSevents = JS.read()
    try:
        for event in JSevents:
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    panAxis = event.value
                elif event.code == ecodes.ABS_Y:
                    tiltAxis = event.value
                elif event.code == ecodes.ABS_Z:
                    slideAxis = event.value * slideDir
            elif event.type == ecodes.EV_KEY:
                if event.value == True:
                    if event.code == ecodes.BTN_SELECT:
                        backBtn = True
                    elif event.code == ecodes.BTN_START:
                        startBtn = True
                    elif event.code == ecodes.BTN_A:
                        aBtn = True
                    elif event.code == ecodes.BTN_B:
                        bBtn = True
                    elif event.code == ecodes.BTN_X:
                        xBtn = True
                    elif event.code == ecodes.BTN_Y:
                        yBtn = True
                elif event.value == False:
                    if event.code == ecodes.BTN_SELECT:
                        backBtn = False
                    elif event.code == ecodes.BTN_START:
                        startBtn = False
                    elif event.code == ecodes.BTN_A:
                        aBtn = False
                    elif event.code == ecodes.BTN_B:
                        bBtn = False
                    elif event.code == ecodes.BTN_X:
                        xBtn = False
                    elif event.code == ecodes.BTN_Y:
                        yBtn = False
    except IOError:
        pass

    return


def getEncoderCount():
    reply = pi.i2c_read_device(bus, 3)
    count = reply[1][0] * 256 * 256 + reply[1][1] * 256 + reply[1][2]
    # print count
    return count


### Begin Parameters for Camera Motion Inside the Dome ###

# System 1 params # System Left for PCC's 2015
# tiltmin = 1140.  # 1159. # High tilt
# tiltmax = 1690.  # 1688. # Low tilt
# panmaxupper = 2000.  # 1906. # Left top
# panminupper = 1060  # 1232. # Right top
# panmaxlower = 1660.  # 1692. # Left bottom
# panminlower = 1300.  # 1321. # Right bottom

# System 2 params # System Right for PCC's 2015
# tiltmin = 1320. ### High tilt
# tiltmax = 1950. #1950. ### Low tilt
# panmaxupper = 2040. #1850. ### Left top
# panminupper = 1080. #1010. ### Right top
# panmaxlower = 1640. #1700. ### Left bottom
# panminlower = 1420. #1440. ### Right bottom

# Limits for setup
#
# tiltmin = 1060
# tiltmax = 1750
# panmin = 500          # servo limits
# panmax = 2500
# panmin = 1200        # camera case fixed limits
# panmax = 1976

### End Parameters for Camera Motion Inside the Dome ###

# Start pigpio
os.system("sudo pigpiod")
sleep(2)  # Wait for pigpiod to start
pi = pigpio.pi()
pi.hardware_clock(4, 2000000)
bus = pi.i2c_open(1, address, 0)
pi.set_mode(OAReset, pigpio.OUTPUT)
pi.set_mode(OAOut, pigpio.INPUT)
pi.set_mode(zoomIn, pigpio.OUTPUT)
pi.set_mode(zoomOut, pigpio.OUTPUT)
pi.write(zoomIn, 1)
pi.write(zoomOut, 1)

# Start xboxdrv
xboxdrv = subprocess.Popen(shlex.split(
        "sudo xboxdrv --detach-kernel-driver -s --deadzone 15% --trigger-as-zaxis --deadzone-trigger 15% -l 2"))

# Reset the Op Amp
pi.write(OAReset, 0)
print "OAReset set Low"
sleep(5)  # Wait for reset and for xboxdrv to initiate
pi.write(OAReset, 1)
print "OAReset set High"

# Initiate joystick device
devices = [InputDevice(fn) for fn in list_devices()]
for dev in devices:
    if dev.name == 'Xbox Gamepad (userspace driver)':
        JS = InputDevice(dev.fn)
        break
JS.grab()

# Set variables
backBtn = False
startBtn = False
aBtn = False
bBtn = False
xBtn = False
yBtn = False
zoomInStartTime = 0
zoomOutStartTime = 0
panAxis = 0.
tiltAxis = 0.
slideAxis = 0.
stepperSpeed = 0.
oldStepperSpeed = stepperSpeed
pan = 1500
tilt = 1500
oldpan = pan
oldtilt = tilt
stepperCount = 0
upperStepperLimit = 0
lowerStepperLimit = 0
stepperFrequency = 0.
toSend = [0,0,0]
oldToSend = toSend
direction = 0
olddir = 0.
dir0hstop = False
dir1hstop = False
# curTime = 0
stopTime = 0.
OAResetComplete = True

# Read servo limit info from file
try:
    pklfile = open('ServoLimitData.pkl', 'r')
    inputdata = pickle.load(pklfile)
    pklfile.close()
    pancenter = inputdata[0]
    tiltcenter = inputdata[1]
    radius = inputdata[2]
    tiltmin = inputdata[3]
# If file cannot be found, set servo limits
except IOError:
    pancenter = 0
    tiltcenter = 0
    radius = 0
    tiltmin = 0
    print "ServoLimitData.pkl does not exist, entering servo limit setup mode"
    setServoLimits()

# Set the stepper limits before normal operation
setStepperLimits()

print "Entering Main Loop"

# -----------Main Program Loop-------------
while not backBtn or not startBtn:
    # print str(curTime - time.time())
    # Get events from evdev
    getJSEvents()
    # Read the current Stepper position from the MCU
    try:
        stepperCount = getEncoderCount()
    except IndexError:
        print "i2c read failed"
    # Save the current time
    curTime = time.time()
    # Respond to button presses
    if startBtn and xBtn:
        startBtn = False
        xBtn = False
        setStepperLimits()
    elif startBtn and bBtn:
        startBtn = False
        bBtn = False
        setServoLimits()
    elif yBtn:
        if zoomInStartTime == 0:
            if zoomOutStartTime != 0:
                pi.write(zoomOut, 1)
                zoomOutStartTime = 0
            pi.write(zoomIn, 0)
            zoomInStartTime = curTime
        yBtn = False
    elif aBtn:
        if zoomOutStartTime == 0:
            if zoomInStartTime != 0:
                pi.write(zoomIn, 1)
                zoomInStartTime = 0
            pi.write(zoomOut, 0)
            zoomOutStartTime = curTime
        aBtn = False
    # Stop zooming after zoomTime has elapsed
    if zoomInStartTime != 0:
        if zoomInStartTime < (curTime - zoomTime):
            pi.write(zoomIn, 1)
            zoomInStartTime = 0
    if zoomOutStartTime != 0:
        if zoomOutStartTime < (curTime - zoomTime):
            pi.write(zoomOut, 1)
            zoomOutStartTime = 0
    # Limit stepperSpeed change
    # print "Input: " + str(slideAxis)
    if math.fabs(slideAxis) > math.fabs(oldStepperSpeed):
        if math.fabs(slideAxis - oldStepperSpeed) > maxaccel:
            if slideAxis > oldStepperSpeed:
                stepperSpeed = oldStepperSpeed + maxaccel
            else:
                stepperSpeed = oldStepperSpeed - maxaccel
        else:
                stepperSpeed = slideAxis
    else:
        if math.fabs(slideAxis - oldStepperSpeed) > maxdecel:
            if slideAxis > oldStepperSpeed:
                stepperSpeed = oldStepperSpeed + maxdecel
            else:
                stepperSpeed = oldStepperSpeed - maxdecel
        else:
            stepperSpeed = slideAxis
    # print "After acceleration/deceleration limit: " + str(stepperSpeed)
    # Calculate direction
    if stepperSpeed != 0:
        if stepperSpeed > 0:
            direction = 1
        else:
            direction = 0
    # Limit stepperSpeed to speedLimit near soft stops and to 0 when across soft stops, but respect deceleration limit
    if direction == 0 and stepperCount > (upperStepperLimit - speedLimitZoneSize):
        if stepperCount > upperStepperLimit:
            if stepperSpeed >= -maxdecel:  # Beacuse direction is 0, stepperSpeed must be <0
                stepperSpeed = 0
            else:
                stepperSpeed += maxdecel
        elif stepperSpeed < -speedLimit:  # Beacuse direction is 0, stepperSpeed must be <0
            if stepperSpeed >= -speedLimit - maxdecel:
                stepperSpeed = -speedLimit
            else:
                stepperSpeed += maxdecel
    if direction == 1 and stepperCount < (lowerStepperLimit + speedLimitZoneSize):
        if stepperCount < lowerStepperLimit:
            if stepperSpeed <= maxdecel:  # Beacuse direction is 1, stepperSpeed must be >0
                stepperSpeed = 0
            else:
                stepperSpeed -= maxdecel
        elif stepperSpeed > speedLimit:  # Beacuse direction is 1, stepperSpeed must be >0
            if stepperSpeed <= speedLimit + maxdecel:
                stepperSpeed = speedLimit
            else:
                stepperSpeed -= maxdecel
    # Calculate the frequency to send to the stepper
    # print "Limits Applied: " + str(stepperSpeed)
    if stepperSpeed != 0:
        stepperFrequency = max(minStepperHz, min(maxStepperHz, stepperHzConstant * math.fabs(stepperSpeed)))
    else:
        stepperFrequency = 0
    oldStepperSpeed = stepperSpeed
    # Set stop flags if magnetic switch triggers
    if pi.read(OAOut) == True and stopTime == 0:
        if direction == 0:
            dir0hstop = True
        elif direction == 1:
            dir1hstop = True
        print "Hard Stopped"
        pi.write(OAReset, 0)
        print "OAReset set Low"
        stopTime = curTime
    elif stopTime != 0:
        if stopTime < (curTime - 0.01):
            pi.write(OAReset, 1)
            print "OAReset set High"
    # Reverse if hard stop flag set
    if dir0hstop:
        if stopTime > (curTime - reverseTime):
            stepperFrequency = reverseSpeed
        else:
            dir0hstop = False
            stopTime = 0
            stepperFrequency = 0
            print "Reverse in dir 1 finished"
    if dir1hstop:
        if stopTime > (curTime - reverseTime):
            stepperFrequency = -reverseSpeed
        else:
            dir1hstop = False
            stopTime = 0
            stepperFrequency = 0
            print "Reverse in dir 0 finished"
    # Calculate new servo values
    pan -= (1.5 * 10 ** (-9)) * (panAxis * math.fabs(panAxis))
    tilt += (0.9 * 10 ** (-9)) * (tiltAxis * math.fabs(tiltAxis))
    # Limit servos to vertical max and within circle
    if tilt < tiltmin:
        tilt = tiltmin
    vector = np.array([pan - pancenter, tilt - tiltcenter])
    norm = np.linalg.norm(vector)
    if norm > radius:
        vector = np.multiply(vector, (radius / norm))
        pan = pancenter + vector[0]
        tilt = tiltcenter + vector[1]
    # Send frequency of stepper pulses if changed
    toSend = stepperCalculator(stepperFrequency)
    if direction == 1:
        toSend[2] |= 0x80
    else:
        toSend[2] &= 0x7F
    if toSend != oldToSend:
        try:
            pi.i2c_write_device(bus, toSend)
        except pigpio.error:
            print "i2c write failed"
    oldToSend = toSend
    # Send pan value if changed
    if pan != oldpan:
        panmod = int(pan * 2)
        try:
            pi.i2c_write_device(bus, [0x01, (panmod & 0xFF00) >> 8, panmod & 0xFF])
        except pigpio.error:
            print "i2c write failed"
        # pan -= (1.5 * 10 ** (-8)) * (panAxis * math.fabs(panAxis))
        # panmin = round(panminupper - ((panminupper - panminlower) / (tiltmax - tiltmin)) * (
        #     tilt - tiltmin))  # camera case tilt-dependent limits
        # panmax = round(panmaxupper - ((panmaxupper - panmaxlower) / (tiltmax - tiltmin)) * (tilt - tiltmin))
        # pan = max(panmin, min(panmax, pan))  # camera case fixed limits
        # panstr = str(int(pan))
        # #      print "pan: " + panstr
        # string = "echo 0=" + panstr + "us > /dev/servoblaster"
        # os.system(string)
    oldpan = pan
    # Send tilt value if changed
    if tilt != oldtilt:
        tiltmod = int(tilt * 2)
        try:
            pi.i2c_write_device(bus, [0x03, (tiltmod & 0xFF00) >> 8, tiltmod & 0xFF])
        except pigpio.error:
            print "i2c write failed"
        # tilt += (0.9 * 10 ** (-8)) * (tiltAxis * math.fabs(tiltAxis))
        # tilt = max(tiltmin, min(tiltmax, tilt))  # camera case limits
        # #      tilt = max(500, min(2500, tilt))           # servo limits
        # #      print "tilt: " + tiltstr
        # tiltstr = str(int(tilt))
        # string = "echo 1=" + tiltstr + "us > /dev/servoblaster"
        # os.system(string)
    oldtilt = tilt
    sleep(.01)

# Cleanup and shutdown
try:
    pi.i2c_write_device(bus, [0, 0, 0])
except pigpio.error:
    print "i2c write failed"
xboxdrv.send_signal(signal.SIGINT)
print "waiting for xboxdrv to terminate"
xboxdrv.wait()
print "xboxdrv terminated"
pi.stop()
os.system("sudo killall pigpiod")
#os.system("shutdown -h now")
