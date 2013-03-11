
"""
Swarmlinebot (Deprecated)

Swarmlinebot was an experiment in constructing a line by 'swarming', having the
bots compete for the privilege of being the next in line. 

Stored for posterity.

NOTE: Deprecated. Superseded by LineBOT.

"""

from Kilobot import *

def load(sim):
#    return Swarmlinebot(sim)
    return Defaultbot(sim)

class Defaultbot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)
        self.program = [self.loop0]


SYN = 2 # dodge lsb
SYNACK = 4
ACK = 6

LINE = 8
SWARM = 10

LO = 45
GOLD = 55
HI = 55

FAR = GOLD
NEAR = LO

class Swarmlinebot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)
        
        self.id = self.secretID # bots have a unique numbering 0..(n-1)
        self.hood = []

        self.spos = 0
        self.target = 0
        self.tcount = 0
        self.tvalid = False

        self.spinmin = FAR
        self.scount = 0
        
        self.msg = [0,0,0,0]
        self.timeout = 0

        if (self.secretID == 0): # the leader
            self.hood = self.secretNx
            self.program = [self.activateL,
                            self.waitFirstSynAck,
                            self.leadloop
                            ]
        else: # others
            self.program = [self.lineInit,
                            self.loop0, # end for first violin
                            self.activate,

                            self.get,
                            self.orbit,
                            self.stride,

                            self.closein,
                            self.loop0,
                            ]

    ##
    ## Func
    ##

    ## Leader and first designation, line initiation
     
    def activateL(self):
        self.hood = self.secretNx
        self.spos = 0
        self.message_out(self.id, self.hood[0], SYN)
        self.toggle_tx()
        self.debug = "LEADER"
        self.set_color(0,3,0)

    def waitFirstSynAck(self):
        self.get_message()
        if (self.msgrx[5] == 1):
            if (self.msgrx[0] == self.hood[0] and self.msgrx[2] == SYNACK):
                print self.secretID, "got SYNACK"
                self.message_out(self.id, self.hood[0], ACK)
            elif (self.msgrx[2] == LINE): # notice that the swarm has begun
                print self.secretID, "joins LINE"
                self.message_out(0, 0, LINE) # join it to wake those nearby                
                return self.goto(self.leadloop)
        self.PC -= 1  

    def leadloop(self):
        self.PC -= 1

    def lineInit(self):
        self.get_message()
        if (self.msgrx[5] == 1):
            # you are the first after leader ...
            if (self.msgrx[0:3] == (0, self.id, SYN)):
                if (not self.tx_enabled):
                    print self.secretID, "got SYN"
                    self.message_out(self.id, self.msgrx[0], SYNACK)
                    self.toggle_tx()
                    self.spos = 1
                    self.debug = "FIRST"
                    self.set_color(0,0,3)        
            elif (self.msgrx[0:3] == (0, self.id, ACK)):
                print self.secretID, "got ACK"     
                self.message_out(1, 1, LINE)
                print self.secretID, "starting SWARM"
                return self.goto(self.closein) # TODO: maintain, (orient)
            # ... or you are not
            elif (self.msgrx[2] == LINE):
                print self.id, "begins target hunt"
                return self.goto(self.activate)

        self.PC -= 1

    def activate(self):
        self.target = 2 # leader=0, first=1
        self.debug = "T:%d" % (self.target)
        self.set_color(3,0,0)

    ## 
    ## Line swarming
    ## 
    def get(self): 
        self.get_message()
        if (self.msgrx[5] == 1):
            self.msg = self.msgrx[0:4]
            if (self.msg[2] == LINE):
                self.timeout = 0
                return self.goto(self.orbit)
            else: # we heard something, but not what we were looking for
                self.timeout = 0

        self.timeout += 1
        if (self.timeout > 10):
            self.timeout = 0
            self.msg = [0, 0, 0, FAR]
            return self.goto(self.stride)
        self.PC -= 1       
        
    def stride(self): # towards the swarm by any means necessary, currently black magic
        if (self.sim.round < 500):
            self.PC -= 1
            return

        self.scount += 1
        if (self.scount == 1):            
            print self.id, "gone spinning"
        elif (self.scount < 75):            
            self.get_message()
            if (self.msgrx[5] == 1):
                self.scount == 80
            else:
                self.fullCCW()
        elif (self.scount < 90): self.fullFWRD()
        else:
            self.spinmin = FAR
            self.scount = 0
            self.goto(self.get)
        self.PC -= 1       

    def orbit(self): # try and join the line
        self.clear_rxbuf()

        heard = self.msg[0]
        dist = self.msg[3]

        # adjust target
        if (heard >= self.target):
            self.target = heard + 1
            print self.id, "target adjust to", self.target
            self.debug = "T:%d" % (self.target)
            self.tcount = 0
            if (self.tcount > 10): # make those too close take another lap
                print self.id, "too close, validity reset"
                self.tvalid = False

#        if (self.id == 2): print self.heard, self.dist, self._history_peek(), self.tcount, self.tvalid
        
        # first visit head
        if (heard == 0 and (GOLD-1 <= dist <= GOLD+1)):
            self.tcount += 1            
            if (self.tcount == 60):
                print self.id, "tvalid True"
                self.tvalid = True                
                self.tcount = 0

        # then go and add yourself to the tail
        if (self.tvalid and 
            heard == self.target - 1 and (GOLD-1 <= dist <= GOLD+1)):
            self.tcount += 1
            if (self.tcount == 35): # magic number for timing
                print self.id, "assumes position as", self.target
                self.spos = self.target
                self.message_out(self.spos, self.spos, LINE)
                self.tx_enabled = 1
                self.debug = "S:%d" % (self.spos)
                self.set_color(0,0,3)        
                self.tcount = 0
                return self.goto(self.closein)
        elif (self.tvalid):
            self.tcount = 0
                
        # steering decision
        peek = self._history_peek() # interference == not at line end, but in transit there
        interference = (peek[0] != heard and peek[2] == LINE and abs(peek[3] - dist) >= 3) 
        if (dist <= LO or interference):
            self.op = self.fullCW
        elif (HI <= dist < FAR):
            self.op = self.fullCCW
        elif (dist == FAR):
            self.op = self.fullCCW if self.rand() > 16 else self.fullCW
        else:            
            self.op = self.fullFWRD

        # update round
        self._history_add(self.msg) # store current msg to memory
        self.op()
        return self.goto(self.get)


    def closein(self): # the last mms are the hardest (?)
        self.PC -= 1
        self.get_message()
        if (self.msgrx[5] == 1):
#            self._history_add(self.msgrx[0:4])
            if (self.msgrx[0] == self.spos - 1):
                if (self.msgrx[3] >= NEAR):
                    self.op = self.fullCCW
                    """ # TODO more smarts in tagging along
                    diff = self._history_peek()[3] - self.msgrx[3]
                    if diff < -1:
                        print diff
                        self.op = self.fullCW if self.op == self.fullCCW else self.fullCCW
                        """
                else:
                    self.op = self.op_null
        self.op()        
