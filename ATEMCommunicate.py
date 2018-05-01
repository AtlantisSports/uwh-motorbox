'''
Created on Feb 20, 2018

@author: Tristan Debrunner

Communicates with the ATEM and sneds commands to switch cameras
when strings are recieved on stdin.
'''

import sys
import select
import configparser
from ATEMControl import Atem

configFile = "config.ini"

config = configparser.ConfigParser()
config.read(configFile)
ATEMAddress = config['Options'].getstring('ATEMAddress')

a = Atem()
a.connectToSwitcher((ATEMAddress, 9910))

a.waitForPacket()
a.waitForPacket()
a.waitForPacket()
a.waitForPacket()

while(True):
    a.waitForPacket()
    ready = select.select([sys.stdin], [], [], 0)[0]
    if ready:
        cmd = sys.stdin.readline()
        if cmd == "CAM1":
            a.sendCommand("CPgI", "\x00\x00\x00\x01")
        elif cmd == "CAM2":
            a.sendCommand("CPgI", "\x00\x00\x00\x02")
        else:
            print("Recieved invalid command: {s}".format(cmd))
