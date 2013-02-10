
"""
Abot 

Abot is an advanced bot, demonstrating complex pattern
formation, namely the Aalto logo ("A!"). Abot assumes a 
successfully chosen leader.

Abot leader starts the pattern while others activate with
a scatter-and-return scheme, where all bots move away 
until they hear nothing and then begin spiraling. The 
spiral eventually hits the existing form and the bot joins
it at the appropriate moment, orbiting the structure
until the dynamically updated target position is reached.

For Abot, the key challenge is in the control routine, that
manages the steering decisions in all situations. Here
the HW limitation of no bearing sensor cearly manifests itself.

The pattern itself is hardcoded behind the getRules() function
and can easily be modified for other shapes. As such, the
algorithm and the execution is relatively generic and adaptable
to many kinds of needs. 

NOTE: The next position is defined by two existing reference
      points in the pattern. Bots bumping into each other is an
      issue and inaccurate positioning makes merry hell of the 
      whole structure, causing complete breakdowns at times,
      as failing gracefully is not always an option.

"""

from Kilobot import *

def load(sim):
    return Abot(sim)

# msgs, dodge lsb
GO = 0x8; SCATTER = 0xA; DONE = 0xC;
# magic consts
TURN = 19; TRIGGER = 5
FRINGE = 67
ANON = -1
RXBUFSIZE = 4

class Abot(Kilobot):
    def __init__(self, sim):
        Kilobot.__init__(self, sim)
        
        self.id = ANON # identity
        self.top = 0

        self.mark = 0 # finish
        self.rules = None 

        self.target = 0 # orbit
        self.tcount = 0
        self.tvalid = False

        self.spiral = 0 # spiral
        self.scount = 0

        if (self.secretID == 0): # the leader, the first violin
            self.program = [self.activateL,
                            self.hold
                            ]
        else: # others
            self.program = [self.activate,
                            self.get,
                            self.doOrbit,
                            self.doSpiral,
                            self.doFinish,
                            self.hold
                            ]
    ##
    ## Info print hack; Simulator function override
    ##
    def drawinfo(self, screen): # draw position text
        pos = self.pos.inttup()
        text = self.font.render(
            "%d:%s" % (self.secretID, str(self.id) if self.id >= 0 else "-"),
            True, (0, 0, 0))
        screen.blit(text, (pos[0] - 12, pos[1] - 2))

    ##
    ## Activation
    ##
     
    def activateL(self):
        self.id = 0
        print "0 assumes position as 0"
        self.debug = "S:0"
        self.message_out(0,0,GO)
        self.toggle_tx()
        self.set_color(0,3,0)
        return self.goto(self.hold)
           
    def activate(self):
        self.get_message()
        if (self.msgrx[5] == 1): # scatter
            self.message_out(42,0,SCATTER)
            self.enable_tx()
            if (self.rand() % 4 == 0):
                self.op = self.fullCW if self.op == self.fullCCW else self.fullCCW
            self.op()
        elif (self.rand() % 100 == 0): # start
            self.disable_tx()
            print self.secretID, "begins target hunt"
            self.set_color(3,0,0)           
            self.target = 1
            self.debug = "T:%d" % (self.target)
            self.getRules(self.target)
            return self.goto(self.get)
        else:
            self.midFWRD()

        self.PC -= 1

    ##
    ## Listen
    ##

    def get(self): 
        isConnected = False
        for i in range(0, RXBUFSIZE): # check all of the buffer for msgs
            self.get_message()
            if (self.msgrx[5] == 1):
                isConnected = True
                self.history_add(self.msgrx[0:4])
            else:
                break

        self.reset_rx()

        if (isConnected and self.id == ANON):
            return self.goto(self.doOrbit)
        elif (isConnected and self.id != ANON):
            return self.goto(self.doFinish)
        else:
            return self.goto(self.doSpiral)

    ##
    ## Move
    ##

    def doSpiral(self): # spiral towards the swarm; turn, forward or finish
        self.scount += 1
        if (self.scount < TURN):
            self.fullCCW()
        elif (self.scount <= TURN + self.spiral):
            self.midFWRD()
        else:
            self.scount = 0
            self.spiral += 3

        # are we by the form yet?
        self.get_message()
        if (self.msgrx[5] == 1):
            self.midFWRD()
            self.fullCCW()
            self.scount = 0
            self.spiral = 0
            self.history_reset()
            return self.goto(self.doOrbit)
        else:            
            self.PC -= 1       

    def doOrbit(self): # follow the form gradient
        
        # ensure we have enough history
        if (not self.history_full()):
            self.fullCCW()
            return self.goto(self.get)

        # reduce and aggregate message history
        top, dists, heard, hbins = self.history_reduce()        
        heardR1 = self.rules[1][0] in heard

        # adjust target, if necessary
        if (top >= self.target):
            self.target = top + 1
            self.getRules(self.target)
            print self.secretID, "target adjust to", self.target
            self.debug = "T:%d" % (self.target)
            self.tvalid = False
            self.tcount = 0
            return self.goto(self.get)

        # decide: either follow general orbit, or start closing in
        if (heardR1): # TODO un-NEGATE
            rule1 = self.rules[1][0]
            rdists = map((lambda x: x[3]), hbins[heard.index(rule1)])

            # average hits the FRINGE, note: smart array
            isValid = len(rdists) > 2 and sum(rdists)/len(rdists) == FRINGE 
#            if (self.target > 6 and not isValid): # make a bit easier to start later on
#                isValid = FRINGE in rdists
#
#            print self.secretID, rule1, rdists, isValid

            if (isValid): # assume the position
                print self.secretID, "assumes position as", self.target
                self.id = self.target
                self.debug = "S:%d" % (self.id)
                self.set_color(3,0,3)        
                return self.goto(self.doFinish)                
                                       
        # steering decision
        self._steer(FRINGE, dists, 50)
          
        return self.goto(self.get)

    def _steer(self, goal, dists, repel):
        multi = 8
        d = dists[0]
        diff = d - goal
        repels = d < repel
        goingUp = diff < 0
        near = 0*multi <= abs(diff) < 1*multi
        far1 = 1*multi <= abs(diff) < 2*multi
        far2 = 2*multi <= abs(diff) < 3*multi
        far3 = 3*multi <= abs(diff) < 4*multi
        far4 = 4*multi <= abs(diff) < 5*multi # 32 <= d < 40
        avg = sum(dists)/len(dists)

        # we are near our goal
        if (goal < d <= goal + multi):
            self.fullCCW()
            self.fullCCW()          
        elif (d == goal):
            self.midFWRD()
        elif (goal - multi <= d < goal):
            self.fullCW() 
            self.fullCW() 

        # we are too close
        elif (repels):
            self.fullCW()

        # we are !near
        elif (far1):
            self.midFWRD()
            self.op = self.fullCW if goingUp else self.fullCCW
            self.op()
        elif (far2): # going down
            self.midFWRD()
            self.op = self.fullCW if goingUp else self.fullCCW
            if (self.rand() % 5 == 0):
                self.op()
        elif (far3):
            self.midFWRD()
            self.op = self.fullCW if goingUp else self.fullCCW
            if (self.rand() % 10 == 0 or avg == d):
                self.op()
        elif (far4):
            self.midFWRD()
            self.op = self.fullCW if goingUp else self.fullCCW
            if (self.rand() % 20 == 0 or avg == d):
                self.op()


    # NOTE: custom pattern; 
    def getRules(self, target):
        if (target == 0): # never used, merely for human readability
            print "ERROR: someone requested rules for target 0"
            exit(-42)
            self.rules = [0, (0, 00), (0, 00), 0]
        elif (target == 1):
            self.rules = [1, (0, 32), (0, 32), 0]
        elif (target == 2):
            self.rules = [2, (0, 56), (1, 32), 0]
        elif (target == 3):
            self.rules = [3, (0, 65), (2, 32), 0]
        elif (target == 4):
            self.rules = [4, (0, 55), (3, 32), 0]
        elif (target == 5):
            self.rules = [5, (0, 32), (4, 32), 0]

        elif (target == 6): # the tips
            self.rules = [6, (4, 64), (2, 32), 0]
        elif (target == 7):
            self.rules = [7, (2, 64), (0, 32), 0]
        elif (target == 8):
            self.rules = [8, (0, 64), (4, 32), 0]

        elif (target == 9): # A pegs
            self.rules = [9, (5, 55), (8, 32), 0]
        elif (target == 10):
            self.rules =[10, (1, 66), (7, 32), 0]

        elif (target == 11): # exclamation
            self.rules =[11, (3, 63), (6, 63), 0]
        elif (target == 12):
            self.rules =[12, (8, 66), (11,33), 0]
        elif (target == 13):
            self.rules =[13, (9, 63), (12,31), 0]
        elif (target == 14):
            self.rules =[14, (9, 60), (13,40), 0]
        

    def _forfeit(self):
        print self.secretID, "forfeits position as", self.id
        self.mark = 0
        self.target = 0
        self.tcount = 0
        self.id = ANON
        self.set_color(3,0,0)
        self.disable_tx()        

    # TODO: proper maintenance procedure
    # the last mms are the hardest
    def doFinish(self):
        # reduce and aggregate message history
        top, dists, heard, hbins = self.history_reduce()        
       
        # if denied, reset and restart
        if (top >= self.id):
            self._forfeit()
            return self.goto(self.get)

        heardR1 = self.rules[1][0] in heard
        heardR2 = self.rules[2][0] in heard
        r1bin = r2bin = None
        heardR1bound = heardR2bound = False
        if (heardR1):
            r1bin = map((lambda x: x[3]), hbins[heard.index(self.rules[1][0])])
            heardR1bound = self.rules[1][1] in r1bin
        if (heardR2):            
            r2bin = map((lambda x: x[3]), hbins[heard.index(self.rules[2][0])])
            heardR2bound = self.rules[2][1] in r2bin
                  
        # done when second is reached (or when we want to be the first violin)
        if ((self.mark == 1 and heardR2bound) or (heardR1bound and self.id == 1)):
            self.top = self.id
            if (self.id == self.secretN - 1):
                self.message_out(self.id, self.id, DONE)
                self.set_color(0,3,0)        
            else:
                self.message_out(self.id, self.id, GO)
                self.set_color(0,0,3)
            self.enable_tx()
            return self.goto(self.hold)
        elif (heardR1): # otherwise follow first
            if (heardR1bound):
                self.mark = 1
            r1bin = map((lambda x: x[3]), hbins[heard.index(self.rules[1][0])])
            # steering
            self._steer(self.rules[1][1], r1bin, 0)
                    
        elif (self.rand() % 100 == 0):
            self._forfeit()
            return self.goto(self.get)
            
        return self.goto(self.get)


    def hold(self):
        self.PC -= 1
        self.get_message()
        if (self.msgrx[5] == 1):

            heard = self.msgrx[0]
            top   = self.msgrx[1]
            mode  = self.msgrx[2]
            dist  = self.msgrx[3]

            if (top > self.top): # to help others, all of the swarm shouts the top
                self.top = top
                self.message_out(self.id, self.top, mode)

            if (mode == DONE): # finish trigger
                self.enable_tx()
                self.message_out(self.id, self.top, DONE)
                self.set_color(0,3,0)

            self.reset_rx()
