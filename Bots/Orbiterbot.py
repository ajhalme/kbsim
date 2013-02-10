
"""
Orbiterbot

Orbiterbot is a somewhat basic demo bot, demonstrating the 
challenges in Kilobot motion control. Orbiterbot strives to
orbit the bots that it sees, i.e., move at a constant 
distance in relation to them. Orbiterbot works best with
few bots and either in a LINE or a small PILED form.

Orbiterbot implements a very naive reaction controller.

NOTE: Also demonstrated is the self.program differentiation,
      simple heterogenous behavior programming.

"""


from Kilobot import *

def load(sim):
    return Orbiterbot(sim)

NEAR = 35
MID = 54
FAR = 69

class Orbiterbot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.id = self.secretID
        self.r = MID
        self.op = self.fullFWRD

        self.dist = 0
        self.timeout = 0

        if (self.id == 0): # the leader
            self.set_color(0,3,0)
            self.program = [self.activate,
                            self.loop,                         
                            ]

        elif (self.secretN - 1 == self.id): # the orbiter
            self.set_color(3,0,0)
            self.program = [self.getX,
                            self.react,
                            self.loop
                            ]
        else: # others
            self.set_color(0,0,3)
            self.program = [self.activate,
                            self.loop,                         
                            ]

    ##
    ## Func
    ##
     
    def activate(self):
        self.message_out(self.id, 0, 0)
        self.debug = str(self.id)
        self.toggle_tx()

    def getX(self):
        self.get_message()
        if (self.msgrx[5] == 1):
            if (self.msgrx[3] < self.r):
                self.dist = self.msgrx[3]
                return
            
        self.timeout += 1
        if (self.timeout > 3):
            self.timeout = 0
            self.dist = FAR
            return
        self.PC -= 1       
        
    def react(self):
        self.clear_rxbuf()

        if (self.dist > self.r):
            self.op = self.fullCCW
        else:            
            self.op = self.fullFWRD

        self.op()
        self.PC -= 2
