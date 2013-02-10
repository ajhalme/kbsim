import pygame
from pygame.locals import *

import sys; sys.path.insert(0, "./lib/")
from pgu import gui
from Vec2d import *

    ##
    ##  KBSimulation graphics
    ##

class KBGUI(gui.container.Container):
    def __init__(self, module):
        
        ## Module
        self.module = module
        self.config = module.config
        self.dmode = self.config['designer']
        self.smode = not self.dmode

        ## UI - Display
        self.screensize = (self.config['width'], 
                           self.config['height'] + self.config['uiheight'])
        self.w, self.h = self.screensize
        self.uiheight = self.config['uiheight']
        pygame.init()
        self.screen = pygame.display.set_mode(self.screensize)
        self.screen.fill(self.config['screenfill'])
        pygame.display.set_caption("Kilobot App")

        ## UI - Elements
        self.font        = pygame.font.Font(None, 15)
        self.trans       = self.config['transparent']
        self.botmove     = None
        self.botsel      = None
        self.noisestat   = 0.0

        self.drawlinks   = True  # c
        self.drawdebug   = True  # d
        self.drawreddots = True  # e
        self.drawgrid    = True  # g
        self.drawinfo    = True  # i
        self.drawradio   = True  # r
        self.drawtraffic = False # t
        self.drawui      = True  # u
        
        if self.dmode:
            self.drawinfo = False
        elif self.smode:
            self.drawgrid = False

    def update_border_collisions(self):
        # dodge, collision detection on borders
        for a in self.module.bots:
            r = a.radius
            x,y = a.pos.inttup()
            if x < r:
                a.pos.__setitem__(0,r)
            if x > (self.w - r):
                a.pos.__setitem__(0,self.w - r)
            if y < self.uiheight + r: # UI bar
                a.pos.__setitem__(1,self.uiheight + r)
            if y > (self.h - r):
                a.pos.__setitem__(1,self.h - r)

    def event(self, e):
        escape = (e.type == KEYUP and e.key == K_ESCAPE)
        if (e.type == QUIT) or escape:
            self.module.running = False
            self.module.app.running = False
        elif e.type == KEYUP:
            self.keyUp(e.key)
        elif e.type == KEYDOWN:
            self.keyDown(e.key)
        elif e.type == MOUSEBUTTONUP:
            self.mouseUp(e.button, e.pos)
        elif e.type == MOUSEMOTION:
            self.mouseMotion(e.buttons, e.pos, e.rel)
                
      
    def draw(self): # draw, lower layers first
        self.screen.fill(self.config['screenfill']) # refresh

        if (self.drawgrid):     
            g = self.config['gridsquare']
            col = self.config['gridcolor']
            ui = self.config['uiheight']
            for i in range(1 + (self.h / g)):
                pygame.draw.line(self.screen, col, (0,ui + i*g), (self.w, ui + i*g))
            for i in range(1 + (self.w / g)):
                pygame.draw.line(self.screen, col, (i*g,0), (i*g, self.h))
        
        if (self.drawradio):     
            if ( self.smode and 
                 (self.module.inoise > 0 or self.module.anoise > 100)):                
                for a in self.module.bots: # draw radio bubble
                    surf = pygame.Surface((a.rradius * 2, a.rradius*2))
                    surf.fill(self.trans)
                    surf.set_colorkey(self.trans)
                    pos = a.pos.inttup()
                    pygame.draw.circle(surf, a.view.colorr +(0,),
                                       (a.rradius,a.rradius), a.rradius)
                    surf.set_alpha(100)
                    self.screen.blit(surf, (pos[0] - a.rradius, pos[1] -a.rradius))
            else:
                for a in self.module.bots: # draw simple radio ranges
                    if (a.tx_enabled == 1):
                        a.view.drawradio(self.screen)

        if (self.smode and self.module.abstract):  # draw a connectivity graph 
            for i in range(0,len(self.module.bots)): # draw an edge if close enough to transmit
                for j in range(i+1, len(self.module.bots)):
                    a = self.module.bots[i]
                    b = self.module.bots[j]
                    dist = a.pos.get_distance(b.pos)
                    bound = a.rradius
                    if dist < bound:
                        pygame.draw.aaline(self.screen, self.config['graphc'],
                                           a.pos.inttup(), b.pos.inttup(), 2)
            for a in self.module.bots: # draw abstraction
                a.view.drawsimple(self.screen) # vertex
        else:            
            for a in self.module.bots: # draw proper bot
                if (self.dmode):
                    degree = self.module.linkc[a.secretID]
                    if (degree == 0):
                        a.view.color = self.config['botcolorbase0']
                    elif (degree == 1):
                        a.view.color = self.config['botcolorbase1']
                    elif (degree == 2):
                        a.view.color = self.config['botcolorbase2']
                    else:
                        a.view.color = self.config['botcolorbasex']

                a.view.draw(self.screen)

        if (self.drawinfo):
            for a in self.module.bots: # draw info: secretID and coords
                a.view.drawinfo(self.screen)

        if (self.drawtraffic):
            for a in self.module.bots:
                a.view.drawtx(self.screen)
            for a in self.module.bots:
                a.view.drawrx(self.screen)

        if (self.drawdebug):
            for a in self.module.bots: # draw debug
                a.view.drawdebug(self.screen)

        if (self.drawui):
            bg = pygame.Surface((self.w, self.config['uiheight'])) 
            bg.fill(self.config['screenfill'])
            col = self.config['uicolor']
            f = self.font.render
            
            self.screen.blit(bg, (0,0)) # bg 
            
            if (self.smode):
                fpsd = f("fps:%3d/%3d" % (self.module.clock.get_fps(), self.module.fps), True, col)
                off = 525
                self.screen.blit(fpsd, (off + 10, 5))

                roundd     = f("round:%06d" % (self.module.round), True, col)
                self.screen.blit(roundd, (off + 10, 15))

                inoised    = f("inoise:%3d" % (self.module.inoise), True, col)
                self.screen.blit(inoised, (off + 95, 5))

                anoised    = f("anoise:%3d" %  (self.module.anoise), True, col)
                self.screen.blit(anoised, (off + 95, 15))

                noisestatd = f("%3d%%" % (int(100*self.module.noisestat)), True, col)
                self.screen.blit(noisestatd, (off + 175, 10))
            elif (self.dmode):
                pass
                

        if (self.drawlinks and self.dmode):
            col1 = self.config['botcolorselg']
            col2 = self.config['botcolorselr']            
            for conn in self.module.links:
                a = conn[0]; b = conn[1]
                diff = a.pos.get_distance(b.pos)
                col = col1 if (diff < self.config['maxdist']) else col2
                pygame.draw.line(self.screen, col, a.pos.inttup(), b.pos.inttup(), 2)
            if (self.botsel != None and self.botselpos != None):
                diff = self.botsel.pos.get_distance(self.botselpos)
                col = col1 if (diff < self.config['maxdist']) else col2
                pygame.draw.line(self.screen, col,
                                 self.botsel.pos.inttup(), 
                                 self.botselpos.inttup(), 2)
            
        if (self.drawreddots and self.dmode):
            for i in range(len(self.module.reddots)):
                r = self.module.reddots[i]
                text = self.font.render("%d" % (i+2), True, (225, 0, 0))
                self.screen.blit(text, r.inttup())                                 


    def keyDown(self, key):
        pass

    def keyUp(self, key):

        if (key == K_a):
            if self.smode:
                self.module.abstract = not self.module.abstract

        elif (key == K_c):
            self.drawlinks = False if self.drawlinks else True

        elif (key == K_d):
            self.drawdebug = False if self.drawdebug else True

        elif (key == K_e):
            self.drawreddots = False if self.drawreddots else True

        elif (key == K_g):
            self.drawgrid = False if self.drawgrid else True

        elif (key == K_h): # show          
            print "SHOW"

        elif (key == K_i):
            self.drawinfo = False if self.drawinfo else True

        elif (key == K_k):
            if self.smode:
                self.module.fps -= 5
                self.module.fps = 0 if self.module.fps < 0 else self.module.fps
        elif (key == K_l):
            if self.smode:
                self.module.fps += 5
                out = self.module.fps > self.config['fpsmax']
                self.module.fps = self.config['fpsmax'] if out else self.module.fps

        elif (key == K_m):
            if self.smode:
                self.module.inoise += 5
                if self.module.inoise > 100: self.module.inoise = 100
        elif (key == K_n):
            if self.smode:
                self.module.inoise -= 5
                if self.module.inoise < 0: self.module.inoise = 0

        elif (key == K_p): # print
            print "PRINT"

        elif (key == K_r):
            self.drawradio = False if self.drawradio else True
        elif (key == K_s):
            if self.smode:
                self.module.stopped = not self.module.stopped
        elif (key == K_t):
            self.drawtraffic = False if self.drawtraffic else True
        elif (key == K_u):
            self.drawui = False if self.drawui else True
                
        elif (key == K_COMMA):
            if self.smode:
                self.module.anoise -= 5
                if self.module.anoise < 100: self.module.anoise = 100
        elif (key == K_PERIOD):
            if self.smode:
                self.module.anoise += 5
                if self.module.anoise > 200: self.module.anoise = 200

        elif (key == K_PAGEDOWN):
            for b in self.module.bots:
                b.pos = b.pos.rotated(90) + Vec2d(self.h,0)
                b.orientation += 90 

        elif (key == K_PAGEUP):
            for b in self.module.bots:
                b.pos = b.pos.rotated(-90) + Vec2d(0,self.w)
                b.orientation -= 90 


    def mouseMotion(self, buttons, pos, rel):
        if (self.botmove != None):
            self.botmove.pos = Vec2d(pos)
        elif (self.botsel != None):
            self.botselpos = Vec2d(pos)
            
    def mouseUp(self, mbutton, mpos):        
        if (mbutton == 1 and self.dmode): # connect
            if (self.botmove == None):  # one thing at a time
                if (self.botsel == None):
                    for b in self.module.bots:
                        pos = b.pos.inttup()
                        if (pos[0] - b.radius < mpos[0] < pos[0] + b.radius and
                            pos[1] - b.radius < mpos[1] < pos[1] + b.radius):
                            b.view.colorc = self.config['botcoloredge1']
                            if (self.botsel == None):
                                self.botsel = b
                                self.botselpos = b.pos
                                break
                else:
                    bot2 = None
                    for b in self.module.bots:
                        pos = b.pos.inttup()
                        if (pos[0] - b.radius < mpos[0] < pos[0] + b.radius and
                            pos[1] - b.radius < mpos[1] < pos[1] + b.radius):
                            bot2 = b
                            break
                    if (bot2 != None and bot2 != self.botsel):
                        flip =  (self.botsel.secretID > bot2.secretID)
                        pair = (self.botsel, bot2) if flip else (bot2, self.botsel)
                        if pair in self.module.links:
                            self.module.links.remove(pair)
                            self.module.linkc[self.botsel.secretID] -= 1
                            self.module.linkc[bot2.secretID] -= 1
                        else:                            
                            self.module.links.append(pair)
                            self.module.linkc[self.botsel.secretID] += 1
                            self.module.linkc[bot2.secretID] += 1

                    self.botsel.view.colorc = self.config['botcoloredge0']              
                    self.botsel = None

        elif (mbutton == 3): # move
            if (self.botsel == None): # one thing at a time
                if (self.botmove == None):
                    for b in self.module.bots:
                        pos = b.pos.inttup()
                        if (pos[0] - b.radius < mpos[0] < pos[0] + b.radius and
                            pos[1] - b.radius < mpos[1] < pos[1] + b.radius):
                            b.view.colorc = self.config['botcoloredge2']
                            if (self.botmove == None):
                                self.botmove = b
                                break
                else:
                    self.botmove.view.colorc = self.config['botcoloredge0']  
                    self.botmove = None

    ##
    ##  Kilobot graphics
    ##


class KilobotView():

    def __init__(self, bot):
        self.bot = bot
        self.module = bot.sim
        self.font = pygame.font.Font(None, 15)

        self.color = self.module.config['botcolorbase0']
        self.colorb = self.module.config['botcolorfeat']
        self.colorc = self.module.config['botcoloredge0']
        self.colorr = self.module.config['botcolorr']

    def drawradio(self, screen): # draw radio
        pygame.draw.circle(screen, self.colorr, self.bot.pos.inttup(), 
                           self.bot.rradius + 1, 1)

    def draw(self, screen): # draw bot
        pos = self.bot.pos.inttup()

        pygame.draw.circle(screen, self.colorc, pos, self.bot.radius + 1) # edge             
        pygame.draw.circle(screen, self.color, pos, self.bot.radius) # body
        pygame.draw.aaline(screen, self.colorb, pos, self.bot.ffoot().inttup(), 1) # ffoot
        pygame.draw.circle(screen, self.colorb, self.bot.lfoot().inttup(), 2) # lfoot
        pygame.draw.circle(screen, self.colorb, self.bot.rfoot().inttup(), 2) # rfoot

        pygame.draw.circle(screen, self.bot.leds, self.bot.led().inttup(), 3) # rled

    def drawsimple(self, screen): # draw bot
        pygame.draw.circle(screen, self.color, self.bot.pos.inttup(), 5)   # body

    def drawinfo(self, screen): # draw position text
        pos = self.bot.pos.inttup()
        text = self.font.render("%d" % (self.bot.secretID), True, (0, 0, 0))
        screen.blit(text, (pos[0] - 7, pos[1] - 2))

    def drawtx(self, screen): # draw if TXing
        if (self.bot.tx_enabled):
            pos = self.bot.pos.inttup()
            data = (self.bot.msgtx[0] << 16) + (self.bot.msgtx[1] << 8) + (self.bot.msgtx[2])
            msg = "T(%06x)" %  (data)
            text = self.font.render(msg, True, (10, 10, 10))
            screen.blit(text, (pos[0] + self.bot.radius, pos[1] - self.bot.radius))

    def drawrx(self, screen): # draw if RX'd
        if (self.bot.msgrx[self.module.config['msg_new']] == 1):
            pos = self.bot.pos.inttup()
            data = (self.bot.msgrx[0] << 16) + (self.bot.msgrx[1] << 8) + (self.bot.msgrx[2])
            msg = "R(%06x:%2d)" %  (data, self.bot.msgrx[3])
            text = self.font.render(msg, True, (10, 10, 10))
            screen.blit(text, (pos[0] + self.bot.radius + 1, pos[1] - self.bot.radius + 10))

    def drawdebug(self, screen): # draw if there is a debug print
        if (self.bot.debug != ""):
            pos = self.bot.pos.inttup()
            msg = "%2dD(%s)" % (self.bot.secretID, self.bot.debug)
            text = self.font.render(msg, True, (10, 10, 10))
            screen.blit(text, (0, self.module.config['uiheight'] + 12 * self.bot.secretID))
