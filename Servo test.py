import pigpio
import os

panServoGpio = 12  # This corresponds to pin 32
tiltServoGpio = 13  # This corresponds to pin 33

os.system('sudo pigpiod')
pi = pigpio.pi()
pi.hardware_PWM(panServoGpio, 50, 75000)
pi.hardware_PWM(tiltServoGpio, 50, 75000)

def setPanPos(pi, position):
    dutycycle = min(125000, max(25000, int(position * 50)))
    print "Setting pan dutycycle to " + str(dutycycle)
    pi.hardware_PWM(panServoGpio, 50, dutycycle)
    return
    
    
def setTiltPos(pi, position):
    dutycycle = min(112500, max(65000, int(position * 50)))
    print "Setting tilt dutycycle to " + str(dutycycle)
    pi.hardware_PWM(tiltServoGpio, 50, dutycycle)
    return
    
done = False
while not done:
    user = input("Enter 1 to set pan, 2 to set tilt, 999 to quit: ")
    if user == 1:
        position = input("Enter position to send to pan")
        setPanPos(pi, position)
    elif user == 2:
        position = input("Enter position to send to tilt")
        setTiltPos(pi, position)
    elif user == 999:
        done = True
        print "Quitting..."
        
os.system('sudo killall pigpiod')