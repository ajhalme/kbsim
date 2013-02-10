
"""
Franklinbot 

Franklinbot is a basic leader election bot, _for CIRCLEs_,
following a probabilistic variant of the Franklin's leader
election algorithm for anonymous rings [1].

the implementations makes good use of the limited 23 bit
wide broadcast channel, simulating directed messages
using the protocol: [myID,yourID,<data>]

As a final touch, we have a tree numbering from the chosen
leader forward, shown as a led-as-bit numbering. Leader
has shows all leds, but after that: 001,010,011,100,...

 [1]
  Leader Election in Anonymous Rings: Franklin Goes Probabilistic
  Rena Bakhshi, Wan Fokkink, Jun Pang and Jaco van de Pol
  http://www.springerlink.com/content/d168748154n32417/
"""

from Kilobot import *

def load(sim):
    return Franklinbot2(sim)

class Franklinbot2(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.N = self.secretN # <= 15, not enough bits for larger
        self.mymsg = [0x00, 0x00, 0x00]
        self.ID = 0
        self.bit = 0
        self.looper = 0

        self.neighbors = []
        self.treepos = 0
        
        self.msgA = 0
        self.msgB = 0

        self.program = [self.activate,
                        self.gethood,
                        self.begin,

                        self.getv,
                        self.getw,
                        self.decide,

                        self.lead,
                        self.follow,

                        self.showtree,

                        self.loop
                        ]

    ##
    ##  Util
    ##

    def _parse(self):
        heardsender = (self.msgrx[0] << 1) | ((self.msgrx[1] & 0x80) >> 7)
        heardID  = ((self.msgrx[1] & 0x7F) << 2) | ((self.msgrx[2] & 0xC0) >> 6)
        heardhop = (self.msgrx[2] & 0x3C) >> 2
        heardbit = (self.msgrx[2] & 0x02) >> 1
        return [heardsender, heardID, heardhop, heardbit]

    def _setmymsgA(self, a):
        self.mymsg[0] = (a & 0x1FE) >> 1
        self.mymsg[1] = (self.mymsg[1] & 0x7F) | ((a & 0x01) << 7)

    def _setmymsgB(self, b):
        self.mymsg[1] = (self.mymsg[1] & 0x80) | ((b & 0x1FC) >> 2)
        self.mymsg[2] = (self.mymsg[2] & 0x3F) | ((b & 0x03) << 6)

    def _setmymsghop(self, m):
        self.mymsg[2] = (self.mymsg[2] & 0xC3) | ((m & 0xf) << 2)

    def _setmymsgbit(self, b):
        self.mymsg[2] = (self.mymsg[2] & 0xFD) | (b << 1) # lsb is special


    ##
    ##  Func
    ##
    
    def activate(self):
        self.id = (self.rand() << 2) + (self.rand() & 0x02) # 0-1023, 10 bits
        self.mode = 0 # 0-7, 3 bits
        self._setmymsgA(self.id)
        self._setmymsgB(self.id)
        self._setmymsghop(0)        
        self._setmymsgbit(self.bit)        
        self.message_out(self.mymsg[0], self.mymsg[1], self.mymsg[2])
        self.toggle_tx()
        self.debug = str(self.id) +":"+ str(self.bit)

    def gethood(self):
        self.looper += 1
        self.get_message()
        if (self.msgrx[5] == 1):
            msg = self._parse()
            if msg[2] == 0: # mode: gethood == 0
                if not (msg[0] in self.neighbors):
                    self.neighbors.append(msg[0])

        if (self.looper < 150): # magic number for "delay"
            self.PC -= 1
        elif (len(self.neighbors) != 2):
            self.looper = 0
            self.PC -= 1
        else:
            print self.secretID, self.id, self.neighbors
            self.looper = 0

    def begin(self):
        self.toggle_b()
        self.min = self.id
        self._setmymsgA(self.id) # ID
        self._setmymsgB(self.min) # lowest seen
        self._setmymsghop(1) # start round
        self._setmymsgbit(self.bit) # first round
        self.message_out(self.mymsg[0], self.mymsg[1], self.mymsg[2])
        
    def getv(self): # from one
        self.get_message()
        if (self.msgrx[5] == 1):
            msg = self._parse()
            if msg[0] == self.neighbors[0]:
                self.msgA = msg
                return
        self.PC -= 1

    def getw(self): # from the other
        self.get_message()
        if (self.msgrx[5] == 1):
            msg = self._parse()
            if msg[0] == self.neighbors[1]:
                self.msgB = msg                
                return
        self.PC -= 1

    def decide(self):
        res = min(self.msgA[1], self.msgB[1])
#        print self.secretID, self.id, self.msgA, self.msgB, "res:", res
        if (res < self.id):   # passive
            self.set_color(3,0,0)
            self.PC += 1     # skip over lead()
        elif ((self.msgA[1] == self.id and self.msgA[2] == self.N) or
              (self.msgB[1] == self.id and self.msgB[2] == self.N)):
            self.set_color(3,3,3)
            self.bit = 1
            self._setmymsgbit(self.bit) # first round
            self.message_out(self.mymsg[0], self.mymsg[1], self.mymsg[2])
            return
        else: # stay active, retry
            self.PC -= 3

    def lead(self):
        self.PC -= 1

    def follow(self):
        self.get_message()
        if (self.msgrx[5] == 1):
            msg = self._parse()
            self._setmymsgB(msg[1])
            self._setmymsghop(msg[2] + 1)
            self._setmymsgbit(msg[3])
            self.message_out(self.mymsg[0], self.mymsg[1], self.mymsg[2])
            if (msg[3] == 1):
                self.treepos = msg[2]
                return
        self.PC -= 1

    def showtree(self):
        r = self.treepos % 2
        g = (self.treepos >> 1) % 2
        b = (self.treepos >> 2) % 2
        self.set_color(3*r,3*g,3*b)

    def loop(self):
        self.PC -= 1
        
        
