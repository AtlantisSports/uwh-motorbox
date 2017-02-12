'''
Created on February 10, 2017 

@author: Tristan
'''

import configparser
import encoder
import pigpio
import math
import numpy as np
import pickle

class ServoController():
    '''
    Controls the servo motors and limits their motion to a circle in the
    pan-tilt plane.
    '''

    def __init__(self, pi, configFile):
        '''
        Constructor

        Arguments:         pi: a pigpio.pi object used to set the PWM output
                   configFile: the .ini file to read config from
        '''
        
        self.pi = pi

        config = configparser.ConfigParser()
        config.read(configFile)
        
        self.panGpio = config['Setup'].getint('panServoGpio')
        self.tiltGpio = config['Setup'].getint('tileServoGpio')

        self.pi.hardware_PWM(self.panGpio, 50, 75000)
        self.pi.hardware_PWM(self.tiltGpio, 50, 75000)
        
        # Read servo limit info from file
        try:
            pklFile = open('ServoLimitData.pkl', 'r')
            inputdata = pickle.load(pklFile)
            pklFile.close()
            self.panCenter = inputdata[0]
            self.tiltCenter = inputdata[1]
            radius = inputdata[2]
            tiltMin = inputdata[3]
            print("pancenter: ", pancenter, "tiltcenter: ", tiltcenter, "radius: ", radius, "tiltmin: ", tiltmin)
            self.limitsSet = True
        # If file cannot be found, set servo limits
        except IOError:
            print "ServoLimitData.pkl does not exist, entering servo limit setup mode"
            self.limitsSet = False


    def move(self, panChange, tiltChange):
        '''
        Moves the servos. If limits are set, 
