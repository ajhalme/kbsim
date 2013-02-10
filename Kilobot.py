import random, copy, pygame

from Vec2d import *
from KBGUI import KilobotView

class Kilobot:
    def __init__(self, sim):
        self.sim = sim

        self.secretID = len(sim.bots) # clever hack, init ~ sim.bots += 1
        self.secretN = sim.config['n']
        self.secretNx = []

        self.radius = sim.config['botradius']
        self.rradius = sim.config['botrradius']
        self.speed = 0

        self.pos = Vec2d(0,0)
        self.orientation = 0

        self.leds = [0,0,0]

        self.op = self.fullCW # fpointer
        self.opc = 0 # op counter
        self.opres = None
        self.history = sim.config['hsize'] * [[None]]
        self.historyp = 0

        self.tx_enabled = 0        
        self.msgrx = sim.config['msgform']
        self.msgtx = sim.config['msgform']
        self.rxbuf = sim.config['rxbufsize'] * [sim.config['msgform']]
        self.rxbufp = 0
        self.rxtempbuf = []

        self.running = False
        
        self.PC = 0
        self.program = []  # derived replace
        self.debug = ""

        self.view = KilobotView(self)

    ## 
    ## Positions
    ## 

    def ffoot(self):
        return self.pos + Vec2d(self.radius - 1, 0).rotated(self.orientation)

    def rfoot(self):
        return self.pos + Vec2d(self.radius - 1, 0).rotated(self.orientation + 120)

    def lfoot(self):
        return self.pos + Vec2d(self.radius - 1, 0).rotated(self.orientation + 240)

    def led(self):
        return self.pos + Vec2d(self.radius - 3, 0).rotated(self.orientation + 60)


    ##
    ##  (Internal) Python API
    ## 

    def turnOnLFoot(self, speed):
        self.speed = speed
        degrees = self.speed
        self.orientation -=degrees
        pos = Vec2d(self.radius - 1, 0).rotated(self.orientation + 60 - degrees)
        self.pos = self.lfoot() + pos

    def turnOnRFoot(self, speed):
        self.speed = speed
        degrees = self.speed
        self.orientation += degrees
        pos = Vec2d(self.radius - 1, 0).rotated(self.orientation - 60 + degrees)
        self.pos = self.rfoot() + pos

    def goForward(self, speed):
        self.turnOnRFoot(speed)
        self.turnOnLFoot(speed)

    def runProgram(self):  # asyncing start, (NB: deep sleep mode ~ 8s)
        if (self.running):
            self.program[self.PC]()
            self.PC = (self.PC + 1) % (len(self.program))
        else: 
            if (random.randrange(0,20) == 0): # magic number
                self.running = True

    ##
    ##  Simulated C API
    ## 

    def set_motor(self, cw_motor, ccw_motor):
       """
       PWM values 0-255 (off-on) for both motors.
       max turning 45deg/s, max speed = 10mm/s
       """
       if cw_motor == ccw_motor: # forward, stop
           self.goForward(int(math.ceil((cw_motor + ccw_motor)/(25.5*4))))
       elif cw_motor == 0: # ccw_motor on
           self.turnOnRFoot(int(math.ceil((ccw_motor)/(25.5*2))))
       elif ccw_motor == 0: # cw_motor on
           self.turnOnLFoot(int(math.ceil((cw_motor)/(25.5*2))))
       else:
           pass # TODO: noisy moving; wide circle, forward AND turn

    def _delay_ms(self, s):
        pass # TODO: delay, maybe an internal variable to do self.PC-- or something like that

    def set_color(self, r, g, b):
        """
        Range: 0-3 (off-brightest)
        """
        self.leds = [r*85,g*85,b*85]

    def kprinti(self, i):
        print i
        
    def kprints(self, s): # obly up to 10 charcaters
        if (len(s) > 10):
            print "PRINTING OVER 10 CHARACTERS"
        print s

    def message_out(self, tx0, tx1, tx2):
        """
        Real:
        Set message values to be sent over IR every .2 seconds, 3 bytes tx0,tx1,tx2
        (tx2 lsb must not be used) .
        This:
        Set outgoing message.
        """
        self.msgtx = (tx0, tx1, tx2 & 0xFE)

    def get_message(self):
        """
        Real:
        Take oldest message off of rx buffer message. It is only new if msgrx[5]==1 !
        If so, message is in msgrx[0] and msgrx[1]; distance to transmitting robot
        (in mm) is in msgrx[3]. The distance depends on the surface used as the light
        intensity is used to compute the value.
        This:
        RX Buffer of four, take the oldest one and pass to msgrx
        TODO: assumption; always receive up to four messages vs. lose some sometimes
        """
        for i in range(0, self.sim.config['rxbufsize']):
            self.rxbufp = (self.rxbufp - 1) % self.sim.config['rxbufsize']
            if (self.rxbuf[self.rxbufp][self.sim.config['msg_new']] == 1):
                self.msgrx = copy.deepcopy(self.rxbuf[self.rxbufp])
                self.rxbuf[self.rxbufp] = self.sim.config['msgform']
                return
        self.msgrx = self.sim.config['msgform']

    def measure_charge_status(self):
        return 0 # TODO: never charging

    def measure_voltage(self):
        """ Shift decimal by two for voltage. """
        return 394 # TODO: apparently, the battery is at 3.94 V
            
    def get_ambient_light(self):
        """ -1 for incoming message, else value of ambient light as seen bt sensor """
        return 0 # TODO: no overhead programming

    def rand(self): # standard C function, here modified to have an 8-bit bound
        return random.randrange(0,256)

    ##
    ##  Extended C API
    ## 

    def midFWRD(self):
        self.set_motor(128,128)

    def fullFWRD(self):
        self.set_motor(255,255)

    def fullCCW(self):
        self.set_motor(255,0)

    def fullCW(self):
        self.set_motor(0,255)

    def stop(self):
        self.set_motor(0,0)

    def wait(self):
        self._delay_ms(100)

    def toggle_r(self):
        new = 255 if (self.leds[0] == 0) else 0
        self.leds = [new, 0, 0]

    def toggle_g(self):
        new = 255 if (self.leds[1] == 0) else 0
        self.leds = [0, new, 0]

    def toggle_b(self):
        new = 255 if (self.leds[2] == 0) else 0
        self.leds = [0, 0, new]

    def sayoutmsg(self):
        self.kprints(self.outmsg)

    def toggle_tx(self):
        self.tx_enabled ^= 1

    def enable_tx(self):
        self.tx_enabled = 1

    def disable_tx(self):
        self.tx_enabled = 0

    def msgrx_reset(self):
        self.msgrx = self.sim.config['msgform']

    def clear_rxbuf(self):
        self.rxbuf = self.sim.config['rxbufsize'] * [self.sim.config['msgform']]

    def reset_rx(self):
        self.msgrx_reset()
        self.clear_rxbuf()
        self.rxbufp = 0

    ## 
    ## Common simulation idioms
    ## 

    def loop(self):  self.PC -= 1 # loop [this]
    def loop0(self): self.PC -= 1 
    def loop1(self): self.PC -= 2 # loop [this-1, this]
    def loop2(self): self.PC -= 3 # loop [this-2, this-1, this]
    def loop3(self): self.PC -= 4
    def loop4(self): self.PC -= 5
    def loop5(self): self.PC -= 6
    def loop6(self): self.PC -= 7
    def loop7(self): self.PC -= 8
    def loop8(self): self.PC -= 9
    def loop9(self): self.PC -= 10

    def goto(self, target):
        self.PC = self.program.index(target) - 1


    ##
    ## History routines
    ##

    def history_add(self, things):
        self.history[self.historyp] = things
        self.historyp = (self.historyp + 1) % self.sim.config['hsize']

    def history_del(self):
        self.historyp = (self.historyp - 1) % self.sim.config['hsize']
        self.history[self.historyp] = [None]

    def history_reset(self):
        self.history = self.sim.config['hsize'] * [[None]]
        self.historyp = 0

    def history_num(self):
        return reduce((lambda x,y: x+1 if y != [None] else x+0), self.history, 0)

    def history_full(self):
        return self.history_num() == self.sim.config['hsize']

    def history_reduce(self):
        top = 0
        dists = []
        heard = []
        hbins = self.sim.config['hsize'] * [[None]]

        for i in range(self.sim.config['hsize']):
            entry = self.history[(self.historyp - 1 - i % self.sim.config['hsize'])]
            if (entry == [None]): break

            mheard = entry[0]
            mtop   = entry[1]
            mmode  = entry[2]
            mdist  = entry[3]
            
            if (mheard not in heard):
                ind = len(heard)
                heard.append(mheard)
                hbins[ind] = [entry]
            else:
                ind = heard.index(mheard)
                hbins[ind].append(entry)
                
            if (mtop > top):
                top = mtop
            
            dists.append(mdist)

        return top, dists, heard, hbins
