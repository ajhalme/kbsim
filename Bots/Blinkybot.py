
"""
Blinkybot 

Blinkybot is a basic demo bot, demonstrating the programming
model and simple control flow.

Blinkybot performs a roughly 45 degree turn in 10 steps and
then moves forward another 10 steps, all the while toggling
its leds on and off.

"""

from Kilobot import *

def load(sim):
    return Blinkybot(sim)

class Blinkybot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)

        self.x = 0

        self.program = [self.toggle_r,
                        self.turn,
                        self.toggle_g,
                        self.go,
                        self.toggle_b]

    def turn(self):
        self.fullCW()
        self.x += 1
        if (self.x < 10):
            self.PC -= 1

    def go(self):
        self.fullFWRD()
        self.x -= 1
        if (self.x > 0):
            self.PC -= 1
