 
import maya.cmds as cmds
from rigpie.pylib.rmath import Vector, Transform

ROTATION_ORDER_LIST = ["xyz","yzx","zxy","xzy","yxz","zyx"]

def alignPosition(node, target, ignoreChildren=False, freezeTransform=False):
    ''' Align two objects positions in world space '''
    source_pos = {}
    children = cmds.listRelatives(node, children=True, type="transform")
    if ignoreChildren and children:
        for child in children:
            source_pos[child] = cmds.xform(child, translation=True, worldSpace=True, query=True)
    
    t = None
    # if target is a string, treat as a maya object, else a float3
    if isinstance(target, str):
        t = cmds.xform(target, worldSpace=True, t=True, q=True)
    elif isinstance(target, Vector):
        t = list(target)
    else:
        t = target
        
    cmds.xform(node, worldSpace=True, t=t)
    
    if ignoreChildren:
        for child in source_pos.keys():
            cmds.xform(child, translation=source_pos[child], worldSpace=True)
            
    if freezeTransform:
        cmds.makeIdentity(node, apply=True, translate=1, rotate=1, scale=1, normal=0)
    
    return True

def alignRotation(node, target, ignoreChildren=False, freezeTransform=False):
    ''' Align two object's rotation in world space '''
    
    source_rots = {}
    children = cmds.listRelatives(node, children=True, type="transform", fullPath=True)
    
    if ignoreChildren and children:
        for child in children:
            source_rots[child] = [cmds.xform(child, rotation=True, worldSpace=True, query=True), ROTATION_ORDER_LIST[cmds.getAttr(child+".rotateOrder")]]
    
    r = None
    rotateOrder = "xyz"
    if isinstance(target, str):
        r = cmds.xform(target, worldSpace=True, rotation=True, query=True)
        rotateOrder=ROTATION_ORDER_LIST[cmds.getAttr(target+".rotateOrder")]
    elif isinstance(target, Vector):
        r = list(target)
    else:
        r = target
    
    cmds.xform(node, rotation=r, rotateOrder=rotateOrder, worldSpace=True)

    # put the children rotations back
    if ignoreChildren:
        for child in source_rots.keys():
            cmds.xform(child, rotation=source_rots[child][0], worldSpace=True, rotateOrder=source_rots[child][1])

    if freezeTransform:
        cmds.makeIdentity(node, apply=True, translate=1, rotate=1, scale=1, normal=0)

    
    return True

# transforms
def align( node, target, r=True, p=True, ignoreChildren=False, freezeTransform=False):
    if (r and p):
        source_mats = {}
        
        children = cmds.listRelatives(node, children=True, type="transform", fullPath=True)
        if ignoreChildren and children:
            for child in children:
                source_mats[child] = cmds.xform(child, matrix=True, worldSpace=True, query=True)
        
        m = None
        if isinstance(target, str):
            m = cmds.xform(target, matrix=True, query=True, worldSpace=True)
        elif isinstance(target, Transform):
            m = list(target)
        else:
            m = target
            
        cmds.xform(node, matrix=m, worldSpace=True)
        
        # put the children rotations back
        if ignoreChildren:
            for child in source_mats.keys():
                cmds.xform(child, matrix=source_mats[child], worldSpace=True)
        
    elif r:
        alignRotation(node, target, ignoreChildren=ignoreChildren, freezeTransform=freezeTransform)
    else:
        alignPosition(node, target, ignoreChildren=ignoreChildren, freezeTransform=freezeTransform)