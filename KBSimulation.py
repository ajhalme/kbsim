from pygame import *
from pygame.locals import *

import sys, imp; sys.path.insert(0, "./lib/")
import random

from Vec2d import *
from Kilobot import *
from KBGUI import *
from KBControl import *
                
class KBSimulation:

    def __init__(self, app, config):
        ## Simulation - Conf
        self.app = app
        self.config = config

        ## Simulation - Core
        self.round = 0
        self.running = False
        self.stopped = False
        self.clock = pygame.time.Clock() # to track FPS
        self.fps = self.config['fps']

        ## Simulation - Noise
        self.anoise = config['anoise']
        self.inoise = config['inoise']
        self.hearmin = config['hearmin']
        
        ## Simulation - View
        if (config['randomseed'] != None):
            random.seed(config['randomseed'])
        self.abstract = False
        self.gui = KBGUI(self)
        self.designerform = False
        self.restartform = False

        ## Simulation - Bots
        thebot = None
        if (self.config['form'] == None):
            thebot = imp.load_source("bot", config['program'])
        else:
            thebot = imp.load_source("bot", "./Bots/Renderbot.py")

        self.bots = []
        for i in range(config['n']):
            self.bots.append(thebot.load(self))
        self.setFormation(config['formation'])



    def setFormation(self, formation):
        if formation == "PILED":
            for b in self.bots:
                b.orientation = random.uniform(0,360)
                b.pos = Vec2d(self.config['width']/2 + random.uniform(0,b.secretID), 
                              self.config['height']/2 + random.uniform(0,b.secretID))

        elif formation == "RANDOM":
            xunit = self.config['width'] / 5
            yunit = self.config['height'] / 5
            for b in self.bots:
                b.orientation = random.uniform(0,360)
                b.pos = Vec2d(random.uniform(yunit, 4*yunit), 
                              random.uniform(xunit, 4*xunit))

        elif formation == "LINE":
            for i in range(0,self.config['n']):
                self.bots[i].pos = Vec2d(self.config['width']/2 + i*34, 
                                         self.config['height']/2)
                self.bots[i].orientation = random.uniform(0,360)            
            self.bots[0].orientation = 180 # make first one point left

        elif formation == "CIRCLE":
            deg = 360 / (self.config['n'])
            pi = 3.141592653589793
            radius = (self.bots[0].radius * (self.config['n'] + 5)) / pi
            
            for i,b in enumerate(self.bots):
                b.orientation = random.uniform(0,360)
                b.pos = Vec2d(self.config['width'] / 2, self.config['height'] / 2) 
                b.pos += Vec2d(0, radius).rotated(deg*i)

        else:
            print "Unknown formation '%s' - aborting." % (formation)
            exit(-42)           


    def update_bot_collisions(self, botpairs):
        for (i,j) in botpairs:
            a = self.bots[i]
            b = self.bots[j]
            dist = a.pos.get_distance(b.pos)
            bound = 2 * a.radius
            if dist < 1 + bound:
                overlap = bound - dist
                direction = b.pos - a.pos
                if (direction == Vec2d(0,0)):
                    direction = Vec2d(1,0)
                direction.length = overlap/2
                b.pos = b.pos + direction
                a.pos = a.pos - direction 


    def update_secretNxs(self, botpairs):
        for b in self.bots: b.secretNx = []

        for (i,j) in botpairs:
            a = self.bots[i]
            b = self.bots[j]
            dist = int(a.pos.get_distance(b.pos))
            if (dist <= self.config['near']): 
                a.secretNx.append(j) # secret
                b.secretNx.append(i) #  neighborhood
        

    def update_messaging(self, botpairs):
        for (i,j) in botpairs:
            a = self.bots[i]
            b = self.bots[j]
            dist = int(a.pos.get_distance(b.pos))
            if (a.running and b.running):
                if (dist < a.rradius and a.tx_enabled == 1): # sends
                        inrange = (a.msgtx[0], a.msgtx[1], a.msgtx[2], dist, 0, 1, 0)
                        b.rxtempbuf.append(inrange)
                if (dist < b.rradius and b.tx_enabled == 1):
                        inrange = (b.msgtx[0], b.msgtx[1], b.msgtx[2], dist, 0, 1, 0)
                        a.rxtempbuf.append(inrange)

        if (self.abstract):
            for b in self.bots:
                numheard = min(len(b.rxtempbuf), self.config['rxbufsize'])            
                random.shuffle(b.rxtempbuf) # ordering randomization (RX/TX delays in HW)
                for i in range(0,numheard):
                    if (b.rxbuf[b.rxbufp][self.config['msg_new']] == 0):
                        b.rxbuf[b.rxbufp] = b.rxtempbuf.pop(0)
                        b.rxbufp = (b.rxbufp + 1) % self.config['rxbufsize']
                b.rxtempbuf = [] #reset
            self.noisestat = 1.0

        else: # SNIR
            noiseOK = 0.0
            noiseFAIL = 0.0
            for b in self.bots:
                k = len(b.rxtempbuf)
                if (k == 0):
                    continue
                k -= 1 # autointerference...
                heard = []
                for m in b.rxtempbuf:
                    randy = random.uniform(50.0,100.0) # delay as random default
                    s = randy / (self.anoise + (k * self.inoise))
                    if s >= self.hearmin:                    
                        noiseOK += 1
                        heard.append(m)
                    else:
                        noiseFAIL += 1

                numheard = min(len(heard), self.config['rxbufsize'])            
                random.shuffle(heard) # ordering randomization (RX/TX delays in HW)

                for i in range(0,numheard):
                    if (b.rxbuf[b.rxbufp][self.config['msg_new']] == 0):
                        b.rxbuf[b.rxbufp] = heard.pop(0)
                        b.rxbufp = (b.rxbufp + 1) % self.config['rxbufsize']
                b.rxtempbuf = [] #reset

            if (self.round % 5 == 0): # too hectic otherwise
                self.noisestat = 0.0 if noiseOK + noiseFAIL == 0 else (noiseOK  / (noiseOK + noiseFAIL))
    
    def stepbots(self):
        # run a step of the program on each bot
        for a in self.bots:     
            a.runProgram()

    def designer(self):
        self.config['designer'] = True
        self.running = False

    def restarter(self):
        self.running = False

    def updateUI(self):

        if (self.designerform):
            self.designer()
            self.designerform = False

        if (self.restartform):
            self.restarter()
            self.restartform = False

        # dodge, collision detection on world borders
        self.gui.update_border_collisions() # note: before bot collisions              

      
    def update(self): # called before draw; update variables

        # process bots in pairs, shuffled
        botn = range(len(self.bots))
        botpairs = [(x, y) for x in botn for y in botn if x > y]
        random.shuffle(botpairs)

        # dodge, collision detection on fellow bots
        self.update_bot_collisions(botpairs)

        # reset secret (internal) neighborhood information
        self.update_secretNxs(botpairs)
       
        # messaging (note: position must be fixed before messaging)
        self.update_messaging(botpairs)


    def run(self):
        self.running = True

        # launch ui
        form = gui.Form()
        ui = gui.App()
        ctrl = KBSControl(self)
        c = gui.Container(align=-1,valign=-1)
        c.add(ctrl,0,0)
        ui.init(c)
     
        while self.running:
            self.updateUI()
            if (not self.stopped): 
                self.stepbots()
                self.update()
                self.round += 1
            for e in pygame.event.get():
                self.gui.event(e)
                ui.event(e)
            self.gui.draw()
            ui.paint()
            pygame.display.flip()
            self.clock.tick(self.fps)      

        return self.config # running a sim doesn't change the configuration
