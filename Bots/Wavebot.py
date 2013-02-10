
"""
Wavebot 

Wavebot is a nontrivial bot, demonstrating an arbitrary 
topology anonymous leader election algorithm variant with
probabilistic identities and broadcast message semantics.
The LE algorithm is based on the Extinction/Echo algorithm
discussed in [1, pp. 242, 322].

Wavebot begins by choosing a random 8-bit identity and by
discovering the neighborhood. Locally minimal nodes establish
new 'waves' of leader candidate transmissions while others
forward them around their hoods. The crux of the algorithm
is in the guarantee that one and only one wave - minimum -
completes a full network traversal. The one who sent that
knows that it is the leader and all the other ones know that
they aren't.

NOTE: As the broadcast medium is shared, the assumptions of 
      the vanilla algorithm cannot be met. The randomization
      allows for directed messages, but sadly the bandwidth
      of 23bits makes the probability of a successful
      execution of the algorithm quite unlikely. Roughly,
      the algorithm has about 1 in 2 chance of succeeding.
      (And this is in the case that the implementation is OK
      and the simulator is not acting up...)

[1] Tel, G. (1994). Introduction to distributed algorithms.
    New York, NY, USA: Cambridge University Press. 
    http://dl.acm.org/citation.cfm?id=203042

"""


from Kilobot import *

def load(sim):
    return Wavebot(sim)

PTOP = 16 # four bits, woo!
DONE        = 0 # 0x0000
TOK    = 8 # 0x1000
LDR    =10 # 0x1010
WIN    =12 # 0x1100
#FREE        =14 # 0x1110

# e.g. P=5, mode_t=LDR --> 3rd byte: [0101|101|S]

class Wavebot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.id = 0 # id for RX/TX

        self.hoodloop = 0      # hood discovery repeater
        self.targetp = 0       # tx pointer
        self.near = []         # da hood    
        self.far  = []         # in range \ da hood
        self.msg = [0,0,0,0]   # sender, receiver, data, data_t

        self.msghistory = []   ## FIFO: enforce unique messages
        self.fifo = []         ## FIFO: extra container

        self.p = 0      # ID2, "self.id for LE use"
        self.caw    = 0 # ID , "Currently active wave"
        self.rec    = 0 # Int, "Number of <tok, caw_p> received"
        self.father = 0 # ID , "Father in wave caw_p"
        self.lrec   = 0 # Int, "Number of <ldr,...> received"
        self.win    = 0 # ID , "Identity of leader"

        self.program = [self.activate,
                        self.gethood,
                        self.sorthood,

                        self.isInitiator,
                        self.sendNewWave,

                        self.tryContinue,
                        self.getMessageAndDecide,
                        self.dealWithLDRmsg,
                        self.dealWithTOKmsg,
                        self.dealWithTOKreinit,
                        self.dealWithTOKhit,
                        self.whiley,

                        self.decideStatus,
                        self.loop
                        ]

    ##
    ##  Hood
    ##
    
    def activate(self):
        self.fillFIFO()
        self.id = self.rand() # 0-255
        self.message_out(self.id, self.id, 0)
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
            elif (self.msgrx[3] > 40 and (not self.msgrx[0] in self.far)):
                self.far.append(self.msgrx[0])
        if (self.hoodloop < 100): # magic number for "delay", we listen the hood for at most 100 calls
            self.PC -= 1

    def sorthood(self):
        self.fillFIFO()
        self.near = sorted(self.near)
        self.far = sorted(self.far)

    ##
    ##  Wave initiation
    ##

    def isInitiator(self):
        self.fillFIFO()
        if (self.id == min(self.near + [self.id])): # is
            self.set_color(3,3,0)
            self.p = (self.rand() % (PTOP - 1)) + 1 # 1-31
            self.caw = self.p
        else: # isn't
            self.set_color(3,0,0)
            self.caw = PTOP
            self.PC += 1 # skip over sendNewWave
        self.disable_tx()
        self.debug = "%.02d:%c:%.02d:%.03d H:%s #F:%s" % (
            self.secretID, 'P' if (self.p>0) else 'p', self.p, self.id, self.near, len(self.fifo))

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
        print "(%.02d) tryContinue :: lrec:%d, lenhood:%d" % (self.secretID, self.lrec, len(self.near))
        if (self.lrec == len(self.near)):
            self.PC += 6 # jump to decide

    def getMessageAndDecide(self):
        self.fillFIFO()
        if (self.fifo != []):
            print "(%.02d) getM&D :: #fifo:%d fifo: %s" % (self.secretID, len(self.fifo), self.fifo)
            self.msg = self.fifo.pop(0)
            print "(%.02d) getM&D :: #fifo:%d msg:%s" % (self.secretID, len(self.fifo), self.msg) 
            print "(%.02d) getM&D :: msg[3]:%d LDR:%d TOK:%d" % (self.secretID, self.msg[3], LDR, TOK)
            if (self.msg[3] == LDR):
                self.win = self.msg[2]
                print "(%.02d) got LDR msg: %s" % (self.secretID, str(self.msg))
                return # goto dealWithLDRmsg next
            elif (self.msg[3] == TOK):
                print "(%.02d) got TOK msg: %s" % (self.secretID, str(self.msg))
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
        print "(%.02d) dealt with LDR, win:%d, lrec:%d" % (self.secretID, self.win, self.lrec)
        self.PC -= 3

    def dealWithTOKmsg(self):
        self.fillFIFO()
        r = self.msg[2]
        if (r < self.caw): # re-init
            print "(%.02d) dealing with TOK; reinit @ r:%d < caw:%d" % (self.secretID, r, self.caw)
            self.caw = r
            self.rec = 0
            self.father = self.msg[0] # q
            return # fall to dealWithTOKreinit
        elif (r == self.caw):
            print "(%.02d) dealing with TOK; hit @ r:%d == caw:%d" % (self.secretID, r, self.caw)
            self.rec += 1
            self.PC += 1 # jump over to dealWithTOKhit
        else: # we ignore the TOK; r > caw, so there's a better wave going on
            print "(%.02d) dealing with TOK; miss @ r:%d > caw:%d" % (self.secretID, r, self.caw)
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
        print "(%.02d) dealt with TOK reinit; father:%d, targets %s, caw:%d, rec:%d" % (
            self.secretID, self.father, str(targets), self.caw, self.rec)
            
    def dealWithTOKhit(self):
        self.fillFIFO()
        if (self.rec == len(self.near)):
            done = False
            if (self.caw == self.p): # I'm the man, and others should know it
                done = self._sendToAll(self.near, self.p, LDR)      
            else:
                done = self._sendToAll([self.father], self.caw, TOK) # I am dissapoint, inform father (only)
            if not done:
                self.PC -= 1
                return                
        print "(%.02d) dealt TOK hit, rec(%d) vs. lennear(%d); caw(%d) vs. p(%d)" % (
                    self.secretID, self.rec, len(self.near), self.caw, self.p)
            
    def whiley(self):
        self.fillFIFO()
#        print "(%.02d) WHILEY" % (self.secretID)
        self.PC -= 7 # jump back to tryContinue
    
    def decideStatus(self):
        print "(%.02d) decidestatus" % (self.secretID)
        if (self.win == self.p):
            self.set_color(0,3,0)
        else:
            self.set_color(0,0,3)
        
    def loop(self):
        self.PC -= 1
            
    def _sendToAll(self, targets, data, data_t):
        if self.targetp < len(targets):
            print "(%.02d) sending %s : %s %d" % (self.secretID, "TOK" if data_t == TOK else "LDR",
                                                  targets, self.targetp)
            self.enable_tx()            
            self.message_out(self.id, targets[self.targetp], (data<<4) | (data_t))
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
                if (temp[1] == self.id and temp[0] in self.near):
                    if (temp not in self.msghistory): # catch just one from each
                        print "(%.02d) %s %s " % (self.secretID, str(temp), str(self.fifo))
                        self.fifo.append(temp)
                        self.msghistory.append(temp)

            else:
                break
