from multiprocessing import Process


ATEMAddress = '192.168.10.10'

def motorControlLoop():
    from evdev import InputDevice, categorize, ecodes, list_devices
    from time import sleep
    import time
    import pigpio
    import os
    import subprocess
    import signal
    import shlex
    import math
    import numpy as np
    import pickle

    # Options
    maxaccel = 2.5
    maxdecel = 40
    speedLimit = 500  # Motor speed limit near soft limits
    speedLimitZoneSize = 12800  # Measured in encoder pulses

    # Setup
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
    panServoGpio = 12  # This corresponds to pin 32
    tiltServoGpio = 13  # This corresponds to pin 33
    slideGpio = 7  # This corresponds to pin 26


    def setSlideLimits(pi, JS, JSstatus):
        print "Entering slide limit set mode"
        done = False
        oldslideAxis = 0.
        limit1 = 0
        limit2 = 0
        while not done:
            # Get events from evdev
            JSstatus = getJSEvents(JS, JSstatus)
            # Send the new slide speed if changed
            if JSstatus['slideAxis'] != oldslideAxis:
                setSlideSpeed(pi, JSstatus['slideAxis'])
            oldslideAxis = JSstatus['slideAxis']
            # Set a limit if the Y button is pressed
            if JSstatus['yBtn']:
                if limit1 == 0:
                    limit1 = getEncoderCount(pi)
                    JSstatus['yBtn'] = False
                    print "limit1 set to: " + str(limit1)
                else:  # If the first limit is already set, set the second, save to global variables, and exit
                    limit2 = getEncoderCount(pi)
                    print "limit2 set to: " + str(limit2)
                    upperSlideLimit = max(limit1, limit2)
                    lowerSlideLimit = min(limit1, limit2)
                    JSstatus['yBtn'] = False
                    done = True
            if JSstatus['startBtn'] and JSstatus['xBtn']:
                print "Switching slide direction"
                JSstatus['slideDir'] *= -1
                JSstatus['startBtn'] = False
                JSstatus['xBtn'] = False
            sleep(0.01)
        print "Exiting slide limit set mode"
        return JSstatus, upperSlideLimit, lowerSlideLimit


    def setServoLimits(pi, JS, JSstatus):
        print "Entering servo limit set mode"
        limit1 = 0
        limit2 = 0
        limit3 = 0
        panpos = 1500.
        tiltpos = 1500.
        setPanPos(pi, panpos)
        setTiltPos(pi, tiltpos)
        done = False
        while not done:
            # Get events from evdev
            JSstatus = getJSEvents(JS, JSstatus)
            if JSstatus['yBtn']:
                if limit1 == 0:
                    limit1 = [panpos, tiltpos]
                    print "limit1 set to " + str(limit1)
                    JSstatus['yBtn'] = False
                elif limit2 == 0:
                    limit2 = [panpos, tiltpos]
                    print "limit2 set to " + str(limit2)
                    JSstatus['yBtn'] = False
                elif limit3 == 0:
                    limit3 = [panpos, tiltpos]
                    print "limit3 set to " + str(limit3)
                    JSstatus['yBtn'] = False
                else:
                    tiltmin = tiltpos
                    d = 2 * (limit1[0] * (limit2[1] - limit3[1]) + limit2[0] * (limit3[1] - limit1[1]) + limit3[0] * (limit1[1] - limit2[1]))
                    pancenter = ((limit1[0] ** 2 + limit1[1] ** 2) * (limit2[1] - limit3[1]) + (limit2[0] ** 2 + limit2[1] ** 2) * (limit3[1] - limit1[1]) + (limit3[0] ** 2 + limit3[1] ** 2) * (limit1[1] - limit2[1])) / d
                    tiltcenter = ((limit1[0] ** 2 + limit1[1] ** 2) * (limit3[0] - limit2[0]) + (limit2[0] ** 2 + limit2[1] ** 2) * (limit1[0] - limit3[0]) + (limit3[0] ** 2 + limit3[1] ** 2) * (limit2[0] - limit1[0])) / d
                    radius = math.sqrt((limit1[0] - pancenter)**2 + (limit1[1] - tiltcenter)**2)
                    JSstatus['yBtn'] = False
                    done = True
            if JSstatus['panAxis'] != 0:
                panpos -= (1.5 * 10 ** (-8)) * (JSstatus['panAxis'] * math.fabs(JSstatus['panAxis']))
                setPanPos(pi, panpos)
            if JSstatus['tiltAxis'] != 0:
                tiltpos += (0.9 * 10 ** (-8)) * (JSstatus['tiltAxis'] * math.fabs(JSstatus['tiltAxis']))
                setTiltPos(pi, tiltpos)
        print "Center coordinates: " + str(pancenter) + "," + str(tiltcenter)
        print "Radius: " + str(radius)
        print "tiltmin: " + str(tiltmin)
        datatosave = [pancenter, tiltcenter, radius, tiltmin]
        output = open('ServoLimitData.pkl', 'w')
        pickle.dump(datatosave, output)
        output.close()
        print "Exiting servo limit set mode"
        return JSstatus, pancenter, tiltcenter, radius, tiltmin


    def getJSEvents(JS, JSstatus):
        JSevents = JS.read()
        try:
            for event in JSevents:
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X:
                        JSstatus['panAxis'] = event.value
                    elif event.code == ecodes.ABS_Y:
                        JSstatus['tiltAxis'] = event.value
                    elif event.code == ecodes.ABS_Z:
                        JSstatus['slideAxis'] = event.value * JSstatus['slideDir']
                elif event.type == ecodes.EV_KEY:
                    if event.value == True:
                        if event.code == ecodes.BTN_SELECT:
                            JSstatus['backBtn'] = True
                        elif event.code == ecodes.BTN_START:
                            JSstatus['startBtn'] = True
                        elif event.code == ecodes.BTN_A:
                            JSstatus['aBtn'] = True
                        elif event.code == ecodes.BTN_B:
                            JSstatus['bBtn'] = True
                        elif event.code == ecodes.BTN_X:
                            JSstatus['xBtn'] = True
                        elif event.code == ecodes.BTN_Y:
                            JSstatus['yBtn'] = True
                    elif event.value == False:
                        if event.code == ecodes.BTN_SELECT:
                            JSstatus['backBtn'] = False
                        elif event.code == ecodes.BTN_START:
                            JSstatus['startBtn'] = False
                        elif event.code == ecodes.BTN_A:
                            JSstatus['aBtn'] = False
                        elif event.code == ecodes.BTN_B:
                            JSstatus['bBtn'] = False
                        elif event.code == ecodes.BTN_X:
                            JSstatus['xBtn'] = False
                        elif event.code == ecodes.BTN_Y:
                            JSstatus['yBtn'] = False
        except IOError:
            pass

        return JSstatus


    def setSlideSpeed(pi, speed):
        dutycycle = min(9500, max(9000, 9250 + speed))
        pi.set_PWM_dutycycle(slideGpio, dutycycle)
        return


    def setPanPos(pi, position):
        dutycycle = min(125000, max(25000, int(position * 50)))
        pi.hardware_PWM(panServoGpio, 50, dutycycle)
        return
        
        
    def setTiltPos(pi, position):
        dutycycle = min(125000, max(25000, int(position * 50)))
        pi.hardware_PWM(tiltServoGpio, 50, dutycycle)
        return


    def getEncoderCount(pi):
        count = 0
        pi.write(sel1gpio, 0)
        pi.write(sel2gpio, 1)
        pi.write(oeGpio, 0)
        sleep(0.000000035)
        count -= pi.read(d7gpio)
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
        pi.write(sel1gpio, 0)
        pi.write(sel2gpio, 1)
        pi.write(oeGpio, 1)
        
        #print "Current count is " + str(count)
        return count

    # Start pigpio
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
    pi.write(rstGpio, 0)
    sleep(000000035)
    pi.write(rstGpio, 1)
    pi.write(oeGpio, 1)
    pi.write(sel1gpio, 0)
    pi.write(sel2gpio, 1)
    pi.hardware_clock(clkGpio, 30000000)
    pi.hardware_PWM(panServoGpio, 50, 75000)
    pi.hardware_PWM(tiltServoGpio, 50, 75000)
    pi.set_PWM_frequency(slideGpio, 50)
    pi.set_PWM_range(slideGpio, 10000)
    pi.set_PWM_dutycycle(slideGpio, 750)

    # Start xboxdrv
    xboxdrv = subprocess.Popen(shlex.split(
            "sudo xboxdrv --detach-kernel-driver -s --deadzone 15% --trigger-as-zaxis --deadzone-trigger 15% -l 2"))
    sleep(3)

    # Initiate joystick device
    devices = [InputDevice(fn) for fn in list_devices()]
    for dev in devices:
        if dev.name == 'Xbox Gamepad (userspace driver)':
            JS = InputDevice(dev.fn)
            break
    JS.grab()

    # Set variables
    JSstatus = dict(backBtn = False, startBtn = False, aBtn = False, bBtn = False, xBtn = False, yBtn = False, panAxis = 0., tiltAxis = 0., slideAxis = 0., slideDir = 1)
    slideSpeed = 0.
    oldSlideSpeed = slideSpeed
    pan = 1500.
    tilt = 1500.
    oldpan = pan
    oldtilt = tilt
    encoderCount = 0
    direction = 0
    # curTime = 0
    
    # Read servo limit info from file
    try:
        pklfile = open('ServoLimitData.pkl', 'r')
        inputdata = pickle.load(pklfile)
        pklfile.close()
        pancenter = inputdata[0]
        tiltcenter = inputdata[1]
        radius = inputdata[2]
        tiltmin = inputdata[3]
    # If file cannot be found, set servo limits
    except IOError:
        print "ServoLimitData.pkl does not exist, entering servo limit setup mode"
        JSstatus, pancenter, tiltcenter, radius, tiltmin = setServoLimits(pi, JS, JSstatus)

    # Set the slide limits before normal operation
    JSstatus, upperSlideLimit, lowerSlideLimit = setSlideLimits(pi, JS, JSstatus)

    print "Entering Motor Control Loop"

    # -----------Main Program Loop-------------
    while not JSstatus['backBtn'] or not JSstatus['startBtn']:
        # print str(curTime - time.time())
    # Get events from evdev
        JSstatus = getJSEvents(JS, JSstatus)
    # Read the current encoder position from the MCU
        encoderCount = getEncoderCount(pi)
    # Respond to button presses
        if JSstatus['startBtn'] and JSstatus['xBtn']:
            JSstatus['startBtn'] = False
            JSstatus['xBtn'] = False
            JSstatus, upperSlideLimit, lowerSlideLimit = setSlideLimits(pi, JS, JSstatus)
        elif JSstatus['startBtn'] and JSstatus['bBtn']:
            JSstatus['startBtn'] = False
            JSstatus['bBtn'] = False
            JSstatus, pancenter, tiltcenter, radius, tiltmin = setServoLimits(pi, JS, JSstatus)
    # Limit slideSpeed change
        if math.fabs(JSstatus['slideAxis']) > math.fabs(oldSlideSpeed):
            if math.fabs(JSstatus['slideAxis'] - oldSlideSpeed) > maxaccel:
                if JSstatus['slideAxis'] > oldSlideSpeed:
                    slideSpeed = oldSlideSpeed + maxaccel
                else:
                    slideSpeed = oldSlideSpeed - maxaccel
            else:
                    slideSpeed = JSstatus['slideAxis']
        else:
            if math.fabs(JSstatus['slideAxis'] - oldSlideSpeed) > maxdecel:
                if JSstatus['slideAxis'] > oldSlideSpeed:
                    slideSpeed = oldSlideSpeed + maxdecel
                else:
                    slideSpeed = oldSlideSpeed - maxdecel
            else:
                slideSpeed = JSstatus['slideAxis']
        # print "After acceleration/deceleration limit: " + str(slideSpeed)
    # Calculate direction
        if slideSpeed != 0:
            if slideSpeed > 0:
                direction = 1
            else:
                direction = 0
    # Limit slideSpeed to speedLimit near soft stops and to 0 when across soft stops, but respect deceleration limit
        if direction == 0 and encoderCount > (upperSlideLimit - speedLimitZoneSize):
            if encoderCount > upperSlideLimit:
                if slideSpeed >= -maxdecel:  # Beacuse direction is 0, slideSpeed must be <0
                    slideSpeed = 0
                else:
                    slideSpeed += maxdecel
            elif slideSpeed < -speedLimit:  # Beacuse direction is 0, slideSpeed must be <0
                if slideSpeed >= -speedLimit - maxdecel:
                    slideSpeed = -speedLimit
                else:
                    slideSpeed += maxdecel
        if direction == 1 and encoderCount < (lowerSlideLimit + speedLimitZoneSize):
            if encoderCount < lowerSlideLimit:
                if slideSpeed <= maxdecel:  # Beacuse direction is 1, slideSpeed must be >0
                    slideSpeed = 0
                else:
                    slideSpeed -= maxdecel
            elif slideSpeed > speedLimit:  # Beacuse direction is 1, slideSpeed must be >0
                if slideSpeed <= speedLimit + maxdecel:
                    slideSpeed = speedLimit
                else:
                    slideSpeed -= maxdecel
    # Calculate new servo values
        pan -= (1.5 * 10 ** (-9)) * (JSstatus['panAxis'] * math.fabs(JSstatus['panAxis']))
        tilt += (0.9 * 10 ** (-9)) * (JSstatus['tiltAxis'] * math.fabs(JSstatus['tiltAxis']))
    # Limit servos to vertical max and within circle
        if tilt < tiltmin:
            tilt = tiltmin
        vector = np.array([pan - pancenter, tilt - tiltcenter])
        norm = np.linalg.norm(vector)
        if norm > radius:
            vector = np.multiply(vector, (radius / norm))
            pan = pancenter + vector[0]
            tilt = tiltcenter + vector[1]
    # Send frequency of stepper pulses if changed
        if slideSpeed != oldSlideSpeed:
            setSlideSpeed(pi, slideSpeed)
    # Send pan value if changed
        if pan != oldpan:
            setPanPos(pi, pan)
        oldpan = pan
    # Send tilt value if changed
        if tilt != oldtilt:
            setTiltPos(pi, tilt)
        oldtilt = tilt
        sleep(.01)

    # Cleanup and shutdown
    xboxdrv.send_signal(signal.SIGINT)
    print "waiting for xboxdrv to terminate"
    xboxdrv.wait()
    print "xboxdrv terminated"
    pi.stop()
    os.system("sudo killall pigpiod")
    #os.system("shutdown -h now")


def ATEMControlLoop(ATEMAddress):
    import socket
    import struct
    import sys
    
    def dumpHex (buffer) :
        s = ''
        for c in buffer:
            s += hex(ord(c)) + ' '
        print s

    def dumpAscii (buffer) :
        s = ''
        for c in buffer:
            if (ord(c)>=0x20)and(ord(c)<=0x7F):
                s+=c
            else:
                s+='.'
        print s

    # implements communication with atem switcher
    class Atem :

        # size of header data
        SIZE_OF_HEADER = 0x0c

        # packet types
        CMD_NOCOMMAND   = 0x00
        CMD_ACKREQUEST  = 0x01
        CMD_HELLOPACKET = 0x02
        CMD_RESEND      = 0x04
        CMD_UNDEFINED   = 0x08
        CMD_ACK         = 0x10

        # initializes the class
        def __init__ (self) :
            self.socket = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setblocking (0)
            self.socket.bind(('0.0.0.0', 9910))
        
        # hello packet
        def connectToSwitcher (self, address) :
            self.address = address
            self.packetCounter = 0
            self.isInitialized = False
            self.currentUid = 0x1337
            
            datagram = self.createCommandHeader (self.CMD_HELLOPACKET, 8, self.currentUid, 0x0)
            datagram += struct.pack('!I',0x01000000)
            datagram += struct.pack('!I', 0x00)
            self.sendDatagram (datagram)

        # reads packets sent by the switcher
        def handleSocketData (self) :
            # network is 100Mbit/s max, MTU is thus at most 1500
            try :
                d = self.socket.recvfrom (2048)
            except socket.error:
                return False
            datagram, server = d
            print 'received datagram'
            header = self.parseCommandHeader(datagram)
            if header :
                self.currentUid = header['uid']
                
                if header['bitmask'] & self.CMD_HELLOPACKET :
                    print 'not initialized, received HELLOPACKET, sending ACK packet'
                    self.isInitialized = False
                    ackDatagram = self.createCommandHeader (self.CMD_ACK, 0, header['uid'], 0x0)
                    self.sendDatagram (ackDatagram)
                elif self.isInitialized and (header['bitmask'] & self.CMD_ACKREQUEST) :
                    print 'initialized, received ACKREQUEST, sending ACK packet'
                    ackDatagram = self.createCommandHeader (self.CMD_ACK, 0, header['uid'], header['packageId'])
                    self.sendDatagram (ackDatagram)
                
                if ((len(datagram) > (self.SIZE_OF_HEADER + 2)) and (not (header['bitmask'] & self.CMD_HELLOPACKET))) :
                    self.parsePayload (datagram)

            return True        

        def waitForPacket(self):
            print ">>> waiting for packet"
            while (not self.handleSocketData()) :
                pass
            print ">>> packet obtained"

        # generates packet header data
        def createCommandHeader (self, bitmask, payloadSize, uid, ackId) :
            buffer = ''
            packageId = 0

            if (not (bitmask & (self.CMD_HELLOPACKET | self.CMD_ACK))) :
                self.packetCounter+=1
                packageId = self.packetCounter
        
            val = bitmask << 11
            val |= (payloadSize + self.SIZE_OF_HEADER)
            buffer += struct.pack('!H',val)
            buffer += struct.pack('!H',uid)
            buffer += struct.pack('!H',ackId)
            buffer += struct.pack('!I',0)
            buffer += struct.pack('!H',packageId)
            return buffer

        # parses the packet header
        def parseCommandHeader (self, datagram) :
            header = {}

            if (len(datagram)>=self.SIZE_OF_HEADER) :
                header['bitmask'] = struct.unpack('B',datagram[0])[0] >> 3
                header['size'] = struct.unpack('!H',datagram[0:2])[0] & 0x07FF
                header['uid'] = struct.unpack('!H',datagram[2:4])[0]
                header['ackId'] = struct.unpack('!H',datagram[4:6])[0]
                header['packageId']=struct.unpack('!H',datagram[10:12])[0]
                print header
                return header
            return False

        def parsePayload (self, datagram) :
            print 'parsing payload'
            # eat up header
            datagram = datagram[self.SIZE_OF_HEADER:]
            # handle data
            while (len(datagram)>0) :
                size = struct.unpack('!H',datagram[0:2])[0]
                packet = datagram[0:size]
                datagram = datagram[size:]
                # skip size and 2 unknown bytes
                packet = packet[4:]
                ptype = packet[:4]
                payload = packet[4:]
                # find the approporiate function in the class
                method = 'pkt'+ptype    
                if method in dir(self) :
                    func = getattr(self, method)
                    if callable(func) :
                        print method
                        func(payload)
                    else:
                        print 'problem, member '+method+' not callable'
                else :
                    print 'unknown type '+ptype
                    #dumpAscii(payload)

            #sys.exit()

        def sendCommand (self, command, payload) :
            print 'sending command'
            size = len(command) + len(payload) + 4
            dg = self.createCommandHeader (self.CMD_ACKREQUEST, size, self.currentUid, 0)
            dg += struct.pack('!H', size)
            dg += "\x00\x00"
            dg += command
            dg += payload
            dumpHex (dg)    
            self.sendDatagram (dg)

        # sends a datagram to the switcher
        def sendDatagram (self, datagram) :
            print 'sending packet'
            dumpHex(datagram)
            self.socket.sendto (datagram, self.address)


        #
        # handling of subpackets
        
        def pkt_ver (self, data) :
            major, minor = struct.unpack('!HH', data)
            self.version = str(major)+'.'+str(minor)
            print 'version '+self.version

        def pkt_pin (self, data) :
            self.productInformation = data

        def pkt_top (self, data) :
            pass

        def pkt_MeC (self, data) :        
            pass

        def pkt_mpl (self, data) :
            pass

        def pkt_MvC (self, data) :
            pass         
        
        def pkt_AMC (self, data) :
            pass

        def pktPowr (self, data) :
            pass

        def pktVidM (self, data) :
            dumpHex (data)
            dumpAscii (data)
            self.videoFormat = data

        def pktInPr (self, data) :
            dumpHex (data)
            dumpAscii (data)
            input = {}
            input['index'] = struct.unpack('B', data[0])[0]
            pos = data[1:].find('\0')
            if (pos==-1) :
                print 'can\'t find \'\\x0\''
            input['longText'] = data[1:pos+1]
            input['shortText'] = data[21:27]
            print input

    def sendATEMCommand(command, data):
        global ATEMAddress
        a = Atem()
        a.connectToSwitcher ((ATEMAddress,9910))
        a.waitForPacket()
        a.waitForPacket()
        a.waitForPacket()
        a.waitForPacket()
        a.sendCommand (command, data); 


motorProcess = Process(target=motorControlLoop, args=())
motorProcess.start()