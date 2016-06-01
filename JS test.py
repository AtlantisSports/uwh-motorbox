from evdev import InputDevice, categorize, ecodes, list_devices
from time import sleep

devices = [InputDevice(fn) for fn in list_devices()]
for dev in devices:
    if dev.name == 'Xbox Gamepad (userspace driver)':
        JS = InputDevice(dev.fn)
        break
JS.grab()

JSstatus = dict(backBtn = False, startBtn = False, aBtn = False, bBtn = False, xBtn = False, yBtn = False, panAxis = 0., tiltAxis = 0., slideAxis = 0., slideDir = 1)

while True:
    JSevents = JS.read()
    try:
        for event in JSevents:
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    JSstatus['panAxis'] = event.value
                elif event.code == ecodes.ABS_Y:
                    JSstatus['tiltAxis'] = event.value
                elif event.code == ecodes.ABS_Z:
                    JSstatus['slideAxis'] = event.value * JSstatus['slideDir']
            elif event.type == ecodes.EV_KEY:
                if event.value == True:
                    if event.code == ecodes.BTN_SELECT:
                        JSstatus['backBtn'] = True
                    elif event.code == ecodes.BTN_START:
                        JSstatus['startBtn'] = True
                    elif event.code == ecodes.BTN_A:
                        JSstatus['aBtn'] = True
                    elif event.code == ecodes.BTN_B:
                        JSstatus['bBtn'] = True
                    elif event.code == ecodes.BTN_X:
                        JSstatus['xBtn'] = True
                    elif event.code == ecodes.BTN_Y:
                        JSstatus['yBtn'] = True
                elif event.value == False:
                    if event.code == ecodes.BTN_SELECT:
                        JSstatus['backBtn'] = False
                    elif event.code == ecodes.BTN_START:
                        JSstatus['startBtn'] = False
                    elif event.code == ecodes.BTN_A:
                        JSstatus['aBtn'] = False
                    elif event.code == ecodes.BTN_B:
                        JSstatus['bBtn'] = False
                    elif event.code == ecodes.BTN_X:
                        JSstatus['xBtn'] = False
                    elif event.code == ecodes.BTN_Y:
                        JSstatus['yBtn'] = False
    except IOError:
        pass
            
    print "backBtn: " + str(JSstatus['backBtn'])
    print "startBtn: " + str(JSstatus['startBtn'])
    print "aBtn: " + str(JSstatus['aBtn'])
    print "bBtn: " + str(JSstatus['bBtn'])
    print "xBtn: " + str(JSstatus['xBtn'])
    print "yBtn: " + str(JSstatus['yBtn'])
    print "panAxis: " + str(JSstatus['panAxis'])
    print "tiltAxis: " + str(JSstatus['tiltAxis'])
    print "slideAxis: " + str(JSstatus['slideAxis'])
    
    sleep(1)