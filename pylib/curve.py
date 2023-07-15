 
import maya.cmds as cmds
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Vector

import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.xform as xform_pylib
import rigpie.pylib.skincluster as skincluster_pylib

def getParameterClosestCurve(node, curve):
    ''' Return the curve parameter that is closest in worldspace to the node '''

    # Find the position on the curve
    npoc = cmds.createNode("nearestPointOnCurve")
    cmds.connectAttr(curve+".worldSpace", npoc+".inputCurve")
    
    # Set the position of the node
    pos = cmds.xform(node, query=True, translation=True, worldSpace=True)
    cmds.setAttr( npoc+".inPosition", pos[0], pos[1], pos[2], type="float3" )
    
    # Get the parametric value along the curve
    param = cmds.getAttr(npoc+".result.parameter")
    
    # Delete the nearestPointOnCurve object
    cmds.delete(npoc)
    
    return param


def attachNodeToCurve( curve, node, worldUpType="vector", worldUpVector=[0,1,0], worldUpObject="", follow=True, aimVector=[1,0,0], upVector=[0,1,0], inverseUp=False, inverseFront=False, bank=False, translationOnly=False):
    ''' Attach the node to the curve '''
    
    # Check to see if curve is a xform
    if ( cmds.objectType(curve) == "transform"):
        curve = cmds.listRelatives(curve, shapes=True)[0]

    if cmds.objectType(curve) != "nurbsCurve":
        print ( "curve.attachNodesToCurve(): %s is not a nurbsCurve!".format(curve) )
        return False
    
    param = getParameterClosestCurve(node, curve)

    aimAxis = "x"
    if aimVector[1]:
        aimAxis = "y"
    elif aimVector[2]:
        aimAxis = "z"

    upAxis = "x"
    if upVector[1]:
        upAxis = "y"
    elif aimVector[2]:
        upAxis = "z"

    flipped_transform = None
    
    # attach node to the path
    if worldUpType == "vector":

        # if it's negative, then create an intermediate transform
        if (aimVector[0] < 0) or (aimVector[1] < 0) or (aimVector[2] < 0):
            flipped_transform = cmds.createNode("transform", name=node+"MotionPathNull")
            parent_constraint = cmds.parentConstraint( flipped_transform, node )[0]
            node = flipped_transform
            
            # find the rotation vector
            if upAxis == "x":
                cmds.setAttr(parent_constraint+".target[0].targetOffsetRotateX", 180)
            elif upAxis == "y":
                cmds.setAttr(parent_constraint+".target[0].targetOffsetRotateY", 180)
            else:
                cmds.setAttr(parent_constraint+".target[0].targetOffsetRotateZ", 180)

        mpath = cmds.pathAnimation ( node, 
                                     curve, 
                                     worldUpType=worldUpType, 
                                     worldUpVector=worldUpVector, 
                                     fractionMode=False, 
                                     follow=follow, 
                                     followAxis=aimAxis, 
                                     upAxis=upAxis, 
                                     inverseUp=inverseUp, 
                                     inverseFront=inverseFront, 
                                     bank=bank
        )
    elif worldUpType == "object":
        mpath = cmds.pathAnimation ( node, 
                                     curve, 
                                     worldUpType=worldUpType, 
                                     worldUpObject=worldUpObject, 
                                     fractionMode=False, 
                                     follow=follow, 
                                     followAxis=aimAxis, 
                                     upAxis=upAxis, 
                                     inverseUp=inverseUp, 
                                     inverseFront=inverseFront, 
                                     bank=bank
    )
    elif worldUpType == "objectrotation":
        mpath = cmds.pathAnimation ( node, 
                                     curve, 
                                     worldUpType=worldUpType, 
                                     worldUpVector=worldUpVector, 
                                     worldUpObject=worldUpObject, 
                                     fractionMode=False, 
                                     follow=follow, 
                                     followAxis=aimAxis, 
                                     upAxis=upAxis, 
                                     inverseUp=inverseUp, 
                                     inverseFront=inverseFront, 
                                     bank=bank
        )
    
    # Disconnect the keys off of the uValue
    connections = cmds.listConnections(mpath+".uValue", plugs=True, connections=True)
    cmds.disconnectAttr(connections[1], connections[0])
    
    # Move the object to where it was
    cmds.setAttr(mpath+".uValue",  param)
    
    if translationOnly:
        attribute_pylib.breakConnection(node+".rotateX")
        attribute_pylib.breakConnection(node+".rotateY")
        attribute_pylib.breakConnection(node+".rotateZ")
    
    return mpath, param, flipped_transform

def createNodesAlongCurve(curve, orientTarget, count, name="CnCurveJnt", type="joint", parameterizeCurve=True, aimVector=[1, 0, 0], upVector=[0,1,0]):
    ''' Create count number of nodes along the curve, with the upvector pointing at the rail. 
        
        targetOrient: can be a node (aligns all nodes to that node) or a spline (uses as a rail)
        parameterizeCurve: rebuild the curve to be 0-1
        keepAlive: Leave all the aims and attachments
        
    '''
    
    rail = None
    
    if isinstance(aimVector, Vector):
        aimVector = list(aimVector)
        
    if isinstance(upVector, Vector):
        upVector = list(upVector)
        
        
    if cmds.objectType(curve) == "nurbsCurve":
        rail = orientTarget
    elif cmds.objectType(orientTarget) in ["transform", "joint"]:
        shape = cmds.listRelatives(orientTarget, shapes=True)
        if shape and cmds.objectType(shape[0]) == "nurbsCurve":
            rail = shape[0]
        else:
            rail = False
    else:
        cmds.error("curve_pylib.createNodesAlongCurve(): Second arg {} not a value object".format(orientTarget))
        return False
    
    if rail == None:
        cmds.error("curve_pylib.createNodesAlongCurve(): Second arg {} not a value object".format(orientTarget))
        return False
    
    if not isinstance(name, MayaName):
        node_name = MayaName(name)
        up_name = MayaName(name)
    else:
        node_name = MayaName(name)
        up_name = MayaName(name)
        
    if parameterizeCurve:
        cmds.rebuildCurve(curve, keepRange=0)
        
        if rail:
            cmds.rebuildCurve(rail, keepRange=0)
    
    up_nodes = []
    parent_dict = {}
    next = None
    nodes = []

    up_name.descriptor = up_name.descriptor + "Up"

    # inverse the aim vector since we're making nodes from end to front
    aimVector = [aimVector[0] * -1, aimVector[1] * -1, aimVector[2] * -1]
    
    for ii in range(count-1, -1, -1):
        max_parameter = cmds.getAttr(curve + ".mmv.max")
        pos_val = cmds.pointOnCurve(curve, parameter=(max_parameter/float(count-1) * float(ii))) 
        
        if rail:
            up_val = cmds.pointOnCurve(rail, parameter=float(ii)/float(count-1))

            up_name.iterator = str(ii)
            up_name.category = "Null"
            up = cmds.createNode("transform", name=up_name)
            cmds.xform(up, translation=up_val, worldSpace=True)
        
        if ii == 0:
            node_name.iterator = ""
        else:
            node_name.iterator = str(ii)
        
        node = cmds.createNode(type, name=node_name)
        cmds.xform(node, translation=pos_val, worldSpace=True)
        
        if rail:
            if next:
                cmds.delete(cmds.aimConstraint(node, next, aimVector=aimVector, upVector=upVector, worldUpType="object", worldUpObject=up))
                parent_dict[next] = node
            else:
                last = node
            
            cmds.delete(up)
        else:
            if next:
                cmds.delete(cmds.orientConstraint(orientTarget, next))
            else:
                last = node
                
            parent_dict[next] = node


        next = node
        nodes.append(node)
    
    # align the last node to the previous one
    xform_pylib.alignRotation(nodes[-1], nodes[-2])
    
    # parent all the nodes
    for child in parent_dict.keys():
        cmds.parent(child, parent_dict[child])
        if type == "joint":
            cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True, normal=0, preserveNormals=True)

    nodes.reverse()
    return nodes
    
def enableStretchyMotionPath(stretchAttr, curve, motionPaths):
    ''' use the arclen to scale the uValue on a motion path, used by attaching nodes to a curve which auto stretches but cant lock curve length'''

    # need to parameterize 0 to 1 for this to work
    degree = cmds.getAttr(curve + '.degree')
    spans = cmds.getAttr(curve + '.spans')
    
    cmds.rebuildCurve(curve, keepRange=True, spans=spans, degree=degree)
    
    # curve info
    curve_info_name = MayaName(curve)
    curve_info_name.category = "Curveinfo"
    curve_info = cmds.arclen(curve, constructionHistory=True)
    curve_info = cmds.rename(curve_info, curve_info_name)
    length = cmds.getAttr( curve_info + ".arcLength" )
    
    # Length stretch difference
    curve_difference_name = MayaName(curve)
    curve_difference_name.category = "Plusminusaverage"
    curve_difference = cmds.createNode("plusMinusAverage", name=curve_difference_name)
    cmds.setAttr(curve_difference+".operation", 2)
    cmds.connectAttr(curve_info+".arcLength", curve_difference+".input1D[0]")
    cmds.setAttr(curve_difference+".input1D[1]", length)
    
    # flip switch value
    invert_switch_name = MayaName(curve)
    invert_switch_name.descriptor += "InvertSwitch"
    invert_switch_name.category = "Plusminusaverage"
    invert_switch = cmds.createNode("plusMinusAverage", name=invert_switch_name)
    cmds.setAttr(invert_switch+".operation", 2)
    cmds.connectAttr(stretchAttr, invert_switch+".input1D[1]")
    cmds.setAttr(invert_switch+".input1D[0]", 1)

    # stretch switch
    stretch_switch_name = MayaName(curve)
    stretch_switch_name.descriptor += "Switch"
    stretch_switch_name.category = "Multiplydivide"
    stretch_switch = cmds.createNode("multiplyDivide", name=stretch_switch_name)
        
    cmds.connectAttr(curve_difference+".output1D", stretch_switch+".input1X")
    cmds.connectAttr(invert_switch+".output1D", stretch_switch+".input2X")
    
    # add switched difference to original
    curve_sum_name = MayaName(curve)
    curve_sum_name.category = "Plusminusaverage"
    curve_sum = cmds.createNode("plusMinusAverage", name=curve_sum_name)
    cmds.connectAttr(stretch_switch+".outputX", curve_sum+".input1D[0]")
    cmds.setAttr(curve_sum+".input1D[1]", length)

    # stretch ratio
    stretch_ratio_name = MayaName(curve)
    stretch_ratio_name.descriptor += "Ratio"
    stretch_ratio_name.category = "Multiplydivide"
    stretch_ratio = cmds.createNode("multiplyDivide", name=stretch_ratio_name)
    cmds.setAttr(stretch_ratio+".operation", 2)
    
    cmds.setAttr(stretch_ratio+".input1X", length)
    cmds.connectAttr(curve_sum+".output1D", stretch_ratio+".input2X")
    
    for motionPath in motionPaths:
    
        # multiplier
        stretch_multiplier_name = MayaName(curve)
        stretch_multiplier_name.category = "Multiplydivide"
        stretch_multiplier = cmds.createNode("multiplyDivide", name=stretch_multiplier_name)
        
        cmds.setAttr(stretch_multiplier+".input1X", cmds.getAttr(motionPath+".uValue"))
        cmds.connectAttr(stretch_ratio+".outputX", stretch_multiplier+".input2X")
        
        cmds.connectAttr(stretch_multiplier+".outputX", motionPath+".uValue")
    
    return curve_info

def enableSlideJoints(retractionAttr, joints, aimVector):
    ''' To be used to make joints slide along an curve with a retraction attribute. '''

    if not cmds.objExists(retractionAttr):
        attribute_pylib.add(retractionAttr, type="float", max=0, min=None, value=0.0)
    
    aim_axis = "X"
    if aimVector[1]:
        aim_axis = "Y"
    elif aimVector[2]:
        aim_axis = "Z"    

    for ii, joint in enumerate(joints):
        joint_translate_attr = "{}.translate{}".format(joint, aim_axis)
        
        joint_translate = cmds.getAttr(joint_translate_attr)
    
        slide_pm_name = MayaName(joint)
        slide_pm_name.descriptor += "Slide"
        slide_pm_name.category = "Plusminusaverage"
        
        slide_pm = cmds.createNode("plusMinusAverage", name=slide_pm_name)
        cmds.connectAttr(retractionAttr, slide_pm+".input1D[1]")
    
        if joint_translate < 0:
            cmds.setAttr(slide_pm+".operation", 2)
    
        plugs = cmds.listConnections("{}.translate{}".format(joint, aim_axis), source=True, plugs=True)
        
        if plugs:
            for plug in plugs:
                node, attr = plug.split(".")
                
                if cmds.objectType(node) != "ikEffector":
                    cmds.connectAttr(plug, slide_pm+".input1D[0]")
                    break
        else:
            cmds.setAttr(slide_pm+".input1D[0]", joint_translate)
            
        cmds.connectAttr(slide_pm+".output1D", joint_translate_attr, force=True)    
    

def enableStretchyComponentJoints(curve, start_node, end_node, joints, controls, component, aimVector=[1, 0, 0], stretch_attr=False):
    ''' To be used in a component to make a spline chain stretchy using joint translation 
        
    '''

    aim_axis = "X"
    if aimVector[1]:
        aim_axis = "Y"
    elif aimVector[2]:
        aim_axis = "Z"
    
    
    # measure arc length and compare it to the start and end pins
    curve_info = cmds.arclen(curve, constructionHistory=True)
    length = cmds.getAttr( curve_info + ".arcLength" )

    # duplicate the curve to measure the static length.  Edit this as needed to maintain length.
    static_curve_name = MayaName(curve)
    static_curve_name.descriptor += "Static"
    
    static_curve = cmds.duplicate(curve, name=static_curve_name)[0]
    cmds.parent(static_curve, component.rig_dag)
    cmds.setAttr(static_curve+".inheritsTransform", True)
    
    static_curve_info = cmds.arclen(static_curve, constructionHistory=True)
    
    ratio_md_name = MayaName(curve)
    ratio_md_name.descriptor = ratio_md_name.descriptor + "Ratio"
    ratio_md_name.category = "Multiplydivide"

    ratio_md = cmds.createNode("multiplyDivide", n=ratio_md_name)
    cmds.setAttr(ratio_md+".operation", 2)
    
    if stretch_attr:
        stretch_attr = component.component_options + ".stretch"
        attribute_pylib.add(stretch_attr, max=1.0, min=0.0, type="float", value=1.0)

        # get the difference of length between static and stretched
        stretch_diff_pm_name = MayaName(component.name)
        stretch_diff_pm_name.descriptor += "StretchDiff"
        stretch_diff_pm_name.category = "Plusminusaverage"
        
        stretch_diff_pm = cmds.createNode("plusMinusAverage", name=stretch_diff_pm_name)
        cmds.setAttr(stretch_diff_pm+".operation", 2)
        cmds.connectAttr(curve_info + ".arcLength", stretch_diff_pm+".input1D[0]")
        cmds.connectAttr(static_curve_info + ".arcLength", stretch_diff_pm+".input1D[1]")
    
        diff_multiplier_name = MayaName(component.name)
        diff_multiplier_name.descriptor += "Diff"
        diff_multiplier_name.category = "Multiplydivide"
    
        diff_multiplier = cmds.createNode("multiplyDivide", name=diff_multiplier_name)
        cmds.connectAttr(stretch_diff_pm+".output1D", diff_multiplier+".input1X")
        cmds.connectAttr(stretch_attr, diff_multiplier+".input2X")
    
        stretch_add_diff_name = MayaName(component.name)
        stretch_add_diff_name.descriptor += "StretchAdd"
        stretch_add_diff_name.category = "Plusminusaverage"
    
        stretch_add_diff = cmds.createNode("plusMinusAverage", name=stretch_add_diff_name)
        cmds.connectAttr(diff_multiplier+".outputX", stretch_add_diff+".input1D[0]")
        cmds.connectAttr(static_curve_info + ".arcLength", stretch_add_diff+".input1D[1]")
        
        cmds.connectAttr(stretch_add_diff+".output1D", ratio_md+".input1X")
    else:
        cmds.connectAttr(curve_info + ".arcLength", ratio_md+".input1X")
    
    start_pin_dm_name = MayaName(start_node)
    start_pin_dm_name.category = "DecomposeMatrix"
    start_pin_dm = cmds.createNode("decomposeMatrix", name=start_pin_dm_name)
    cmds.connectAttr(start_node+".worldMatrix", start_pin_dm+".inputMatrix")
    
    end_pin_dm_name = MayaName(end_node)
    end_pin_dm_name.category = "DecomposeMatrix"
    end_pin_dm = cmds.createNode("decomposeMatrix", name=end_pin_dm_name)
    cmds.connectAttr(end_node+".worldMatrix", end_pin_dm+".inputMatrix")
    
    static_distance_name = MayaName(start_node)
    static_distance_name.descriptor = static_distance_name.descriptor + "StretchStatic"
    static_distance_name.category = "DistanceDimension"
    static_distance = cmds.createNode("distanceDimShape", n=str(static_distance_name)+"Shape")
    
    cmds.rename(cmds.listRelatives(static_distance, parent=True)[0], static_distance_name)
    cmds.parent(cmds.listRelatives(static_distance, parent=True)[0], component.worldspace_dag)
    
    cmds.connectAttr(static_curve_info + ".arcLength", ratio_md+".input2X") 
    
    for ii, joint in enumerate(joints):
        if ii == 0:
            continue
            
        stretch_md_name = MayaName(joint)
        stretch_md_name.descriptor = stretch_md_name.descriptor + "Stretch"
        stretch_md_name.category = "MultiplyDivide"
        
        stretch_md = cmds.createNode("multiplyDivide", name=stretch_md_name)
        
        joint_translate = "{}.translate{}".format(joint, aim_axis.capitalize())
        
        cmds.connectAttr(ratio_md+".outputX", stretch_md+".input1X")
        cmds.setAttr(stretch_md+".input2X", cmds.getAttr(joint_translate))
        
        cmds.connectAttr(stretch_md+".outputX", joint_translate)
        

def createSplineDriver(name, curve, extrude_curve, joints, skinclusterSmoothIterations=10):
    ''' extrude the curve to make a driver to be used as a utility mesh '''
    
    # Extrude curve for driver
    cmds.nurbsToPolygonsPref( pt=1, un=1, vn=1)
    (driver, extrude) = cmds.extrude(extrude_curve, curve, ch=True, rn=False, po=1, et=2, ucp=0, fpt=1, upn=1, rotation=0, scale=1, rsp=1)
    driver = cmds.rename(driver, name)
    
    cmds.delete(driver, constructionHistory = True)
    
    cmds.select(joints)
    skincluster = cmds.skinCluster(driver, joints, toSelectedBones=True, ignoreHierarchy=True)[0]
    
    skincluster_pylib.smoothFlood(driver, iterations=skinclusterSmoothIterations)
    
    cmds.delete(extrude_curve)
    
    return driver