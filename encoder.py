'''
Created on February 10, 2017 

@author: Tristan
'''

import pigpio
import configparser
from time import sleep


class Encoder():
    '''
    Interfaces with the HCTL-2022 encoder counter IC to get and set the encoder count
    '''


    def __init__(self, pi, configFile):
        '''
        Constructor

        Arguments:         pi: a pigpio.pi object used to control gpio's
                   configFile: the .ini file to read config from
        '''

        self.pi = pi

        config = configparser.ConfigParser()
        config.read(configFile)

        self.d0gpio = config['Setup'].getint('d0gpio')
        self.d1gpio = config['Setup'].getint('d1gpio')
        self.d2gpio = config['Setup'].getint('d2gpio')
        self.d3gpio = config['Setup'].getint('d3gpio')
        self.d4gpio = config['Setup'].getint('d4gpio')
        self.d5gpio = config['Setup'].getint('d5gpio')
        self.d6gpio = config['Setup'].getint('d6gpio')
        self.d7gpio = config['Setup'].getint('d7gpio')
        self.clkGpio = config['Setup'].getint('clkGpio')
        self.rstGpio = config['Setup'].getint('rstGpio')
        self.oeGpio = config['Setup'].getint('oeGpio')
        self.sel1gpio = config['Setup'].getint('sel1gpio')
        self.sel2gpio = config['Setup'].getint('sel2gpio')

        self.pi.set_mode(self.d0gpio, pigpio.INPUT)
        self.pi.set_mode(self.d1gpio, pigpio.INPUT)
        self.pi.set_mode(self.d2gpio, pigpio.INPUT)
        self.pi.set_mode(self.d3gpio, pigpio.INPUT)
        self.pi.set_mode(self.d4gpio, pigpio.INPUT)
        self.pi.set_mode(self.d5gpio, pigpio.INPUT)
        self.pi.set_mode(self.d6gpio, pigpio.INPUT)
        self.pi.set_mode(self.d7gpio, pigpio.INPUT)
        self.pi.set_pull_up_down(self.d0gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d1gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d2gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d3gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d4gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d5gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d6gpio, pigpio.PUD_UP)
        self.pi.set_pull_up_down(self.d7gpio, pigpio.PUD_UP)
        self.pi.set_mode(self.rstGpio, pigpio.OUTPUT)
        self.pi.set_mode(self.oeGpio, pigpio.OUTPUT)
        self.pi.set_mode(self.sel1gpio, pigpio.OUTPUT)
        self.pi.set_mode(self.sel2gpio, pigpio.OUTPUT)

        self.resetEncoderCount()
        self.pi.write(self.oeGpio, 1)
        self.pi.write(self.sel1gpio, 0)
        self.pi.write(self.sel2gpio, 1)

        self.pi.hardware_clock(self.clkGpio, 30000000)


    def resetEncoderCount(self):
        self.pi.write(self.rstGpio, 0)
        sleep(0.000000035)
        self.pi.write(self.rstGpio, 1)


    def getEncoderCount(self):
        self.count = 0
        self.pi.write(self.sel1gpio, 0)
        self.pi.write(self.sel2gpio, 1)
        self.pi.write(self.oeGpio, 0)
        sleep(0.000000035)
        self.count -= self.pi.read(self.d7gpio)
        self.count *= 2
        self.count += self.pi.read(self.d6gpio)
        self.count *= 2
        self.count += self.pi.read(self.d5gpio)
        self.count *= 2
        self.count += self.pi.read(self.d4gpio)
        self.count *= 2
        self.count += self.pi.read(self.d3gpio)
        self.count *= 2
        self.count += self.pi.read(self.d2gpio)
        self.count *= 2
        self.count += self.pi.read(self.d1gpio)
        self.count *= 2
        self.count += self.pi.read(self.d0gpio)
        self.count *= 2
        self.pi.write(self.sel1gpio, 1)
        sleep(0.000000035)
        self.count += self.pi.read(self.d7gpio)
        self.count *= 2
        self.count += self.pi.read(self.d6gpio)
        self.count *= 2
        self.count += self.pi.read(self.d5gpio)
        self.count *= 2
        self.count += self.pi.read(self.d4gpio)
        self.count *= 2
        self.count += self.pi.read(self.d3gpio)
        self.count *= 2
        self.count += self.pi.read(self.d2gpio)
        self.count *= 2
        self.count += self.pi.read(self.d1gpio)
        self.count *= 2
        self.count += self.pi.read(self.d0gpio)
        self.count *= 2
        self.pi.write(self.sel1gpio, 0)
        self.pi.write(self.sel2gpio, 0)
        sleep(0.000000035)
        self.count += self.pi.read(self.d7gpio)
        self.count *= 2
        self.count += self.pi.read(self.d6gpio)
        self.count *= 2
        self.count += self.pi.read(self.d5gpio)
        self.count *= 2
        self.count += self.pi.read(self.d4gpio)
        self.count *= 2
        self.count += self.pi.read(self.d3gpio)
        self.count *= 2
        self.count += self.pi.read(self.d2gpio)
        self.count *= 2
        self.count += self.pi.read(self.d1gpio)
        self.count *= 2
        self.count += self.pi.read(self.d0gpio)
        self.count *= 2
        self.pi.write(self.sel1gpio, 1)
        sleep(0.000000035)
        self.count += self.pi.read(self.d7gpio)
        self.count *= 2
        self.count += self.pi.read(self.d6gpio)
        self.count *= 2
        self.count += self.pi.read(self.d5gpio)
        self.count *= 2
        self.count += self.pi.read(self.d4gpio)
        self.count *= 2
        self.count += self.pi.read(self.d3gpio)
        self.count *= 2
        self.count += self.pi.read(self.d2gpio)
        self.count *= 2
        self.count += self.pi.read(self.d1gpio)
        self.count *= 2
        self.count += self.pi.read(self.d0gpio)
        self.pi.write(self.sel1gpio, 0)
        self.pi.write(self.sel2gpio, 1)
        self.pi.write(self.oeGpio, 1)
        
        #print "Current count is " + str(self.count)
        return self.count

