import pigpio
import os
from time import sleep

slideGpio = 7  # This corresponds to pin 26

os.system("sudo pigpiod")
sleep(2)  # Wait for pigpiod to start
pi = pigpio.pi()

pi.set_PWM_frequency(slideGpio, 50)
pi.set_PWM_range(slideGpio, 10000)
pi.set_PWM_dutycycle(slideGpio, 9250)

sleep(2)
pi.set_PWM_dutycycle(slideGpio, 9300)

sleep(2)
pi.set_PWM_dutycycle(slideGpio, 9250)

sleep(2)
pi.set_PWM_dutycycle(slideGpio, 0)

pi.stop()
os.system("sudo killall pigpiod")