
"""
LineBOT 

LineBOT is an advanced bot, demonstrating the fusion of a 
general (connected) topology leader election algorithm (see
Wavebot) and a pattern formation scheme (see Abot), 
hardcoded to produce a line starting from the leader. 

LineBOT does the following:
 * choose an identity at random
 * shout out to neighborhood, aggregate a map of own hood
 * begin leader election either as an initiator or a repeater
 * pass LE waves until convergence
 * decide to either take the leader role or not
 * leader: begin the line
 * followers: scatter and spiral back, then orbit the form
              already in place and join it as instructed

NOTE: This a HC bot, be comfortable with the programming
      model before trying to decipher this. Also see the
      standalone version of the two parts of the algorithm:
      leader election and orbit pattern formation.

"""

from Kilobot import *

def load(sim):
    return LineBOT(sim)

PTOP = 16 # four bits, woo!
# modes, note that we dodge the LSB
TOK = 0x0; LDR = 0x2; WIN = 0x4
GO = 0x8; SCATTER = 0xA; DONE = 0xC;
# magic numbers
TURN = 19; TRIGGER = 5; FRINGE = 67; ANON = -1
RXBUFSIZE = 4

class LineBOT(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        # Neighborhood and RX/TX structures
        self.near = []         # da hood    
        self.hoodid = 0 # id for RX/TX
        self.hoodloop = 0      # hood discovery repeater
        self.targetp = 0       # tx pointer
        self.msg = [0,0,0,0]   # sender, receiver, data, data_t
        self.msghistory = []   ## FIFO: enforce unique messages
        self.fifo = []         ## FIFO: extra container

        # Leader election variables
        self.p = 0      # ID2, "self.id for LE use"
        self.caw    = 0 # ID , "Currently active wave"
        self.rec    = 0 # Int, "Number of <tok, caw_p> received"
        self.father = 0 # ID , "Father in wave caw_p"
        self.lrec   = 0 # Int, "Number of <ldr,...> received"
        self.win    = 0 # ID , "Identity of leader"

        # Pattern formation variables
        self.id = ANON      # identity (position in pattern)
        self.top = 0
        self.target = 0     # orbit
        self.spiral = 0     # spiral
        self.scount = 0
        self.mark   = 0     # finish
        self.rules  = None 
        self.paidDues = False

        self.program = [self.activate,
                        self.gethood,
                        self.sorthood,

                        # Leader election

                        self.isInitiator,
                        self.sendNewWave,

                        self.tryContinue,
                        self.getMessageAndDecide,
                        self.dealWithLDRmsg,
                        self.dealWithTOKmsg,
                        self.dealWithTOKreinit,
                        self.dealWithTOKhit,
                        self.whiley,

                        self.decideStatus, # TODO: fuse

                        # Pattern formation
                        self.activateL, # Leader
                        self.hold,

                        self.activateF, # Follower
                        self.get,
                        self.doOrbit,
                        self.doSpiral,
                        self.doFinish,
                        self.hold
                        ]

        
    ###
    ###
    ###    Leader election
    ###
    ###

    ##
    ##  Hood
    ##
    
    def activate(self):
        self.fillFIFO()
        self.hoodid = self.rand() # 0-255
        self.message_out(self.hoodid, self.hoodid, 0)
        self.enable_tx()

    def gethood(self):
        bypass = False
        self.hoodloop += 1
        self.get_message()
        if (self.msgrx[5] == 1):
            if (self.msgrx[0] != self.msgrx[1]): # someone's already post-hood
                print "(%.02d) bypassing, %d is ahead" % (self.secretID, self.msgrx[0])
                # HACK, we imitate fillFIFO() on the received msg
                temp = self._msgparse(self.msgrx)
                self.fifo.append(temp)
                self.msghistory.append(temp)                
                return
                                
            elif (self.msgrx[3] <= 40 and (not self.msgrx[0] in self.near)):
                self.near.append(self.msgrx[0])
        if (self.hoodloop < 100): # magic number for listen "delay"
            self.PC -= 1

    def sorthood(self):
        self.fillFIFO()
        self.near = sorted(self.near)

    ##
    ##  Wave initiation
    ##

    def isInitiator(self):
        self.fillFIFO()
        if (self.hoodid == min(self.near + [self.hoodid])): # is
            self.set_color(3,3,0)
            self.p = (self.rand() % (PTOP - 1)) + 1 # 1-31
            self.caw = self.p
        else: # isn't
            self.set_color(3,0,0)
            self.caw = PTOP
            self.PC += 1 # skip over sendNewWave
        self.disable_tx()
        self.debug = "%.02d:%c:%.02d:%.03d H:%s #F:%s" % (
            self.secretID, 'P' if (self.p>0) else 'p', self.p, 
            self.hoodid, self.near, len(self.fifo))

    def sendNewWave(self):
        self.fillFIFO()
        done = self._sendToAll(self.near, self.p, TOK)
        if not done:
            self.PC -= 1
            return

    ##
    ##  Main loop
    ##

    def tryContinue(self):
        self.fillFIFO()
        if (self.lrec == len(self.near)):
            self.PC += 6 # jump to decide

    def getMessageAndDecide(self):
        self.fillFIFO()
        if (self.fifo != []):
            self.msg = self.fifo.pop(0)
            if (self.msg[3] == LDR):
                self.win = self.msg[2]
                return # goto dealWithLDRmsg next
            elif (self.msg[3] == TOK):
                self.PC += 1
                return # goto dealWithTOKmsg next
        self.PC -= 1

    def dealWithLDRmsg(self):
        self.fillFIFO()
        if (self.lrec == 0):
            done = self._sendToAll(self.near, self.win, LDR)
            if not done:
                self.PC -= 1
                return
        self.lrec += 1
        self.PC -= 3

    def dealWithTOKmsg(self):
        self.fillFIFO()
        r = self.msg[2]
        if (r < self.caw): # re-init
            self.caw = r
            self.rec = 0
            self.father = self.msg[0] # q
            return # fall to dealWithTOKreinit
        elif (r == self.caw):
            self.rec += 1
            self.PC += 1 # jump over to dealWithTOKhit
        else: # we ignore the TOK; r > caw, so there's a better wave going on
            self.PC -= 4 # back to tryContinue
   
    def dealWithTOKreinit(self):
        self.fillFIFO()
        targets = filter((lambda x: x!=self.father), self.near)
        done = self._sendToAll(targets, self.caw, TOK)
        if not done:
            self.PC -= 1
            return
         # we ALSO go through TOKhit, when reiniting
        self.rec += 1
            
    def dealWithTOKhit(self):
        self.fillFIFO()
        if (self.rec == len(self.near)):
            done = False
            if (self.caw == self.p): # I'm the man, and others should know it
                done = self._sendToAll(self.near, self.p, LDR)      
            else: # I am dissapoint, inform father (only)
                done = self._sendToAll([self.father], self.caw, TOK)
            if not done:
                self.PC -= 1
                return                
            
    def whiley(self):
        self.fillFIFO()
        self.PC -= 7 # jump back to tryContinue
    
    def decideStatus(self):
        self.reset_rx()
        if (self.win == self.p):
            print self.secretID, "wins the election"
            return self.goto(self.activateL)
        else:
            print self.secretID, "scatters and starts to follow"
            return self.goto(self.activateF)
        
    def loop(self):
        self.PC -= 1
            
    def _sendToAll(self, targets, data, data_t):
        if self.targetp < len(targets):
            self.enable_tx()            
            self.message_out(self.hoodid, targets[self.targetp], (data<<4) | (data_t))
            self.targetp += 1
            return False
        else:
            self.disable_tx()            
            self.targetp = 0                 
            return True

    def _msgparse(self, msg):
        return [msg[0], msg[1], (0xF0 & msg[2]) >> 4, (0x0E & self.msgrx[2])]

    def fillFIFO(self):
        for i in range(0, 4):
            self.get_message()
            if (self.msgrx[5] == 1):
                temp = self._msgparse(self.msgrx)
                if (temp[1] == self.hoodid and temp[0] in self.near):
                    if (temp not in self.msghistory): # catch just one from each
                        self.fifo.append(temp)
                        self.msghistory.append(temp)

            else:
                break




    ###
    ###
    ###    Pattern formation
    ###
    ###

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
        print self.secretID, "assumes position as 0"
        self.debug = "S:0"
        self.message_out(self.id, self.id, GO)
        self.enable_tx()
        self.set_color(0,3,0)
        return self.goto(self.hold)
           
    def activateF(self):
        self.get_message()
        if (self.msgrx[5] == 1): # scatter
            self.set_color(0,0,0)
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
        for i in range(0,RXBUFSIZE): # check all of the buffer for msgs
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
        if not (self.history_full()):
            self.fullCCW()
            return self.goto(self.get)

        # reduce and aggregate message history
        top, dists, heard, hbins = self.history_reduce()        
        ruler1 = self.rules[1][0]
        ruler2 = self.rules[2][0]
        heardR1 = ruler1 in heard
        heardR2 = ruler2 in heard

        # adjust target, if necessary
        if (top >= self.target):
            self.target = top + 1
            self.getRules(self.target)
            print self.secretID, "target adjust to", self.target
            self.debug = "T:%d" % (self.target)
            self.paidDues = False
            return self.goto(self.get)

        # paying dues; must visit zero before joining the form
        if (0 in heard):
            if (len(hbins[heard.index(0)]) == 8):                
                self.paidDues = True

        # decide: either follow general orbit, or start closing in
        if (heardR1):
            r1dists = map((lambda x: x[3]), hbins[heard.index(ruler1)])
            avg1 = sum(r1dists)/len(r1dists)

            if (heardR2):
                r2dists = map((lambda x: x[3]), hbins[heard.index(ruler2)])
                avg2 = sum(r2dists)/len(r2dists)
                # TODO: use these for damage control, e.g. missing the target

            isValid = len(r1dists) > 3 and avg1 == FRINGE
           
            if (isValid and self.paidDues): # assume the position
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
        else:
            self.rules = [target, 
                          (target - 2, 65), 
                          (target - 1, 32),
                          0]

    def _forfeit(self):
        print self.secretID, "forfeits position as", self.id
        self.mark = 0
        self.target = 0
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

            # to help others, the swarm shouts the top
            if (top > self.top and (mode==GO or mode==DONE)):
                self.top = top
                self.message_out(self.id, self.top, mode)

            # finishing trigger
            if (mode == DONE):
                self.enable_tx()
                self.message_out(self.id, self.top, DONE)
                self.set_color(0,3,0)

            self.reset_rx()
