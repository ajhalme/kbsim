import pygame
from pygame.locals import *

import sys; sys.path.insert(0, "./lib/")
from pgu import gui


    ##
    ##  KB Simulator Control
    ##


class KBSControl(gui.Table):
    def __init__(self, sim):         
        gui.Table.__init__(self)
        
        config = sim.config

        def fullscreen(btn): pygame.display.toggle_fullscreen()
        def designer(btn): sim.designerform = True
        def restart(btn): sim.restartform = True
        def fps_update(slider): sim.fps = slider.value

        fg = config['uicolor']

        self.tr()

        self.td(gui.Label(" SIMULATION "))

        td_left  = {'padding_left': 25}
        td_right = {'padding_right': 25}

        btn = gui.Switch(value=False,name='fullscreen')
        btn.connect(gui.CHANGE, fullscreen, btn)        
        self.td(gui.Label("full ",color=fg), align=1, style=td_left)
        self.td(btn, align=-1, style=td_right)

        td_styleb = {'padding_left': 5,
                    'padding_right':5,
                    'padding_top': 5,
                    'padding_bottom': 5}

        btn = gui.Button("designer")
        btn.connect(gui.CLICK, designer, btn)        
        self.td(btn, style=td_styleb)

        btn = gui.Button("restart")
        btn.connect(gui.CLICK, restart, btn)        
        self.td(btn, style=td_styleb)

        self.td(gui.Label("FPS:"))
        slider = gui.HSlider(value=sim.fps,min=25,max=config['fpsmax'],size=20,width=120,name='fps')
        self.td(slider)
        slider.connect(gui.CHANGE, fps_update, slider)

    ##
    ##  KB Designer Control
    ##


class KBDControl(gui.Table):
    def __init__(self, designer):         
        gui.Table.__init__(self)
        
        config = designer.config

        def fullscreen(btn): pygame.display.toggle_fullscreen()
        def analyse(btn): designer.analyseform = True # TODO: this could/should be custom events
        def connect(btn): designer.connectform = True
        def execute(btn): designer.executeform = True
        def clear(btn): designer.clearform = True

        fg = config['uicolor']

        self.tr()

        self.td(gui.Label("  DESIGNER  "))

        td_left  = {'padding_left': 25}
        td_right = {'padding_right': 25}

        btn = gui.Switch(value=False,name='fullscreen')
        btn.connect(gui.CHANGE, fullscreen, btn)        
        self.td(gui.Label("full ",color=fg), align=1, style=td_left)
        self.td(btn, align=-1, style=td_right)

        td_styleb = {'padding_left': 5,
                    'padding_right':5,
                    'padding_top': 5,
                    'padding_bottom': 5}

        btn = gui.Button("clear")
        btn.connect(gui.CLICK, clear, btn)        
        self.td(btn, style=td_styleb)

        """
        btn = gui.Button("analyse")
        btn.connect(gui.CLICK, analyse, btn)        
        self.td(btn, style=td_styleb)
        """

        btn = gui.Button("connect")
        btn.connect(gui.CLICK, connect, btn)        
        self.td(btn, style=td_styleb)

        btn = gui.Button("execute")
        btn.connect(gui.CLICK, execute, btn)        
        self.td(btn, style=td_styleb)
