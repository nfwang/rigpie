 
import maya.cmds as cmds

from rigpie.pylib.component import Component
from rigpie.pylib.control import Control
from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Transform, Vector

import rigpie.pylib.curve as curve_pylib
import rigpie.pylib.skincluster as skincluster_pylib
import rigpie.pylib.shape as shape_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.mayatransform as mayatransform_pylib
import rigpie.pylib.shape as shape_pylib


class Slider(Component):
    ''' Given a curve place a joint as a motion path in the center of the curve and drive it along the path based on other attributes. '''
    
    def __init__(self,  **kwargs):
        
        # Required arguments
        kwargs['name'] = kwargs.get('name', 'CnSplineCurve1')
        
        super().__init__(**kwargs)

        self.curve = kwargs.get('curve', 'CnSliderCurve')
        self.curveSkinweights = kwargs.get('curveSkinweights', None)
        self.jointParent = kwargs.get('jointParent', '')
        self.curveParent = kwargs.get('curveParent', '')
        
        self.createControl = kwargs.get('createControl', False)
        
        self.negativeMaxValue = kwargs.get('negativeMaxValue', -180)
        self.negativeScaleValue = kwargs.get('negativeScaleValue', .5)
        self.positiveMaxValue = kwargs.get('positiveMaxValue', 180)
        self.positiveScaleValue = kwargs.get('positiveScaleValue', .5)

        self.rotationOrder = kwargs.get('rotationOrder', 'xyz')
        self.driverAttr = kwargs.get('driverAttr', 'CnRootJnt.rotateX')

        self.size = kwargs.get('size', 10)
        
        # Protected members
        self.controls = []
        self.driver_plug = None
        
    def mirror(self):
        original_side = "Lf"
        mirrored_side = "Rt"
        
        if self.name[0:2] == "Rt":
            original_side = "Lf"
            original  = "Rt"
        
        newself = Slider(name=self.name.replace(original, mirrored_side))
        
        newself.curve = self.curve.replace(original, mirrored_side)

        if self.curveSkinweights:
            mirror_skinweight_tuples = []
            for tuple_list in self.curveSkinweights:
                newlist = []
                for tuple in tuple_list:
                    newlist.append((tuple[0].replace(original, mirrored_side), tuple[1]))
                    
                mirror_skinweight_tuples.append(newlist)
                
            newself.curveSkinweights = mirror_skinweight_tuples
        
        newself.jointParent = self.jointParent.replace(original, mirrored_side)
        newself.curveParent = self.curveParent.replace(original, mirrored_side)
        
        newself.createControl = self.createControl
        
        newself.positiveMaxValue = self.positiveMaxValue
        newself.positiveScaleValue = self.positiveScaleValue
        newself.negativeMaxValue = self.negativeMaxValue 
        newself.negativeScaleValue = self.negativeScaleValue
        
        newself.rotationOrder = self.rotationOrder
        newself.driverAttr = self.driverAttr.replace(original, mirrored_side)
        
        newself.mirrored = 1
        
        return newself
        
        
    def prebuild(self):
        super().prebuild()
        
    def build(self):
        
        # rebuild curve to be parameterized 0 to 1
        cmds.rebuildCurve( self.curve, 
                           constructionHistory=True, 
                           replaceOriginal=True, 
                           rebuildType=0, 
                           endKnots=1, 
                           keepRange=0, 
                           keepControlPoints=True, 
                           keepEndPoints=True, 
                           keepTangents=False
        )
        
        cmds.parent(self.curve, self.worldspace_dag)
        cmds.connectAttr(self.rig_attr, self.curve+".visibility")
        
        positiveNegative_condition_name = MayaName(self.name)
        positiveNegative_condition_name.category = "Condition"
        positiveNegative_condition = cmds.createNode("condition", name=positiveNegative_condition_name)
        cmds.setAttr(positiveNegative_condition+".operation", 2)

        driver_node, driver_attr = self.driverAttr.split(".")
        
        # Create an intermediate attr if the attr doesnt exist
        if not cmds.objExists(self.driverAttr):
            self.driver_plug = "{}.{}_plug".format(self.name, driver_attr)
            attribute_pylib.add(self.driver_plug, type="float", keyable=False)
            cmds.connectAttr(self.driver_plug, positiveNegative_condition+".firstTerm")
        else:
            cmds.connectAttr(self.driverAttr, positiveNegative_condition+".firstTerm")
        
        # check to see if there's a unitConversion and if there is, use that output.
        driver_attr_out = cmds.listConnections(positiveNegative_condition+".firstTerm", source=True, plugs=True)[0]
        
        # Negative values
        scaleNegative_md_name = MayaName(driver_node)
        
        # Normalize the scaled value
        normalizeNegative_md_name = MayaName(self.name)
        normalizeNegative_md_name.descriptor = normalizeNegative_md_name.descriptor + "NormalizeNeg"
        normalizeNegative_md_name.category = "Multiplydivide"
        normalizeNegative_md = cmds.createNode("multiplyDivide", name=normalizeNegative_md_name)
        
        cmds.setAttr(normalizeNegative_md+".operation", 2)
        cmds.setAttr(normalizeNegative_md+".input2X", self.negativeMaxValue)
        cmds.connectAttr(driver_attr_out, normalizeNegative_md+".input1X")
        
        # Remap value to be 0 to .5
        normalizeNegative_md_name.category = "Remapvalue"
        negative_remap = cmds.createNode("remapValue", name=normalizeNegative_md_name)
        cmds.setAttr(negative_remap+".outputMin", .5)
        cmds.connectAttr(normalizeNegative_md+".outputX", negative_remap+".inputValue")

        # scale value if it's not 1
        negative_value_plug = negative_remap+".outValue"
        
        if self.negativeScaleValue != 1:
            scaleNegative_md_name = MayaName(self.name)
            scaleNegative_md_name.descriptor = scaleNegative_md_name.descriptor + "ScaleNeg"
            scaleNegative_md_name.category = "Multiplydivide"
            
            scaleNegative_md = cmds.createNode("multiplyDivide", name=scaleNegative_md_name)
            cmds.connectAttr(negative_remap+".outValue", scaleNegative_md+".input1X")
            cmds.setAttr(scaleNegative_md+".input2X", self.negativeScaleValue)
            
            negative_value_plug = scaleNegative_md + ".outputX"
        
        cmds.connectAttr(negative_value_plug, positiveNegative_condition+".colorIfFalseR")
        
        # Positive values
        scalePositive_md_name = MayaName(driver_node)
        
        # Normalize the scaled value
        normalizePositive_md_name = MayaName(self.name)
        normalizePositive_md_name.descriptor = normalizePositive_md_name.descriptor + "NormalizePos"
        normalizePositive_md = cmds.createNode("multiplyDivide", name=normalizePositive_md_name)
        cmds.setAttr(normalizePositive_md+".operation", 2)
        cmds.setAttr(normalizePositive_md+".input2X", self.positiveMaxValue)
        cmds.connectAttr(driver_attr_out, normalizePositive_md+".input1X")
        
        # Remap value to be 0 to .5
        normalizePositive_md_name.category = "Remapvalue"
        positive_remap = cmds.createNode("remapValue", name=normalizePositive_md_name)
        cmds.setAttr(positive_remap+".outputMin", .5)
        cmds.setAttr(positive_remap+".outputMax", 0)
        cmds.connectAttr(normalizePositive_md+".outputX", positive_remap+".inputValue")

        
        # scale the value if it's not one
        positive_value_plug = positive_remap+".outValue"
        
        if self.positiveScaleValue != 1:
            scalePositive_md_name = MayaName(self.name)        
            scalePositive_md_name.descriptor = scalePositive_md_name.descriptor + "ScalePos"
            scalePositive_md_name.category = "Mulitplydivide"
            
            scalePositive_md = cmds.createNode("multiplyDivide", name=scalePositive_md_name)
            cmds.connectAttr(positive_remap+".outValue", scalePositive_md+".input1X")
            cmds.setAttr(scalePositive_md+".input2X", self.positiveScaleValue)
            
            positive_value_plug = scalePositive_md+".outputX"
        
        cmds.connectAttr(positive_value_plug, positiveNegative_condition+".colorIfTrueR")
        
        # transform that drives the control
        slider_transform_name = MayaName(self.name)
        slider_transform_name.category = "Null"
        
        self.slider_transform = mayatransform_pylib.createLocator(name=slider_transform_name, parent=self.worldspace_dag)
        cmds.connectAttr(self.rig_attr, self.slider_transform+".visibility")

        # slider joint
        slider_joint_name = MayaName(self.name)
        slider_joint_name.category = "Jnt"
        self.slider_joint = cmds.createNode("joint", name=slider_joint_name)
        
        cmds.setAttr(self.slider_joint+".radius", self.size/30.0)

        # place transform in the right spot because of a weird update bug
        curve_info = cmds.createNode("pointOnCurveInfo")
        cmds.connectAttr(self.curve+".worldSpace[0]", curve_info+".inputCurve")
        cmds.setAttr(curve_info+".parameter", cmds.getAttr(positiveNegative_condition+".outColorR"))
        
        param_position = cmds.getAttr(curve_info + ".position")[0]
        
        cmds.setAttr(self.slider_transform+".translate", 
                     param_position[0],
                     param_position[1],
                     param_position[2],
                     type="float3"
        )
        
        cmds.delete(curve_info)
        
        # Motion Path
        motion_path, param, flipped_transforms = curve_pylib.attachNodeToCurve( self.curve,
                                                                                self.slider_transform, 
                                                                                translationOnly=True
        )
        
        slider_transform_name.category = "Motionpath"
        motion_path = cmds.rename(motion_path, str(slider_transform_name))

        cmds.connectAttr(positiveNegative_condition+".outColorR", motion_path+".uValue")
        
        # Create Control
        if self.createControl:
            slider_transform_name.category = "Ctrl"

            self.control = Control( name=slider_transform_name,
                                    color=shape_pylib.getColorBySide(str(slider_transform_name)), 
                                    size=2,
                                    shapeType="cube",
                                    depth=2,
                                    lockAndHide=["v"], 
                                    rotationOrder=self.slider_transform,
                                    matrix=self.slider_transform, 
                                    parent=self.controls_dag
            )
            self.registerControl(self.control)
            
            cmds.parentConstraint(self.control.name, self.slider_joint)        
            cmds.scaleConstraint(self.control.name, self.slider_joint)
            
            cmds.parentConstraint(self.slider_transform, self.control.zero)
            
            # constrain the orientation to the jointParent
            if self.jointParent:
                cmds.orientConstraint(self.jointParent, self.control.offset_transforms[0])
            
        else:
            cmds.pointConstraint(self.slider_transform, self.slider_joint)

            # constrain the orientation to the jointParent
            if self.jointParent:
                cmds.orientConstraint(self.jointParent, self.slider_joint)
        

        if self.curveSkinweights:
            # collect list of influences
            influences = []
            for list in self.curveSkinweights:
                for cl_list in list:
                    influence = cl_list[0]
                    if influence not in influences:
                        influences.append(influence)
            
            skincluster = cmds.skinCluster(self.curve, influences)[0]
            for cv in range(len(self.curveSkinweights)):
                weight_tuples = self.curveSkinweights[cv]
                cmds.skinPercent (skincluster, "{}.cv[{}]".format(self.curve, cv), transformValue=weight_tuples)
                
            skincluster_pylib.removeUnusedInfluences(skincluster)
        elif self.curveParent:
            cmds.parentConstraint(self.curveParent, self.curve, maintainOffset=True)
            cmds.scaleConstraint(self.curveParent, self.curve)

        # put this in the end to avoid maya cycles because of the cmds.skincluster function
        cmds.parent(self.slider_joint, self.jointParent)
        
        
    def postbuild(self):
        super().postbuild()
        
        if self.driver_plug:
            cmds.connectAttr(self.driverAttr, self.driver_plug)
            
        # export joint dictionary
        self.export_joints[self.slider_joint] = None
        self.export_joints_start = [self.slider_joint]
        self.export_joints_end = [self.slider_joint]