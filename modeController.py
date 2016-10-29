'''
Created on Oct 29, 2016

@author: Tristan
'''

import os

class ModeController():
    '''
    Handles mode tracking for the motor box
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.mode = "SlideLimitSetup"
    
    
    def handleButtonEvents(self, JSStatus):
        '''
        Checks if the mode should be switched based on button statuses
        '''
        if self.mode == "Running":
            if JSStatus['StartBtn'] and JSStatus['XBtn']:
                self.mode = "SlideLimitSetup"
            elif JSStatus['StartBtn'] and JSStatus['YBtn']:
                self.mode = "ServoLimitSetup"
        
        if JSStatus['StartBtn'] and JSStatus['BackBtn']:
            os.system('sudo shutdown now')