 
import maya 
import maya.cmds as cmds

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Vector

import rigpie.pylib.constraints as constraints_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.mayatransform as mayatransform_pylib


def setSpaceDrivenKey(driver, driven, addLocal=False):
    addLocal = int(addLocal)
    
    for driver_index in range( len(driven) ):
        for current_driven in range( len(driven) ):
            if current_driven == driver_index:
                cmds.setDrivenKeyframe(driven[current_driven], currentDriver=driver, value=1, driverValue=driver_index)
            else:
                cmds.setDrivenKeyframe(driven[current_driven], currentDriver=driver, value=0, driverValue=driver_index)
    
    if addLocal:
        for driver_index in range( len(driven) ):
            cmds.setDrivenKeyframe( driven[driver_index], currentDriver=driver, value=0, driverValue=len(driven))

def createSpaceSwitch(ctrl, parents, ctrlParent="", nicenames="", type="parent", addLocal=False, attrNode=None, attrName="space", maintainOffsets = [], default=0, blendAttr=False ):
    '''
        ctrl: control to get the space
        parents: list of transform to swap spaces to
        ctrlParent: the transform that will get the constraints
        nicenames: list of enums for space switch
        type: constraint type "parent" or "orient"
        addLocal: create a local space (space to it's existing parent)
        attrNode: put the space switch attr on this node
        attrName: name for space swtich attr "space" is default.
        default: default enum value.
        
    '''
    
    # if no parent is supplied, just use the parent of the control
    if ctrlParent == "":
        ctrlParent = cmds.listRelatives(ctrl, p=True)[0]
    
    # add local automatically adds a "local" enum to the switch
    # this will set all of the parent/orient constraints to 0 allowing the control to follow it's native parent
    if addLocal:
        nicenames = nicenames +  ":local"

    nicenames_list = nicenames.split(":")

    if not attrNode:
        attrNode = ctrl
        
    cmds.addAttr( attrNode, ln=attrName, at="enum", en=nicenames, defaultValue=default, keyable=True )
    
    switchAttr = attrNode+"."+attrName
    driven = []
    
    for pp in range( len(parents) ):
        parent = parents[pp]
        
        if type == "parent":
            con, hook = constraints_pylib.parentConstraintMaintainOffset( parent, ctrlParent, descriptionSuffix=nicenames_list[pp].capitalize())
        else:
            con, hook = constraints_pylib.orientConstraintMaintainOffset( parent, ctrlParent, descriptionSuffix=nicenames_list[pp].capitalize())

        if maintainOffsets:
            if maintainOffsets[pp] == 0:
                for a in ['tx','ty','tz','rx','ry','rz']:
                    cmds.setAttr (f"{hook}.{a}", 0)
            
        cmds.setAttr( con+"."+hook+"W"+str(pp), 0 )
        driven.append( con+"."+hook+"W"+str(pp) )
        
    setSpaceDrivenKey(switchAttr, driven, addLocal=addLocal )
    cmds.setAttr(switchAttr, default)

    # add a attribute to blend the space switch
    if blendAttr:
        attr = attrNode + ".spaceBlend"
        attribute_pylib.add(attr, type="float", value=1)
        
        space_parent = cmds.listRelatives(ctrlParent, parent=True)[0]
        
        # local space transform
        blend_hook_name = MayaName(ctrlParent)
        blend_hook_name.descriptor += "BlendHook"
        blend_hook_name.category = "Null"
        
        blend_hook = cmds.createNode("transform", name=blend_hook_name, parent=space_parent)
        xform_pylib.align(blend_hook, ctrl)
        
        ctrl_parent_name = MayaName(ctrlParent)
        ctrl_parent_name.descriptor += "Blend"
        
        blend_parent = cmds.createNode("transform", name=ctrl_parent_name, parent=space_parent)
        xform_pylib.align(blend_parent, ctrl)
        cmds.parent(ctrl, blend_parent)
        
        blend_matrix_name = MayaName(ctrl_parent_name)
        blend_matrix_name.category = "Blendmatrix"
        blend_matrix = cmds.createNode("blendMatrix", name=blend_matrix_name)
        
        cmds.connectAttr(blend_hook+".xformMatrix", blend_matrix+".target[0].targetMatrix")
        cmds.connectAttr(ctrlParent+".xformMatrix", blend_matrix+".target[1].targetMatrix")
        
        cmds.connectAttr(blend_matrix+".outputMatrix", blend_parent+".offsetParentMatrix")
        cmds.connectAttr(attr, blend_matrix+".target[1].weight")
        
        cmds.setAttr(blend_matrix + ".target[1].useScale", 0)
        cmds.setAttr(blend_matrix + ".target[1].useShear", 0)
        
        cmds.setAttr(blend_parent+".translate", 0, 0, 0, type="float3")
        cmds.setAttr(blend_parent+".rotate", 0, 0, 0, type="float3")
                    
        if type == "orient":
            cmds.setAttr(blend_matrix + ".target[1].useTranslate", 0)
        

def proximityPin(nodes, mesh, maintainOffset=True):
    ''' given a list of nodes use maya's proximity pin to pin to mesh '''
    
    proxy_pin_name = MayaName()
    proxy_pin_name.descriptor = mesh
    proxy_pin_name.category = "Proximitypin"
    
    proxy_pin = cmds.createNode("proximityPin", name=proxy_pin_name)
    
    pin_transforms = []
    for ii, node in enumerate(nodes):
        # set the input matrix
        cmds.connectAttr(node+".worldMatrix", "{}.inputMatrix[{}]".format(proxy_pin, ii))
        world_matrix = cmds.getAttr("{}.inputMatrix[{}]".format(proxy_pin, ii))
        cmds.disconnectAttr(node+".worldMatrix", "{}.inputMatrix[{}]".format(proxy_pin, ii))
        cmds.setAttr("{}.inputMatrix[{}]".format(proxy_pin, ii), world_matrix, type="matrix")
        
        pin_transform_name = MayaName(node)
        pin_transform_name.descriptor = pin_transform_name.descriptor + mesh + "Proximity"
        pin_transform_name.category = "Null"
        
        pin_transform = cmds.createNode("transform", name=pin_transform_name )
        
        cmds.connectAttr("{}.outputMatrix[{}]".format(proxy_pin, ii), pin_transform+".offsetParentMatrix")
        pin_transforms.append(pin_transform)
        
    cmds.connectAttr(mesh+".worldMesh[0]", proxy_pin+".deformedGeometry")
    
    if maintainOffset:
        cmds.setAttr(proxy_pin+".offsetTranslation", 1.0)
        cmds.setAttr(proxy_pin+".offsetOrientation", 1.0)
    
    return proxy_pin, pin_transforms

def createNoFlipAutoTransform(ctrl,
                              referenceTransform,
                              referenceTransformParent=None,
                              frontAxis=[0,1,0],
                              backAxis=[0,-1,0],
                              startAxis=[0,0,-1],
                              upPlaneAxis="YZ",
                              visibilityAttr=None):
    ''' Create an auto space option for an upvector that will flip to a different quadrant when it reaches the ends of the quadrant '''
    
    rotate_axis = "XYZ"
    for axis in upPlaneAxis:
        rotate_axis = rotate_axis.replace(axis, "")
    
    # find the distance from the ctrl to the referenceTransform
    ctrl_position_vector = distance = Vector(cmds.xform(ctrl, translation=True, query=True, worldSpace=True))
    referenceTransform_position_vector = Vector(cmds.xform(referenceTransform, translation=True, query=True, worldSpace=True))
    
    if not referenceTransformParent:
        referenceTransformParent = cmds.listRelatives(referenceTransform, parent=True)
        if referenceTransformParent:
            referenceTransformParent = referenceTransformParent[0]
        else:
            referenceTransformParent = referenceTransform
            
    distance_vector = ctrl_position_vector - referenceTransform_position_vector
    distance = distance_vector.length()
    
    # create the transforms
    ctrl_name = MayaName(ctrl)
    referenceTransform_name = MayaName(referenceTransform)
    
    start_transform_name = MayaName(ctrl)
    start_transform_name.descriptor = start_transform_name.descriptor + referenceTransform_name.descriptor + "Up"
    start_transform_name.category = "Null"
    start_transform = None
    
    front_transform_name = MayaName(ctrl)
    front_transform_name.descriptor = front_transform_name.descriptor + referenceTransform_name.descriptor + "Front"
    front_transform_name.category = "Null"
    front_transform = None

    back_transform_name = MayaName(ctrl)
    back_transform_name.descriptor = back_transform_name.descriptor + referenceTransform_name.descriptor + "Back"
    back_transform_name.category = "Null"
    back_transform = None

    
    # if there is a component_option, then make a locator with the visibility attached to that component_option
    if visibilityAttr:
        start_transform = mayatransform_pylib.createLocator(name=start_transform_name, parent=referenceTransform, matrix=referenceTransform)
        cmds.connectAttr(visibilityAttr, start_transform+".visibility")
        
        front_transform = mayatransform_pylib.createLocator(name=front_transform_name, parent=referenceTransform, matrix=referenceTransform)
        cmds.connectAttr(visibilityAttr, front_transform+".visibility")
        
        back_transform = mayatransform_pylib.createLocator(name=back_transform_name, parent=referenceTransform, matrix=referenceTransform)
        cmds.connectAttr(visibilityAttr, back_transform+".visibility")
    else:
        start_transform = cmds.createNode(name=start_transform_name, parent=referenceTransform)
        xform_pylib.align(start_transform, referenceTransform)
        
        front_transform = cmds.createNode(name=front_transform_name, parent=referenceTransform)
        xform_pylib.align(front_transform, referenceTransform)
        
        back_transform = cmds.createNode(name=back_transform_name, parent=referenceTransform)
        xform_pylib.align(back_transform, referenceTransform)

    # place the transforms
    start_vector = (Vector(startAxis) * distance).get()
    cmds.setAttr("{}.translate".format(start_transform), start_vector[0], start_vector[1], start_vector[2], type="float3")
    
    front_vector = (Vector(frontAxis) * distance).get()
    cmds.setAttr("{}.translate".format(front_transform), front_vector[0], front_vector[1], front_vector[2], type="float3")
    
    back_vector = (Vector(backAxis) * distance).get()
    cmds.setAttr("{}.translate".format(back_transform), back_vector[0], back_vector[1], back_vector[2], type="float3")

    # conditions to check if the reference is past 90 and -90
    front_transform_name.category = "Condition"
    front_transform_condition = cmds.createNode("condition", name=front_transform_name)
    cmds.setAttr(front_transform_condition+".operation", 2)
    cmds.setAttr(front_transform_condition+".secondTerm", 88)
    cmds.setAttr(front_transform_condition+".colorIfTrueR", 2)
    cmds.setAttr(front_transform_condition+".colorIfFalseR", 0)

    back_transform_name.category = "Condition"
    back_transform_condition = cmds.createNode("condition", name=back_transform_name)
    cmds.setAttr(back_transform_condition+".operation", 5)
    cmds.setAttr(back_transform_condition+".secondTerm", -88)
    cmds.setAttr(back_transform_condition+".colorIfTrueR", 1)
    cmds.setAttr(back_transform_condition+".colorIfFalseR", 0)

    space_picker_name = MayaName(ctrl)
    space_picker_name.descriptor = start_transform_name.descriptor + referenceTransform_name.descriptor + "Picker"
    space_picker_name.category = "Plusminusaverage"
    
    space_picker = cmds.createNode("plusMinusAverage", name=space_picker_name)
    
    cmds.connectAttr(front_transform_condition+".outColorR", space_picker+".input1D[0]")
    cmds.connectAttr(back_transform_condition+".outColorR", space_picker+".input1D[1]")

    # transform to track the driver and ignore joint orient
    reference_name = MayaName(ctrl)
    reference_name.descriptor = start_transform_name.descriptor + referenceTransform_name.descriptor + "NoFlip"
    reference_name.category = "Null"
    reference = cmds.createNode("transform", name=reference_name, parent=referenceTransformParent)
    cmds.setAttr(reference+".rotateOrder", cmds.getAttr(referenceTransform+".rotateOrder"))
    
    cmds.parentConstraint(referenceTransform, reference)

    cmds.connectAttr("{}.rotate{}".format(reference, rotate_axis), front_transform_condition+".firstTerm")
    
    # check to see if there's a unitConversion and if there is, use that output.
    reference_transform_attr = cmds.listConnections(front_transform_condition+".firstTerm", source=True, plugs=True)[0]
    
    cmds.connectAttr(reference_transform_attr, back_transform_condition+".firstTerm")

    # transform for space switching
    space_switch_name = MayaName(ctrl)
    space_switch_name.descriptor = start_transform_name.descriptor + referenceTransform_name.descriptor + "Space"
    space_switch_name.category = "Null"
    space_switch = cmds.createNode("transform", name=space_switch_name, parent=referenceTransformParent)

    cmds.parentConstraint(start_transform, space_switch)
    cmds.parentConstraint(front_transform, space_switch)
    space_constraint = cmds.parentConstraint(back_transform, space_switch)[0]
    
    space_constraint_attrs = [ "{}.{}W0".format(space_constraint, start_transform), 
                               "{}.{}W1".format(space_constraint, front_transform), 
                               "{}.{}W2".format(space_constraint, back_transform),
    ]

    setSpaceDrivenKey(space_picker+".output1D", space_constraint_attrs)
    
    return space_switch




def constrain_halfway_transforms(controls, hammockTransforms):
    ''' given a list controls constrain the ends to the middles '''
    
    def split_list(l, even, odd):
        def sub(index, l, odd, even):
            try:
                if index % 2 == 0:
                    even.append(l[index])
                else:
                    odd.append(l[index])
            except IndexError: # we've reached the end of the list
                return odd, even
    
            return sub(index+1, l, odd, even) # recursive call by advancing the index
        return sub(0, l, [], [])
    
    even, odd = split_list(controls, [], [])
    
    if len(odd) == 3:
        hammock_transform_name = MayaName(odd[1].name)
        hammock_transform_name.descriptor += "HammockSpace"
        hammock_transform_name.category = "Null"
        
        hammock_transform = cmds.createNode("transform", name=hammock_transform_name)
        xform_pylib.align(hammock_transform, odd[1].name)
        hammockTransforms.append(hammock_transform)
        
        cmds.pointConstraint(odd[0].name, hammock_transform, maintainOffset=True)
        cmds.pointConstraint(odd[2].name, hammock_transform, maintainOffset=True)

        hammock_transform_name = MayaName(even[0].name)
        hammock_transform_name.descriptor += "HammockSpace"
        hammock_transform_name.category = "Null"
        
        hammock_transform = cmds.createNode("transform", name=hammock_transform_name)
        xform_pylib.align(hammock_transform, even[0].name)
        hammockTransforms.append(hammock_transform)

        cmds.pointConstraint(odd[0].name, hammock_transform, maintainOffset=True)
        cmds.pointConstraint(odd[1].name, hammock_transform, maintainOffset=True)

        hammock_transform_name = MayaName(even[1].name)
        hammock_transform_name.descriptor += "HammockSpace"
        hammock_transform_name.category = "Null"
        
        hammock_transform = cmds.createNode("transform", name=hammock_transform_name)
        xform_pylib.align(hammock_transform, even[1].name)
        hammockTransforms.append(hammock_transform)
        
        cmds.pointConstraint(odd[1].name, hammock_transform, maintainOffset=True)
        cmds.pointConstraint(odd[2].name, hammock_transform, maintainOffset=True)
    else:
        half_index = int((len(controls) + 1) / 2)
        
        hammock_transform_name = MayaName(controls[half_index-1].name)
        hammock_transform_name.descriptor += "HammockSpace"
        hammock_transform_name.category = "Null"

        hammock_transform = cmds.createNode("transform", name=hammock_transform_name)
        xform_pylib.align(hammock_transform, controls[half_index-1].name)
        hammockTransforms.append(hammock_transform)
                
        cmds.pointConstraint(controls[0].name, hammock_transform, maintainOffset=True)
        cmds.pointConstraint(controls[-1].name, hammock_transform, maintainOffset=True)

        leftovers = [controls[:half_index], controls[half_index-1:]]
    
        if len(leftovers[0]) == 2:
            return True
    
        constrain_halfway_transforms(leftovers[0], hammockTransforms)
        constrain_halfway_transforms(leftovers[1], hammockTransforms)
    
    return hammockTransforms