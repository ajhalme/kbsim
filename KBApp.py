import pygame
from pygame.locals import *

import sys; sys.path.insert(0, "./lib/")
from pgu import gui
from Vec2d import *

from KBGUI import *
from KBSimulation import *
from KBDesigner import *
from KBDialog import *


    ##
    ##  KB Application
    ##


class KBApp(gui.container.Container):
    def __init__(self, config):       
        self.config = config       
        self.running = True
        self.module = None

    def loadmodule(self):
        dmode = self.config['designer']
        smode = not dmode
        dialog = self.config['dialog']

        # designer
        if dmode and not dialog:
            self.module = KBDesigner(self, self.config)
        elif dmode and dialog:
            self.module = KBDDialog(self.config)
        # simulation
        elif smode and not dialog:
            self.module = KBSimulation(self, self.config)
        elif smode and dialog:
            self.module = KBSDialog(self.config)

    def run(self):
        while self.running:
            dmode = self.config['designer']
            dialog = self.config['dialog']

            print "Run module:", "designer" if dmode else "sim", "dialog" if dialog else ""
            self.loadmodule()
            self.config = self.module.run()
