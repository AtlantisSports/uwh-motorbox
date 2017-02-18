'''
Created on February 10, 2017 

@author: Tristan
'''

import configparser
import encoder
import math
import pigpio

class MotorController():
    '''
    controls the slide motor, including acceleration limits and end limits
    '''
    
    useEndLimits = True; # When True, enables end stop limits
    
    def __init__(self, pi, configFile):
        '''
        Constructor

        Arguments:         pi: a pigpio.pi object used to set the PWM output
                   configFile: the .ini file to read config from
        '''
        
        self.pi = pi

        config = configparser.ConfigParser()
        config.read(configFile)

        self.maxAccel = config['Options'].getfloat('maxAccel')
        self.maxDecel = config['Options'].getfloat('maxDecel')
        self.speedLimit = config['Options'].getfloat('speedLimit')
        self.speedLimitZoneSize = config['Options'].getfloat('speedLimitZoneSize')
        self.gpio = config['Setup'].getint('slideGpio')
        
        self.encoder = encoder.Encoder(pi, configFile)

        self.pi.set_PWM_frequency(self.slideGpio, 50)
        self.pi.set_PWM_range(self.slideGpio, 10000)
        self.pi.set_PWM_dutycycle(self.slideGpio, 750)

        self.limit1 = None
        slef.limit2 = None
        self.upperLimit = None
        self.lowerLimit = None

        self.direction = 1  # Switches between 1 and -1 to switch deirections
        self.speed = 0
        self.oldSpeed = 0
        self.targetSpeed = 0

    
    def setSpeed(self, targetSpeed):
        '''
        Sets the target speed of the motor, then calls update() to update
        the actual speed according to end limits and acceleration limits
        '''
        self.targetSpeed = targetSpeed
        self.update()


    def update(self):
        '''
        Sets the speed of the motor based on the target speed and
        acceleration limits and end stops (if enabled)
        '''

        self.encoderCount = self.encoder.getEncoderCount()

        if useEndLimits and self.upperLimit != None and self.lowerLimit != None:
            if self.targetSpeed < 0 and self.encoderCount > (self.upperLimit - self.speedLimitZoneSize):
                if self.encoderCount > self.upperLimit:
                    self.targetSpeed = 0
                elif self.targetSpeed < -self.speedLimit:
                    self.targetSpeed = -self.speedLimit
            if self.targetSpeed > 0 and self.encoderCount < (self.lowerLimit + self.speedLimitZoneSize):
                if self.encoderCount < self.lowerLimit:
                    self.targetSpeed = 0
                elif self.speed > self.speedLimit:
                    self.targetSpeed = self.speedLimit

        # Limit speed change
        if math.fabs(self.targetSpeed) > math.fabs(self.oldSpeed):
            if math.fabs(self.targetSpeed - self.oldSpeed) > self.maxAccel:
                if self.targetSpeed > self.oldSpeed:
                    self.speed = self.oldSpeed + self.maxAccel
                else:
                    self.speed = self.oldSpeed - self.maxAccel
            else:
                    self.speed = self.targetSpeed
        else:
            if math.fabs(self.targetSpeed - self.oldSpeed) > self.maxDecel:
                if self.targetSpeed > self.oldSpeed:
                    self.speed = self.oldSpeed + self.maxDecel
                else:
                    self.speed = self.oldSpeed - self.maxDecel
            else:
                self.speed = self.targetSpeed

        self.setPWM()

        
    def setPWM(self, speed = None):
        '''
        Changes the PWM output so the motor goes at self.speed
        '''
        dutycycle = min(9500, max(9000, 9250 + (speed if speed!=None else self.speed)/2))
        #print "Setting slide dutycycle to " + str(dutycycle)
        self.pi.set_PWM_dutycycle(self.slideGpio, dutycycle)


    def softStop(self):
        '''
        Brings the motor to a deceleration limited stop
        '''
        self.targetSpeed = 0

        while self.speed != 0:
            self.update()
            sleep(0.01)


    def hardStop(self):
        '''
        Brings the motor to an immediate stop
        '''
        self.targetSpeed = 0
        self.oldSpeed = 0
        self.speed = 0

        self.setPWM()
        
    
    def setLimit(self):
        '''
        Sets either limit1 or limit2 to the current encoder count.
        If limit1 and limit2 are !=0, sets upperLimit and lowerLimit
        to limit1 and limit2 appropriately, then resets limit1 and
        limit2 to 0.
        '''
        self.encoderCount = self.encoder.getEncoderCount()

        if self.limit1 == None:
            self.limit1 = self.encoderCount
            print("limit1 set to: ", limit1)
        else:
            self.limit2 = self.encoderCount
            print("limit2 set to: ", limit2)
            self.upperLimit = max(self.limit1, self.limit2)
            self.lowerLimit = min(self.limit1, self.limit2)
            self.limit1 = 0
            self.limit2 = 0

