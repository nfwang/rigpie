 
import maya.cmds as cmds
import maya.mel as mel
import json
import os

from os.path import exists

import rigpie.pylib.attribute as attribute_pylib

def fbx(jointNode="Root", geoNode="geo", rigNode="rig", path=None):
    ''' generate a fbx from a rig'''
    
    if not cmds.objExists(rigNode):
        cmds.error("export.fbx(): rigNode '{}' not found in scene.".format(rigNode))
        return False   

    if not cmds.objExists(geoNode):
        cmds.error("export.fbx(): geoNode '{}' not found in scene.".format(geoNode))
        return False

    if not cmds.objExists(jointNode):
        cmds.error("export.fbx(): jointNode '{}' not found in scene.".format(jointNode))
        return False
    
    if not path:
        path = ""

        maya_path = cmds.file(sceneName=True, query=True)
        if not maya_path:
            cmds.error("export.fbx(): Please save your scene into the proper folder structure before export.")
            return False
        
        maya_path_tokens = maya_path.split("/")
        asset_name = maya_path_tokens[7]
    
        for ii in range(9):
            path += maya_path_tokens[ii] + "/"
            
        path += "export"
        
        # if the path doesnt exist, create it.
        if not exists(path):
            os.mkdir(path)
            
        path += "/SK_{}.fbx".format(asset_name)

        
    # Delete joint constraints
    parent_constraints = cmds.listRelatives(jointNode, allDescendents=True, type="parentConstraint")
    orient_constraints = cmds.listRelatives(jointNode, allDescendents=True, type="orientConstraint")
    scale_constraints = cmds.listRelatives(jointNode, allDescendents=True, type="scaleConstraint")    
    
    cmds.delete(parent_constraints)
    cmds.delete(orient_constraints)
    cmds.delete(scale_constraints)
    
    # Disconnect connections for clean export.
    for attr in cmds.listAttr(geoNode):
        try:
            attribute_pylib.breakConnection(geoNode+"."+attr)
        except:
            pass
            
    for attr in cmds.listAttr(jointNode):
        try:
            attribute_pylib.breakConnection(jointNode+"."+attr)
        except:
            pass


    # Move "geo" group to world space
    cmds.parent("{}|{}".format(rigNode, geoNode), world=True)

    # Create New Bind Pose on skincluster
    cmds.delete(cmds.ls(type="dagPose"))
    cmds.dagPose(jointNode, bindPose=True, save=True, selection=True)
    
    # Get fbx path from maya path
    cmds.select(jointNode)
    cmds.select(geoNode, add=True)
    print ("export.fbx(): Saving Export Rig to: {}".format(path))
    
    
    # Export fbx on geo and export skeleton
    mel.eval('FBXExport -caller FBXMayaTranslator -s 1 -f "{}" -exportFormat "fbx;v=0"'.format(path))


