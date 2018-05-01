
import os
import joyStick
import subprocess
import shlex
from time import sleep

# Start xboxdrv
xboxdrv = subprocess.Popen(shlex.split("sudo xboxdrv -c /home/pi/uwh-motorbox/xboxdrvconfig.ini"))
print("xboxdrv started")

JS = joyStick.JoyStick()

while True:
    JS.update()
    print('pan: {}   tilt: {}   slide: {}'.format(JS.panAxis, JS.tiltAxis, JS.slideAxis))
    sleep(0.1)
