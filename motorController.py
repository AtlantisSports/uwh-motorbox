'''
Created on February 10, 2017 

@author: Tristan
'''

import configparser

class MotorController():
    '''
    controls the slide motor, including acceleration limits
    '''


    def __init__(self, pi, configFile):
        '''
        Constructor

        Arguments:         pi: a pigpio.pi object to set the PWM for the slide motor
                   configFile: the .ini file to read config from
        '''
        
        self.pi = pi

        config = configparser.ConfigParser()
        config.read(configFile)

        self.maxAcc = config['Options'].getfloat('maxAccel')
        self.maxDec = config['Options'].getfloat('maxAccel')
        self.spLim = config['Options'].getfloat('maxAccel')
        self.spLimZoneSize = config['Options'].getfloat('maxAccel')
        self.gpio = config['Setup'].getint('slideGpio')
        
        # Import encoder


