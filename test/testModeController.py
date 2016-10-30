'''
Created on Oct 29, 2016

@author: Tristan
'''
import unittest
from modeController import ModeController 


class TestModeController(unittest.TestCase):


    def setUp(self):
        self.modeController = ModeController()


    def tearDown(self):
        pass


    def testSwitchFromRunningToSlideLimitSetup(self):
        self.modeController.mode = "Running"
        self.modeController.handleButtonEvents(
            {'StartBtn':True, 'BackBtn':False, 'XBtn':True, 'YBtn':False})
        self.assertEqual(self.modeController.mode, "SlideLimitSetup")
        
        
    def testSwitchFromRunningToServoLimitSetup(self):
        self.modeController.mode = "Running"
        self.modeController.handleButtonEvents(
            {'StartBtn':True, 'BackBtn':False, 'XBtn':False, 'YBtn':True})
        self.assertEqual(self.modeController.mode, "ServoLimitSetup")
        
        
    def testSimultaneousButtonPresses(self):
        self.modeController.mode = "Running"
        self.modeController.handleButtonEvents(
            {'StartBtn':True, 'BackBtn':False, 'XBtn':True, 'YBtn':True})
        self.assertEqual(self.modeController.mode, "Running")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()