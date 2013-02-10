
"""
Listenbot

Listenbot is a basic demo bot, demonstrating the programming
model and the simulation environment with respect to message
transmission and networking.

Listenbot sends a random 23bit ID and runs around until three
different IDs have been heard. Later and after a fake delay,
the program is begun anew.

"""


from Kilobot import *

def load(sim):
    return Listenbot(sim)

class Listenbot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.var_data = [0x00, 0x00, 0x00]
        self.var_distance = 0
        self.heard = 3 * [(0x00, 0x00, 0x00, 0)] # msg1,2,3,dist
        self.heardp = 0
        self.count = 0

        self.program = [self.setmsg,
                        self.toggle_tx,

                        self.wander,
                        self.hearbarrier,
                        self.toggle_r,

                        self.wander,
                        self.hearbarrier,
                        self.toggle_g,

                        self.wander,
                        self.hearbarrier,
                        self.toggle_b,

                        self.loop
                        ]

    def setmsg(self):
        self.message_out(self.rand(),self.rand(),self.rand())

    def wander(self):
        move = self.rand()
        if move < 225:
            self.fullFWRD()
        else:
            self.fullCCW()

    def hearbarrier(self):
        self.get_message()
        if (self.msgrx[5] == 0):
            self.PC -= 2
            return

        msg = (self.msgrx[0], self.msgrx[1], self.msgrx[2], self.msgrx[3])
        for i in range(0,self.heardp):
            if (self.heard[i][0] == msg[0] and
                self.heard[i][1] == msg[1] and
                self.heard[i][2] == msg[2]):
                self.PC -= 2
                return
                
        self.heard[self.heardp] = msg
        self.heardp += 1

    def loop(self):
        self.count += 1 # fake delay
        if (self.count < 100):
            self.PC -= 1
            return
        self.count = 0
        self.heard = 3 * [(0x00, 0x00, 0x00, 0)] # msg1,2,3,dist
        self.heardp = 0
        self.set_color(0,0,0)
        self.msgrx_reset()
        
