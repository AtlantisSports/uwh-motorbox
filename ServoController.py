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
            print("pancenter: ", pancenter, "tiltcenter: ", tiltcenter, "radius: ", 
                    radius, "tiltmin: ", tiltmin)
            self.limitsSet = True
        # If file cannot be found, set servo limits
        except IOError:
            print("ServoLimitData.pkl does not exist, entering servo limit setup mode")
            self.panCenter = None
            self.tiltCenter = None
            self.radius = None
            self.tiltMin = None
            self.limitsSet = False

        self.pan = 1500.
        self.tilt = 1500.
        self.oldPan = self.pan
        self.oldTilt = self.tilt
        self.setPan()
        self.setTilt()


    def move(self, panChange, tiltChange, ignoreLimits = False):
        '''
        Moves the servos. If limitsSet is true, and ignoreLimits is false,
        calles applyLimits
        '''
        
        self.pan -= (7.5 * 10 ** (-9)) * (panChange * math.fabs(panChange))
        self.tilt += (4.5 * 10 ** (-9)) * (tiltChange * math.fabs(tiltChange))
        
        if self.limitsSet and not ignoreLimits:
            self.applyLimits
     
        if self.oldPan != self.pan:
            self.setPan()

        if self.oldTilt != self.tilt:
            self.setTilt()



    def setPan(self, position = None):
        '''
        Sets the PWM of the pan servo
        '''
        dutycycle = min(125000, max(25000, int((position if position!=None else self.pan) * 50)))
        #print "Setting pan dutycycle to " + str(dutycycle)
        self.pi.hardware_PWM(self.panGpio, 50, dutycycle)
        return
        
        
    def setTilt(self, position = None):
        '''
        Sets the PWM of the tilt servo
        '''
        dutycycle = min(125000, max(25000, int((position if position!=None else self.tilt) * 50)))
        #print "Setting tilt dutycycle to " + str(dutycycle)
        self.pi.hardware_PWM(self.tiltGpio, 50, dutycycle)
        return


    def applyLimits(self):
        '''
        Applies the limits to self.tilt and self.pan
        '''
        if self.tilt < self.tiltMin:
            self.tilt = self.tiltMin
        vector = np.array([self.pan - self.panCenter, self.tilt - self.tiltCenter])
        norm = np.linalg.norm(vector)
        if norm > self.radius:
            vector = np.multiply(vector, (self.radius / norm))
            self.pan = self.panCenter + vector[0]
            self.tilt = self.tiltCenter + vector[1]


    def setLimit(self):
        '''
        Sets the lowest indexed limit to the current position.
        If all three are set, uses current tilt position to set
        tiltMin, then computes the limit data and resets
        limit1 through limit3.
        '''
        if self.limit1 == None:
            self.limit1 = [self.pan, self.tilt]
            print("limit1 set to ", self.limit1)
        elif self.limit2 == None:
            self.limit2 = [self.pan, self.tilt]
            print("limit2 set to ", limit2)
        elif self.limit3 == None:
            limit3 = [panpos, tiltpos]
            print("limit3 set to ", limit3)
        else:
            tiltMin = self.tilt
            d = 2 * (self.limit1[0] * (self.limit2[1] - self.limit3[1]) + self.limit2[0]
                        * (self.limit3[1] - self.limit1[1]) + self.limit3[0]
                        * (self.limit1[1] - self.limit2[1]))
            pancenter = ((self.limit1[0] ** 2 + self.limit1[1] ** 2)
                        * (self.limit2[1] - self.limit3[1]) + (self.limit2[0] ** 2
                        + self.limit2[1] ** 2) * (self.limit3[1] - self.limit1[1])
                        + (self.limit3[0] ** 2 + self.limit3[1] ** 2)
                        * (self.limit1[1] - self.limit2[1])) / d
            tiltcenter = ((self.limit1[0] ** 2 + self.limit1[1] ** 2)
                        * (self.limit3[0] - self.limit2[0]) + (self.limit2[0] ** 2
                        + self.limit2[1] ** 2) * (self.limit1[0] - self.limit3[0])
                        + (self.limit3[0] ** 2 + self.limit3[1] ** 2)
                        * (self.limit2[0] - self.limit1[0])) / d
            radius = math.sqrt((self.limit1[0] - self.panCenter)**2
                        + (self.limit1[1] - self.tiltCenter) ** 2)

            datatosave = [pancenter, tiltcenter, radius, tiltmin]
            output = open('ServoLimitData.pkl', 'w')
            pickle.dump(datatosave, output)
            output.close()

            self.limit1 = None
            self.limit2 = None
            self.limit3 = None

