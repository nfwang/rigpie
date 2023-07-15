 

import maya.cmds as cmds

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Transform, Vector

import rigpie.pylib.attribute as attribute
import rigpie.pylib.xform as xform


def offsetParentMatrixConstraint(parent, child, alignTo="child", zeroChildTransform=True):
    ''' Use Maya's offsetParentMatrix to drive the child with the parent. 
        Default: Align the parent to the child.
        
        A blendmatrix will be created if the child is already being driven by an offsetParentMatrix and the weight attr will be returned.
        
    '''
    
    output = None
    existing_source = cmds.connectionInfo(child+".offsetParentMatrix", sourceFromDestination=True)
    if existing_source is not "":
        # there's already a connection to the offsetParentMatrix
        existing_node, existing_plug = existing_source.split(".")

        if cmds.objectType(existing_node) == "blendMatrix": # add target to existing blendMatrix 
            ii = 0 
            source_plug = cmds.connectionInfo("{}.target[{}].targetMatrix".format(existing_node, ii), sfd=True)
            while source_plug is not "":
                ii += 1
                next_plug = "{}.target[{}].targetMatrix".format(existing_node, ii)
                source_plug = cmds.connectionInfo(next_plug, sfd=True)

            output = next_plug.replace("targetMatrix", "weight")
            child_plug = next_plug
        else:  # create a blendMatrix
            
            source_name = MayaName(existing_node)
            source_name.category = "Blendmatrix"

            blend_matrix = cmds.createNode("blendMatrix", name=source_name)
            child_plug = blend_matrix+".target[1].targetMatrix"
            
            cmds.connectAttr(existing_source, blend_matrix+".target[0].targetMatrix")
            output = child_plug.replace("targetMatrix", "weight")
            cmds.connectAttr(blend_matrix+".outputMatrix", child+".offsetParentMatrix", force=True)
            
    else:
        # align
        if alignTo == "child":
            xform.align(parent, child, ignoreChildren=True)
        elif alignTo == "parent":
            xform.align(child, parent, ignoreChildren=True)
        
        child_plug = child+".offsetParentMatrix"
        
    # convert to childs local space if the child has a parent
    childs_parent = cmds.listRelatives(child, parent=True)

    if childs_parent:
        # use local space by multiplying the inverse matrix of the child's current parent with the new parents worldMatrix.
        
        local_space_matrix_name = MayaName(child)
        local_space_matrix_name.category = "Multmatrix"
        local_space_matrix = cmds.createNode("multMatrix", n=str(local_space_matrix_name))
        
        cmds.connectAttr(parent+".worldMatrix[0]", local_space_matrix+".matrixIn[0]")
        cmds.connectAttr(childs_parent[0]+".worldInverseMatrix[0]", local_space_matrix+".matrixIn[1]")
        cmds.connectAttr(local_space_matrix+".matrixSum", child_plug)
        
        # zero out everything after offsetParentMatrix is connected
        if zeroChildTransform:
            cmds.xform(child, m=list(Transform()))
    else:
        
        cmds.connectAttr(parent+".worldMatrix[0]", child_plug)

        if zeroChildTransform:
            cmds.xform(child, m=list(Transform()))
        

    return output

def connectAttrToConstraint(constraint, attribute, reverse=False):
    ''' Given a two constrained targets and an attribute, connect and invert the weight value of the second target '''
    
    if cmds.objectType(constraint) == "orientConstraint":
        constraint_attr = "targetRotate"
    elif cmds.objectType(constraint) == "parentConstraint":
        constraint_attr = "targetParentMatrix"
        
    target_a = cmds.listConnections("{}.target[0].{}".format(constraint, constraint_attr))[0]
    target_b = cmds.listConnections("{}.target[1].{}".format(constraint, constraint_attr))[0]
    
    target_attr_a = "{}.{}W0".format(constraint, target_a)
    target_attr_b = "{}.{}W1".format(constraint, target_b)
    
    plus_minus_name = MayaName("Cn{}{}_Plusminusaverage".format(constraint, attribute))
        
    plus_minus = cmds.createNode("plusMinusAverage", n=str(plus_minus_name))
    cmds.setAttr("{}.input1D[0]".format(plus_minus), 1)
    cmds.setAttr("{}.operation".format(plus_minus), 2)
    
    if reverse:
        cmds.connectAttr(attribute, target_attr_b)
        cmds.connectAttr(attribute, "{}.input1D[1]".format(plus_minus))
        cmds.connectAttr("{}.output1D".format(plus_minus), target_attr_a)
    else:
        cmds.connectAttr(attribute, target_attr_a)
        cmds.connectAttr(attribute, "{}.input1D[1]".format(plus_minus))
        cmds.connectAttr("{}.output1D".format(plus_minus), target_attr_b)
    

def parentConstraintMaintainOffset(parnt, obj, removeExisting=False, descriptionSuffix=""):
    ''' use transforms to align and use true parenting with constraints with no offsets '''
    
    # If this is true, delete the currently existing constraints
    if removeExisting:
        allcons = []
        for axis in ["tx","ty","tz","rx","ry","rz"]:
            cons = cmds.listConnections(obj+"."+axis)
            if cons != None:
                for cc in cons:
                    if not cc in allcons:
                        allcons.append(cc)

        try: cmds.delete(allcons)
        except: pass

    # Store the current attribute lock state
    locks = attribute.getAttrLocks(obj)
    
    # Unlock the attrs if necessary
    attribute.unlockAndShow(obj,["t","r"])
    
    # Make hook
    parnt_name = MayaName(parnt)
    
    hook_name = MayaName(obj)
    hook_name.descriptor = hook_name.descriptor + parnt_name.side + parnt_name.descriptor + descriptionSuffix + "Hook"
    hook_name.category = "Null"
    
    hook = cmds.createNode("transform", n=hook_name)
    
    # Hide to fix zoom focus issues
    cmds.setAttr(hook+".v", 0)
    attribute.lockAndHide(hook, ['v'])
    
    xform.align(hook, obj)
    pcon = cmds.parentConstraint(hook, obj )[0]
    
    cmds.parent(hook, parnt)
    
    # Set the current attribute lock state
    attribute.setAttrLocks(obj, locks)
    return pcon, hook
    
def parentConstraint(parnt, obj, mo=False):
    ''' parentConstraint unlocks everything, constrains then puts all the locked channels back '''

    # Store the current attribute lock state
    locks = attribute.getAttrLocks(obj)
    
    # Unlock the attrs if necessary
    attribute.unlockAndShow(obj,["t","r"])
    
    # constrain
    pcon = cmds.parentConstraint(parnt, obj, mo=mo )[0]
    
    # Set the current attribute lock state
    attribute.setAttrLocks(obj, locks)
    return pcon

def orientConstraintMaintainOffset(parnt, obj, descriptionSuffix=""):
    ''' use transforms to align and use true parenting with constraints with no offsets '''
    
    # Store the current attribute lock state
    locks = attribute.getAttrLocks(obj)
    attribute.unlockAndShow(obj, ["r"])
    
    # Make hook
    parnt_name = MayaName(parnt)
    
    hook_name = MayaName(obj)
    hook_name.descriptor = hook_name.descriptor + parnt_name.descriptor + descriptionSuffix + "Hook"
    hook_name.category = "Null"
    
    hook = cmds.createNode("transform", n=hook_name)
    
    xform.align(hook, parnt)
    xform.align(hook, obj, p=False)
    
    ocon = cmds.orientConstraint(hook, obj)[0]
    
    cmds.setAttr(hook+".v", 0)
    attribute.lockAndHide(hook, ['v'])
   
    cmds.parent(hook, parnt)
    
    # Set the attribute lock state
    attribute.setAttrLocks(obj, locks)
    return ocon, hook

