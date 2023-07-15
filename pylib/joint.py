 

import maya.cmds as cmds

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Transform

import rigpie.pylib.xform as xform
import rigpie.pylib.rmath as rigMath
import rigpie.pylib.curve as curve_pymodule
import rigpie.pylib.constraints as constraints


def isExportJoint(joint):
    ''' Check to see if a joint is considered an export joint '''
    
    if cmds.objectType(joint) != "joint":
        return False
        
    if joint[-3:] == "Jnt":
        return False
    else:
        return True
    
def getExportFromRigJointName(joint):
    ''' Return the export joint string'''

    if "Jnt" not in joint:
        return joint
    
    return joint[:-3]
    
def getRigFromExportJointName(joint):
    ''' Return the rig joint name from the export joint name'''
    
    if "Jnt" in joint:
        return joint
    else:
        return joint + "Jnt"
        

def duplicate(joint, searchReplace=[], appendDescription="", radius=None, hierarchy=True):
    ''' Duplicate a joint and all it's children with a search replace string '''
    
    if hierarchy:
        joint_list = [joint] + cmds.listRelatives(joint, allDescendents=True, type="joint")
    else:
        joint_list = [joint]
    
    duplicate_dictionary = {} # <duplicated>:<original>
    for jj in joint_list:
        name = ""
        if searchReplace:
            name = jj.replace(searchReplace[0], searchReplace[1])
        else:
            duplicate_name = MayaName(joint)
            duplicate_name.descriptor = duplicate_name.descriptor + appendDescription
            name = str(duplicate_name)
            
        duplicate = cmds.createNode("joint", name=name)

        duplicate_dictionary[duplicate] = jj

    # parent
    for duplicate in duplicate_dictionary.keys():
        original = duplicate_dictionary[duplicate]
        original_parent = cmds.listRelatives(original, parent=True)
        
        if original_parent:
            original_parent = original_parent[0]
            duplicated_parent = ""
            if searchReplace:
                duplicated_parent = original_parent.replace(searchReplace[0], searchReplace[1])
            else:
                duplicated_parent_name = MayaName(original_parent)
                duplicated_parent_name.descriptor = duplicated_parent_name.descriptor + appendDescription
                duplicated_parent = str(duplicated_parent_name)            

            if cmds.objExists(duplicated_parent):
                cmds.parent(duplicate, duplicated_parent)
            else:
                cmds.parent(duplicate, original_parent)

        # joint attributes
        joint_orient = cmds.getAttr(jj+".jointOrient")[0]
        cmds.setAttr(duplicate+".jointOrient", joint_orient[0], joint_orient[1], joint_orient[2], type="float3")

        preferred_angle = cmds.getAttr(jj+".preferredAngle")[0]
        cmds.setAttr(duplicate+".preferredAngle", preferred_angle[0], preferred_angle[1], preferred_angle[2], type="float3")
        
        if radius:
            cmds.setAttr(duplicate+".radius", radius)
        else:
            cmds.setAttr(duplicate+".radius", cmds.getAttr(jj+".radius"))
            
        for attr in ["translate", "rotate", "scale"]:
            for axis in ["X", "Y", "Z"]:
                cmds.setAttr("{}.{}{}".format(duplicate, attr, axis), cmds.getAttr("{}.{}{}".format(original, attr, axis)))

        # shear
        for axis in ["XY", "XZ", "YZ"]:
            cmds.setAttr("{}.shear{}".format(duplicate, axis), cmds.getAttr("{}.shear{}".format(original, axis)))
                
    return list(duplicate_dictionary.keys())
    
def getLongAxisVector(jnt):
    ''' Get the long axis vector based on the t value '''

    translate_x = abs(cmds.getAttr(jnt+".translateX"))
    translate_y = abs(cmds.getAttr(jnt+".translateY"))
    translate_z = abs(cmds.getAttr(jnt+".translateZ"))
    
    if ( translate_x >= translate_y) and (translate_x >= translate_z):
        if cmds.getAttr(jnt+".translateX") < 0:
            return [-1, 0, 0]
        else:
            return [1, 0, 0]
            
    elif (translate_y >= translate_x) and (translate_y >= translate_z):
        if cmds.getAttr(jnt+".translateY") < 0:
            return [0, -1, 0]
        else:
            return [0, 1, 0]
    else:
        if cmds.getAttr(jnt+".translateZ") < 0:
            return [0, 0, -1]
        else:
            return [0, 0, 1]

    
def getLongAxis(jnt):
    ''' Get the long axis based on the t value.'''
    
    translate_x = abs(cmds.getAttr(jnt+".translateX"))
    translate_y = abs(cmds.getAttr(jnt+".translateY"))
    translate_z = abs(cmds.getAttr(jnt+".translateZ"))
    
    if ( translate_x >= translate_y) and (translate_x >= translate_z):
       return "X"
    elif (translate_y >= translate_x) and (translate_y >= translate_z):
       return "Y"
    else:
       return "Z"
       

    
def attachToMotionPath(joints, curve, rail, aimVector=[1,0,0], upVector=[0,1,0], parameterizeCurve=True):
    
    if parameterizeCurve:
        cmds.rebuildCurve(curve, keepRange=0)
        cmds.rebuildCurve(rail, keepRange=0)
    
    attach_nulls = []
    up_nulls = []

    # determine the front and up axis
    frontAxis = "x"
    upAxis = "y"
    
    if aimVector[1]:
        frontAxis = "y"
    elif aimVector[2]:
        frontAxis = "z"

    if (aimVector[0] < 1) or (aimVector[1] < 1) or (aimVector[2] < 1):
        inverseFront = True

    if upVector[1]:
        upAxis = "y"
    elif upVector[2]:
        upAxis = "z"

    if (upVector[0] < 1) or (upVector[1] < 1) or (upVector[2] < 1):
        inverseUp = True
    
    for joint in joints:
        # get parameter for rail
        param = curve_pymodule.getParameterClosestCurve(joint, curve)
        
        # get the name if it is a maya name else just append "_up"
        try:
            attach_name = MayaName(joint)
            attach_name.descriptor = attach_name.descriptor + "Attach"
            attach_name.category = "Null"
            
        except:
            up_name = joint + "_attach"

        try:
            up_name = MayaName(joint)
            up_name.descriptor = up_name.descriptor + "AttachUp"
            up_name.category = "Null"
            
        except:
            up_name = joint + "_up"

        # up null
        up = cmds.createNode("transform", name=up_name)
        up_pos = cmds.pointOnCurve( rail, parameter=param)

        cmds.xform(up, translation=list(up_pos), worldSpace=True)
        curve_pymodule.attachNodeToCurve(rail, up)

        # we need to create an attach null in order to keep the joints in a chain.
        attach = cmds.createNode("transform", name=attach_name)
        xform.align(attach, joint)
        
        curve_pymodule.attachNodeToCurve( curve, 
                                          attach, 
                                          worldUpType="object", 
                                          worldUpObject=up, 
                                          frontVector=aimVector, 
                                          upVector=upVector, 
                                          inverseFront=inverseFront, 
                                          inverseUp=inverseUp
        )
        
        constraints.offsetParentMatrixConstraint(attach, joint)
        
        # zero out the joint
        cmds.xform(joint, matrix=list(Transform()))
