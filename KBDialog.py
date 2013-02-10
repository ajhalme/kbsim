import pygame
from pygame.locals import *

import sys; sys.path.insert(0, "./lib/")
from pgu import gui


    ##
    ##  KB Simulator Dialog
    ##


class KBSDialog:
    def __init__(self, config):       
        self.config = config       
        self.running = True

        self.form = gui.Form()
        self.module = gui.Desktop()

        self.module.connect(gui.QUIT, self.module.quit,None)                
        self.main = gui.Container(width=self.config['width'], 
                             height=self.config['height'])
        newdialog = NewKBSDialog(self.config)
        newdialog.connect(gui.CHANGE,self.module.quit, None)
        self.main.add(newdialog, 0, 0)

    def run(self):
        self.module.run(self.main) 

        updates = dict(self.form.items())
        self.config['program'] = updates['program']
        self.config['formation'] = updates['formation']
        self.config['n'] = int(updates['n'])

        self.config['dialog'] = False

        return self.config

class NewKBSDialog(gui.Dialog):
    def __init__(self, config):         
        title = gui.Label("New simulation")       
        t = gui.Table()
        
        t.tr()
        t.td(gui.Label("Bots:"),align=1)
        t.td(gui.Input(name="n",value=config['n'],size=4), align=-1)

        def open_file_browser(arg):
            d = gui.FileDialog()
            d.connect(gui.CHANGE, handle_file_browser_closed, d)
            d.open()

        def handle_file_browser_closed(dlg):
            if dlg.value: program.value = dlg.value

        t.tr()
        t.td( gui.Label('Program:') )
        program = gui.Input(name="program", value=config['program'])
        t.td( program )
        b = gui.Button("Browse...")
        b.connect(gui.CLICK, open_file_browser, gui.CHANGE)
        t.td(b)

        t.tr()
        t.td(gui.Label("Formation:"))
        e = gui.Select(name="formation", value=config['formation'])
        e.add("Circle",'CIRCLE')
        e.add("Piled",'PILED')
        e.add("Line",'LINE')
        e.add("Random",'RANDOM')
        t.td(e, align=-1)

        t.tr()
        e = gui.Button("Okay")
        e.connect(gui.CLICK,self.send,gui.CHANGE)
        t.td(e, align=-1)
        
        e = gui.Button("Cancel")
        e.connect(gui.CLICK,self.close,None)
        t.td(e, align=1)
        
        self.value = None
        gui.Dialog.__init__(self,title,t)    


    ##
    ##  KB Designer Dialog
    ##


class KBDDialog:
    def __init__(self, config):       
        self.config = config       
        self.running = True

        self.form = gui.Form()
        self.module = gui.Desktop()

        self.module.connect(gui.QUIT,self.module.quit,None)                
        main = gui.Container(width=self.config['width'], 
                             height=self.config['height'])
        newdialog = NewKBDDialog(self.config)
        newdialog.connect(gui.CHANGE,self.module.quit, None)
        main.add(newdialog, 0, 0)

    def run(self):
        # self.module.run(self.main) 
        # TODO: proper updates
        """
        updates = dict(form.items())
        self.config['program'] = updates['program']
        self.config['formation'] = updates['formation']
        self.config['n'] = int(updates['n'])
        """

        self.config['dialog'] = False

        return self.config

class NewKBDDialog(gui.Dialog):
    def __init__(self, config):         
        title = gui.Label("New design")       
        t = gui.Table()
        
        t.tr()
        t.td(gui.Label("Bots:"),align=1)
        t.td(gui.Input(name="n",value=config['n'],size=4), align=-1)

        ## TODO: what here?

        t.tr()
        e = gui.Button("Okay")
        e.connect(gui.CLICK,self.send,gui.CHANGE)
        t.td(e, align=-1)
        
        e = gui.Button("Cancel")
        e.connect(gui.CLICK,self.close,None)
        t.td(e, align=1)
        
        self.value = None
        gui.Dialog.__init__(self,title,t)
