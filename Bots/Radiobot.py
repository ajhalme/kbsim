
"""
Radiobot 

Radiobot is a basic demo bot, demonstrating messaging and
serving as a simple tester for communication schemes
in the simulator itself, including noise.

Radiobot wanders until it hears someone.

"""

from Kilobot import *

def load(sim):
    return Radiobot(sim)

class Radiobot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.var_data = [0x00, 0x00, 0x00]
        self.var_distance = 0

        self.program = [self.setmsg,
                        self.toggle_tx,
                        self.toggle_r,
                        self.wander,
                        self.hearbarrier,
                        self.toggle_r,
                        self.toggle_g,
                        self.loop
                        ]

    def setmsg(self):
        self.message_out(0x10,0x20,0x30) # note that the last one gets masked to 0xFE

    def wander(self):
        move = self.rand()
        if move < 225:
            self.fullFWRD()
        else:
            self.fullCCW()

    def hearbarrier(self):
        data = distance = 0
        self.get_message()
        if (self.msgrx[5] == 1):
            self.var_data = [self.msgrx[0], self.msgrx[1], self.msgrx[2]]
            self.var_distance = self.msgrx[3]
        else:
            self.PC -= 2

    def loop(self):
        self.PC -= 1
        
        
