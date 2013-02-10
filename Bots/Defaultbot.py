
"""
Defaultbot 

Defaultbot is the minimal, Kilobot inheriting bot.

It loops indefinitely.

"""



from Kilobot import *

def load(sim):
    return Defaultbot(sim)

class Defaultbot(Kilobot): 
    def __init__(self, sim):
        Kilobot.__init__(self, sim)
        self.program = [self.loop0]
