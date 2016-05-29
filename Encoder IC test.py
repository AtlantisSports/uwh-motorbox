import pigpio
import os
from time import sleep

d0gpio = 4  # This corresponds to pin 7
d1gpio = 17  # This corresponds to pin 11
d2gpio = 27  # This corresponds to pin 13
d3gpio = 22  # This corresponds to pin 15
d4gpio = 10  # This corresponds to pin 19
d5gpio = 9  # This corresponds to pin 21
d6gpio = 11  # This corresponds to pin 23
d7gpio = 5  # This corresponds to pin 29
clkGpio = 6  # This corresponds to pin 31
rstGpio = 25  # This corresponds to pin 22
oeGpio = 24  # This corresponds to pin 18
sel1gpio = 18  # This corresponds to pin 12
sel2gpio = 23  # This corresponds to pin 16

os.system("sudo pigpiod")
sleep(2)  # Wait for pigpiod to start
pi = pigpio.pi()
pi.set_mode(d0gpio, pigpio.INPUT)
pi.set_mode(d1gpio, pigpio.INPUT)
pi.set_mode(d2gpio, pigpio.INPUT)
pi.set_mode(d3gpio, pigpio.INPUT)
pi.set_mode(d4gpio, pigpio.INPUT)
pi.set_mode(d5gpio, pigpio.INPUT)
pi.set_mode(d6gpio, pigpio.INPUT)
pi.set_mode(d7gpio, pigpio.INPUT)
pi.set_pull_up_down(d0gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d1gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d2gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d3gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d4gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d5gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d6gpio, pigpio.PUD_UP)
pi.set_pull_up_down(d7gpio, pigpio.PUD_UP)
pi.set_mode(rstGpio, pigpio.OUTPUT)
pi.set_mode(oeGpio, pigpio.OUTPUT)
pi.set_mode(sel1gpio, pigpio.OUTPUT)
pi.set_mode(sel2gpio, pigpio.OUTPUT)
pi.write(rstGpio, 1)
pi.write(oeGpio, 1)
pi.write(sel1gpio, 0)
pi.write(sel2gpio, 1)
pi.hardware_clock(clkGpio, 30000000)

done = False

while not done:
    person = input("Enter 999 to quit: ")
    if person == 999:
        print "Quitting"
        done = True
    else:
        count = 0
        pi.write(sel1gpio, 0)
        pi.write(sel2gpio, 1)
        pi.write(oeGpio, 0)
        sleep(0.000000035)
        count += pi.read(d7gpio)
        count *= 2
        count += pi.read(d6gpio)
        count *= 2
        count += pi.read(d5gpio)
        count *= 2
        count += pi.read(d4gpio)
        count *= 2
        count += pi.read(d3gpio)
        count *= 2
        count += pi.read(d2gpio)
        count *= 2
        count += pi.read(d1gpio)
        count *= 2
        count += pi.read(d0gpio)
        count *= 2
        pi.write(sel1gpio, 1)
        sleep(0.000000035)
        count += pi.read(d7gpio)
        count *= 2
        count += pi.read(d6gpio)
        count *= 2
        count += pi.read(d5gpio)
        count *= 2
        count += pi.read(d4gpio)
        count *= 2
        count += pi.read(d3gpio)
        count *= 2
        count += pi.read(d2gpio)
        count *= 2
        count += pi.read(d1gpio)
        count *= 2
        count += pi.read(d0gpio)
        count *= 2
        pi.write(sel1gpio, 0)
        pi.write(sel2gpio, 0)
        sleep(0.000000035)
        count += pi.read(d7gpio)
        count *= 2
        count += pi.read(d6gpio)
        count *= 2
        count += pi.read(d5gpio)
        count *= 2
        count += pi.read(d4gpio)
        count *= 2
        count += pi.read(d3gpio)
        count *= 2
        count += pi.read(d2gpio)
        count *= 2
        count += pi.read(d1gpio)
        count *= 2
        count += pi.read(d0gpio)
        count *= 2
        pi.write(sel1gpio, 1)
        sleep(0.000000035)
        count += pi.read(d7gpio)
        count *= 2
        count += pi.read(d6gpio)
        count *= 2
        count += pi.read(d5gpio)
        count *= 2
        count += pi.read(d4gpio)
        count *= 2
        count += pi.read(d3gpio)
        count *= 2
        count += pi.read(d2gpio)
        count *= 2
        count += pi.read(d1gpio)
        count *= 2
        count += pi.read(d0gpio)
        count *= 2
        pi.write(sel1gpio, 0)
        pi.write(sel2gpio, 1)
        pi.write(oeGpio, 1)
        
        print "Current count is " + str(count)

pi.stop()
os.system("sudo killall pigpiod")