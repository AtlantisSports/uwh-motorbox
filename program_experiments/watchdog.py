from evdev import InputDevice, list_devices
from time import sleep

normal = True

while normal:
    devices = [InputDevice(fn) for fn in list_devices()]
    for dev in devices:
        if dev.name == 'Xbox Gamepad (userspace driver)':
            print "found xbox"
    sleep(.5)