 
import maya.cmds as cmds

from rigpie.pylib.rmath import Transform

import rigpie.pylib.xform as xform_pylib

def getTransformLimitLists (node):
    ''' get a list of the value lists and the enabled lists '''
    
    enable_lists = []
    value_lists = []
    
    enable_lists.append(cmds.transformLimits(node, enableTranslationX=True, query=True))
    enable_lists.append(cmds.transformLimits(node, enableTranslationY=True, query=True))
    enable_lists.append(cmds.transformLimits(node, enableTranslationZ=True, query=True))
    
    value_lists.append(cmds.transformLimits(node, translationX=True, query=True))
    value_lists.append(cmds.transformLimits(node, translationY=True, query=True))
    value_lists.append(cmds.transformLimits(node, translationZ=True, query=True))
    
    return (value_lists, enable_lists)
    
def setTransformLimitLists (node, limit_list):
    ''' set the value lists and the enabled lists 
    
        [[[value_x_min, value_x_max], [value_y_min, value_y_max], [value_z_min, value_z_max]], [[enabled_x_min, enabled_x_max], [...], [...]]]
    
    '''
    
    cmds.transformLimits(node, translationX=limit_list[0][0])
    cmds.transformLimits(node, translationY=limit_list[0][1])
    cmds.transformLimits(node, translationZ=limit_list[0][2])

    cmds.transformLimits(node, enableTranslationX=limit_list[1][0])
    cmds.transformLimits(node, enableTranslationY=limit_list[1][1])
    cmds.transformLimits(node, enableTranslationZ=limit_list[1][2])

    
def createLocator(name="locator1", size=1, parent="", matrix=None):
    ''' Create a maya space locator with certain parameters '''
    
    # locator
    locator = cmds.spaceLocator(name=name)[0]
    
    # size
    cmds.setAttr(locator+".localScale", size, size, size, type="float3")
    
    # parent
    if cmds.objExists(parent):
        cmds.parent(locator, parent)
    
    # align
    if isinstance(matrix, Transform):
        cmds.xform(locator, m=list(matrix), worldSpace=True)
    elif matrix and cmds.objExists(matrix):
        xform_pylib.align(locator, matrix)
    
    return locator
    