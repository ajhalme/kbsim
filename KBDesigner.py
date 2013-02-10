from pygame import *
from pygame.locals import *

import sys; sys.path.insert(0, "./lib/")
import math, random

from Vec2d import *
from Kilobot import *
from KBGUI import *
from KBControl import *

VERSION = 0.1; LEFT = 0; RIGHT = 1

class KBDesigner:
    def __init__(self, app, config):

        self.app = app
        self.config = config

        self.running = False

        self.bots = []
        self.botmove = None
        self.botsel = None
        self.botselpos = None

        self.orientation = 0
        self.links = []
        self.linkc = self.config['n'] * [0]
        self.conns = []
        self.reddots = []

        self.gui = KBGUI(self)
        self.analyseform = False
        self.connectform = False
        self.executeform = False
        self.clearform = False

        for i in range(self.config['n']):
            self.bots.append(Kilobot(self))

        for b in self.bots: # set semi-random initial position and orientation
            b.orientation = random.uniform(0,360)
            b.pos = Vec2d(self.config['width']/2 + random.uniform(0,b.secretID),
                          (self.config['height']*2)/3 + random.uniform(0,b.secretID))

    """
    def parsedatafile(self, targetfile):
        N = 3
        conns = []
        orientation = 0
        with open(targetfile, 'r') as f:
            try:
                for line in f:
                    tok = line.split()
                    if (tok[0] == "KBFORM"):
                        if (tok[1] != str(VERSION)):                    
                            print "Unknown data type, expecting 'KBFORM %2g'" % (VERSION)
                            quit(-42)
                        print ">> Reading data file"
                    elif (tok[0] == "N"):
                        N = int(tok[1])
                    elif (tok[0] == "o"):
                        orientation = int(tok[1])
                    elif (tok[0] == "-"):
                        break
                    elif (tok[0] == "#"):
                        pass
                    else:
                        entry = (int(tok[0]), (int(tok[1]), int(tok[2])), 
                                 (int(tok[3]), int(tok[4])), int(tok[5]))
                        print tok, "    -->   ", entry
                        conns.append(entry)
            except e, msg:
                print "File read failed:", msg
        return N, orientation, conns
        """

    """
    def render(self):
        print ">> Rendering"
        self.reddots = []
        self.links = []
        for i in range(2,self.config['n']):
            rules = None
            for conn in self.conns:
                if (conn[0] == i):
                    rules = conn
                    break
            if (rules == None):
                print "File had no rules for %d, breaking." % (i)
                break
            posA = self.bots[rules[1][0]].pos
            posB = self.bots[rules[2][0]].pos
            posAt = posA.inttup()
            posBt = posB.inttup()
            xA = posAt[0]
            yA = posAt[1]
            xB = posBt[0]
            yB = posBt[1]
            
            rA = rules[1][1]
            rB = rules[2][1]
            ds = posA.get_dist_sqrd(posB)
#            print xA, yA, xB, yB, rA, rB, ds
            Ka = (pow(rA+rB,2) - ds); Ka = 0.01 if Ka < 0 else Ka
            Kb = (ds - pow(rA-rB,2)); Kb = 0.01 if Kb < 0 else Kb # precision...
            K = 0.25 * math.sqrt(Ka * Kb)

            xt = (0.5 * (xB + xA)) + (0.5 * (xB - xA) * ((rA**2) - (rB**2)) / ds)
            yt = (0.5 * (yB + yA)) + (0.5 * (yB - yA) * ((rA**2) - (rB**2)) / ds)
            x1 = xt + (2 * (yB - yA) * K / ds)
            y1 = yt - (2 * (xB - xA) * K / ds)
            x2 = xt - (2 * (yB - yA) * K / ds)
            y2 = yt + (2 * (xB - xA) * K / ds)

#            print i, rules, "posA/B:", posAt, posBt, Vec2d(x1,y1), Vec2d(x2,y2)           
            print " %d:"%(i), Vec2d(x1,y1).inttup(), Vec2d(x2,y2).inttup(), 
            print "choosing", rules[3]
            if (rules[3] == LEFT):
                self.reddots.append(Vec2d(x2,y2))
                self.bots[i].pos = Vec2d(x1,y1)
            else:
                self.reddots.append(Vec2d(x1,y1))
                self.bots[i].pos = Vec2d(x2,y2)

            self.links.append((self.bots[i], self.bots[rules[1][0]]))
            self.links.append((self.bots[i], self.bots[rules[2][0]]))
            """

    def analyser(self):
        print "---\n ANALYSER \n---"
        n = len(self.bots)
        isLinked = filter((lambda x: self.linkc[x] == 1), range(n))
        is2Linked = filter((lambda x: self.linkc[x] == 2), range(n))
        isXLinked = filter((lambda x: self.linkc[x] > 2), range(n))

        print "n = %03d | L0:%03d  L1:%03d  L2:%03d  LX:%03d" % (
            n, n - len(isLinked), len(isLinked), len(is2Linked), len(isXLinked))
        
        if (len(is2Linked + isXLinked) < n):
            print "DEGREE TEST FAILED: some have degree < 2"
        else:
            print "DEGREE TEST OK: all have degree >= 2"


    def connecter(self):
        print "---\n CONNECTER \n---"
        poss = []
        for b in self.bots:
            tup = b.pos.inttup()
            poss.append(tup)

        avg = map((lambda x: x/len(self.bots)), reduce((lambda x,y: [x[0] + y[0], x[1] + y[1]]), poss, [0,0]))
        print  "positions:", poss, "\n", "avg:", avg
        avg = Vec2d(avg)


        # computer kNN and find those closest to the center of the bot mass
        # TODO: make less sloppy; proper generative 2-MST etc


        order = []
        k = self.config['n']
        knns = len(self.bots) * [None]
        for i in range(len(self.bots)):
            bot = self.bots[i]
            dist = avg.get_distance(bot.pos)
            order.append((dist, bot))
                
            knns[i] = []
            for bat in self.bots:
                if (bat == bot): continue
                dist = bot.pos.get_distance(bat.pos)
                knns[i].append([dist, bat])
            knns[i] = sorted(knns[i])[:k] # drop some

        order = sorted(order)

        # create links
        self.links = []
        self.linkc = self.config['n'] * [0]
        
        # startup
        a = order[0][1]
        b = order[1][1]
        pair = (a,b) if (a.secretID > b.secretID) else (b,a)
        self.links.append(pair)
        self.linkc[a.secretID] += 1
        self.linkc[b.secretID] += 1
        
        inplace = [a.secretID, b.secretID] # keep track of the existing form
        dist = int(round(a.pos.get_distance(b.pos)))
        self.conns = [(1, (0, dist), (0, dist))] # start conns
        self.orientation = int((b.pos - a.pos).get_angle())

        for i in map((lambda x: x[1].secretID), order[2:]):
            knn = map((lambda x: x[1].secretID), knns[i])
            bot = self.bots[i]            
            myid = len(inplace)
            temp = None 
            for j in knns[i]: # try to connect every bot to form as directly as possible
                dist = int(round(j[0]))
                k = j[1].secretID
                bat = self.bots[k]
                if (k in inplace):
                    # add links by secretID
                    pair = (bot,bat) if i > k else (bat,bot)
                    self.links.append(pair)
                    self.linkc[bot.secretID] += 1
                    self.linkc[bat.secretID] += 1

                    # add connection by form index
                    if (temp == None):
                        inplace.append(i)
                        temp = [k, inplace.index(k), dist]
                    else:
                        but = self.bots[temp.pop(0)]
                        # trigonometric black magic
                        # we compute the angle of bot in relation to a vector defined by to others (bat and but)
                        angle = (bot.pos - bat.pos).rotated(-(but.pos - bat.pos).get_angle()).get_angle()
                        left = angle < 0
#                        print bat.secretID, "-->", but.secretID, ":", bot.secretID, "L" if angle < 0 else "R"

                        if (left): # we force RIGHTHANDSIDE positioning
                            self.conns.append((myid, temp, [inplace.index(k), dist]))
                        else:
                            self.conns.append((myid, [inplace.index(k), dist], temp))
                        break

        print "conns:"
        for i,conn in enumerate(self.conns):
            print conn

    def clearer(self):
        self.links = []
        self.linkc = self.config['n'] * [0]

    def executor(self):        
        if (self.conns == []):
            print "SANITY CHECK: No conns, won't start execution"
            return            

        print self.orientation

        self.config['form'] = {'version': "KBFORM 0.1",
                               'n' : self.config['n'],
                               'orientation': self.orientation,
                               'rules': self.conns
                               }

        self.config['designer'] = False
        self.running = False

    def updateUI(self):

        # analyse the current form
        if (self.analyseform):
            self.analyser()
            self.analyseform = False

        if (self.connectform):
            self.connecter()
            self.connectform = False

        if (self.clearform):
            self.clearer()
            self.clearform = False

        if (self.executeform):
            self.executor()
            self.executeform = False

        # dodge, collision detection on world borders
        self.gui.update_border_collisions() # note: before bot collisions              

    def update(self): # called before draw; update variables
              
        # process bots in pairs, shuffled
        botn = range(len(self.bots))
        botpairs = [(x, y) for x in botn for y in botn if x > y]
        random.shuffle(botpairs)

        # dodge, collision detection on fellow bots
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

    def run(self):
        self.running = True

        # launch ui
        form = gui.Form()
        ui = gui.App()
        ctrl = KBDControl(self)
        c = gui.Container(align=-1,valign=-1)
        c.add(ctrl,0,0)
        ui.init(c)
     
        while self.running:
            self.updateUI()
            self.update()
            for e in pygame.event.get():
                self.gui.event(e)
                ui.event(e)
            self.gui.draw()
            ui.paint()
            pygame.display.flip()

        return self.config
