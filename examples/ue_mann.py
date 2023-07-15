import maya.cmds as cmds

import rigpie.pylib.hik as hik_pylib

from rigpie.templates.biped import Biped

source_path = ((str(__file__)).replace(".py", "")).replace("\\", "/")


class Ue_mann(Biped):
    ''' Unreal Engine mannequin example '''
    
    def __init__(self):
        super().__init__()
        
        self.skeleton_path       = source_path + "/elements/skeleton.mb"
        self.controlshape_path   = source_path + "/elements/control_shapes.mb"
        self.geometry_path       = source_path + "/elements/ue_mann.mb"
        self.skinweights_path    = source_path + "/elements/weights/"

        self.exportRig = True
        
        self.setup() 
        self.registerComponents()

        self.prebuild()
        self.build()
        self.postbuild()


    def registerComponents(self):
        ''' Custom component registration '''
        super().registerComponents()

        
    def prebuild(self):
        ''' custom prebuild, builds all organizational transforms'''
        super().prebuild()

        
    def build(self):
        ''' custom build: builds controls, once done do parenting/constraining between components'''
        super().build()        

        # parenting/constraining between components:
        
        # constrain mesh
        
    def postbuild(self):
        ''' custom postbuild: export rig, load skinweights, control shapes, locking transforms'''
        super().postbuild() 

    def createExportRig(self):
        ''' extra joint parenting '''
        
        super().createExportRig()