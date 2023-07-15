 
from os.path import exists

from rigpie.pylib.mayaname import MayaName
from rigpie.pylib.rmath import Transform

import maya.cmds as cmds
import rigpie.pylib.controlshape as controlshape_pylib
import rigpie.pylib.attribute as attribute_pylib
import rigpie.pylib.xform as xform_pylib

class Control(object):
    ''' Control object '''
    
    def __init__(self, *args, **kwargs):

        object.__init__(self)
        if args:
            self.createFromString(args[0])
            return
        
        self.name = kwargs.get('name', 'CnDefaultCtrl') 
        self.size = kwargs.get('size', 1) 
        self.inputJoint = kwargs.get('inputJoint', '')
        self.shapeType = kwargs.get('shapeType', 'cube')
        self.matrix = kwargs.get('matrix', '')
        self.depth = kwargs.get('depth', 1)
        self.parent = kwargs.get('parent', '')
        self.lockAndHide = kwargs.get('lockAndHide', ['v'])
        self.type = kwargs.get('type', 'transform')
        self.connectScale = kwargs.get('connectScale', True)
        self.color = kwargs.get('color', 'yellow')
        self.shapeRotation = kwargs.get('shapeRotation', [0,0,0])
        self.rotationOrder = kwargs.get('rotationOrder', '')
        self.thickness = kwargs.get('thickness', -1)
        
        self.zero = None
        self.shape = None
        self.offset_transforms = []
        
        self.create()
    
    def createFromString(self, node, size=1):
        if cmds.objExists(node):
            self.name = node
            
            offset_transforms = []
            parent = node
            parents = cmds.listRelatives(parent, parent=True)
            
            all_parents = cmds.ls(node, long=True)[0].split('|')[1:-1]
            all_parents.reverse()
            
            for count in range(len(all_parents)):
                parent = all_parents[count]
                
                name = MayaName(parent)
                
                if name.category == "Zero":
                    self.zero = parent
                    break
                else:
                    offset_transforms.append(parent)
                
            self.offset_transforms = offset_transforms
            
            # get all the shape information
            for shape in cmds.listRelatives(node, shapes=True):
                if isControlShape(shape):
                    # shape instance
                    self.shape = shape
                    
                    # color
                    if cmds.getAttr( shape+".overrideRGBColors"):
                        r = cmds.getAttr(shape+".overrideColorR")
                        g = cmds.getAttr(shape+".overrideColorG")
                        b = cmds.getAttr(shape+".overrideColorB")
                        
                        self.color = [r, g, b]
                    else:
                        self.color = cmds.getAttr( shape+".overrideColor")
                        
                    # thickness
                    self.thickness = cmds.getAttr(shape+".lineWidth")
                    
                    # only do the first one found
                    break

            self.shapeRotation = [0,0,0]
            self.rotationOrder = node
            self.type = cmds.objectType(node)
            self.size = size
            self.matrix = node
            self.parent = cmds.listRelatives(node, parent=True)
            self.inputJoint = None
            
            lockAndHide = []
            if cmds.getAttr(node+".translate", lock=True):
                lockAndHide.append('t')
            if cmds.getAttr(node+".rotate", lock=True):
                lockAndHide.append('r')
            if cmds.getAttr(node+".scale", lock=True):
                lockAndHide.append('s')
            if cmds.getAttr(node+".visibility", lock=True):
                lockAndHide.append('v')
                
            self.lockAndHide = lockAndHide
            
            # just set the default shape type
            self.shapeType = None
    
    def create(self, description=""):
        tail = ""
        control = ""

        # convert to string if you're getting a mayaname object
        if isinstance(self.name, MayaName):
            self.name = str(self.name)
        
        rotateOrder = 0
        # Setup rotation order
        if self.rotationOrder == "":
            if cmds.objExists(self.inputJoint):
                rotateOrder = cmds.getAttr(self.inputJoint+".rotateOrder")
        else:
            rotOrders = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
            if cmds.objExists(self.rotationOrder):
                rotateOrder = cmds.getAttr(self.rotationOrder+".rotateOrder")
            else:
                rotateOrder = rotOrders.index(self.rotationOrder)

        # Create control
        shape_name = MayaName(self.name)
        shape_name.descriptor += description
        
        cmds.select(cl=True)
        if self.shapeType == None:
            control = cmds.createNode("transform", n=shape_name)
        else:
            control = controlshape_pylib.create(shapeType=self.shapeType, type=self.type, size=self.size, name=shape_name, color=self.color, rot=self.shapeRotation, thickness=self.thickness)

        # Create Nulls and Zero grps
        zero = ""
        head = control
        
        transform_name = MayaName(self.name)
        transform_name.descriptor += description

        
        for ii in range(0, self.depth):
            if ii == 0:
                transform_name.category = "Zero"
                tail = cmds.createNode("transform", n=str(transform_name))
                zero = tail
                head = tail
            elif ii == 1:
                transform_name.category = "Auto"
                new_transform = cmds.createNode("transform", n=str(transform_name))
                cmds.parent(new_transform, tail)
                self.offset_transforms.append(new_transform)
                tail = new_transform
            else:
                transform_name.category = "Auto"
                transform_name.instance = ii
                new_transform = cmds.createNode("transform", n=str(transform_name))
                self.offset_transforms.append(new_transform)
                cmds.parent(new_transform, tail)
                tail = new_transform
                
            cmds.parent(control, tail)

        # Matrix can be either a maya node or a list of 16 floats
        if isinstance(self.matrix, Transform):
            cmds.xform(head, m=list(self.matrix), worldSpace=True)
        elif cmds.objExists(self.matrix):
            xform_pylib.align(head, self.matrix)

        # Set parent
        if self.parent != "":
            cmds.parent(head, self.parent)
        
        # Constrain node to control, usually a joint
        if self.inputJoint:
            cmds.parentConstraint(control, self.inputJoint)
            
            if self.connectScale:
                cmds.scaleConstraint(control, self.inputJoint)

        # Lock and Hide attrs
        attribute_pylib.lockAndHide(control, self.lockAndHide)
        
        # Lock and hide radius attr if joint
        try: cmds.setAttr(control+".radius", channelBox=False)
        except: pass

        # maya control for parallel eval
        cmds.controller(control)
        
        # rotation order
        cmds.setAttr(control+".rotateOrder", rotateOrder)
            
        self.zero = zero
        self.shape = cmds.listRelatives(control, s=1)[0]
        
        # tag the shape as a control shape for import/export
        tagAsControlShape(self.shape)
        
        # make rotation order available in the channel box
        cmds.setAttr(control+".rotateOrder", keyable=False, channelBox=True)
        
        return head
        
    def addTransformOffset(self):
        ''' add a transform as a parent to the control '''
        
        last_transform_name = MayaName(self.name)
        last_transform_name.category = "Auto"
        transform_parent = self.zero

        # if a offset transform already exists
        if len(self.offset_transforms) >= 1:
            last_transform_name = MayaName(self.offset_transforms[0])
            
            if last_transform_name.instance:
                instance = int(last_transform_name.instance) + 1
                last_transform_name.instance = str(instance)
            else:
                last_transform_name.instance = "1"
            transform_parent = self.offset_transforms[0]
        
        transform_offset = cmds.createNode("transform", name=last_transform_name, parent=transform_parent)
        self.offset_transforms = [transform_offset] + self.offset_transforms
        xform_pylib.align(transform_offset, self.name)
        
        attr_locks = attribute_pylib.getAttrLocks(self.name)
        cmds.parent(self.name, transform_offset)
        
        return transform_offset

        
    def goToBindPose(self):
        goToBindPose(self.name)
   
    def goToZeroPose(self):
        goToZeroPose(self.name)

def goToZeroPose(control):
    ''' zero out '''
    
    if not cmds.getAttr(control+".translate", lock=True):
        if not cmds.getAttr(control+".translateX", lock=True):
            cmds.setAttr(control+".translateX", 0.0)
        if not cmds.getAttr(control+".translateY", lock=True):
            cmds.setAttr(control+".translateY", 0.0)
        if not cmds.getAttr(control+".translateZ", lock=True):
            cmds.setAttr(control+".translateZ", 0.0)

    if not cmds.getAttr(control+".rotate", lock=True):
        if not cmds.getAttr(control+".rotateX", lock=True):
            cmds.setAttr(control+".rotateX", 0.0)
        if not cmds.getAttr(control+".rotateY", lock=True):
            cmds.setAttr(control+".rotateY", 0.0)
        if not cmds.getAttr(control+".rotateZ", lock=True):
            cmds.setAttr(control+".rotateZ", 0.0)


def goToBindPose(control):
    ''' Rotate and move control to bind pose'''
    position = None
    rotation = None
    
    if cmds.objExists(control+".bindPosX"):
        position = [cmds.getAttr(control+".bindPosX"), cmds.getAttr(control+".bindPosY"), cmds.getAttr(control+".bindPosZ")]
    if cmds.objExists(control+".bindRotX"):
        rotation = [cmds.getAttr(control+".bindRotX"), cmds.getAttr(control+".bindRotY"), cmds.getAttr(control+".bindRotZ")]
    
    if position:
        if not cmds.getAttr(control+".translateX", lock=True):
            cmds.setAttr(control+".translateX", position[0])
        if not cmds.getAttr(control+".translateY", lock=True):
            cmds.setAttr(control+".translateY", position[1])
        if not cmds.getAttr(control+".translateZ", lock=True):
            cmds.setAttr(control+".translateZ", position[2])
        
    if rotation:
        if not cmds.getAttr(control+".rotateX", lock=True):
            cmds.setAttr(control+".rotateX", rotation[0])
        if not cmds.getAttr(control+".rotateY", lock=True):
            cmds.setAttr(control+".rotateY", rotation[1])
        if not cmds.getAttr(control+".rotateZ", lock=True):
            cmds.setAttr(control+".rotateZ", rotation[2])



	
def exportShapes(nodes, filename):

    shape_root = cmds.createNode("transform", n="importShapes")
    
    for node in nodes:
        
        control = Control(node)
    
        new_node = duplicate(control, category="Ctrlnurbs")
        attribute_pylib.unlockAndShow(new_node.name, ['t', 'r', 's', 'v'])
        cmds.parent(new_node.name, shape_root)
        
    cmds.select(shape_root)

    export_shapes = cmds.listRelatives(shape_root, allDescendents=True)
    export_shapes.append(shape_root)
    
    for shape in export_shapes: 
        cmds.setAttr( shape+".visibility", lock=False )
        try:
            cmds.setAttr( shape+".visibility", True )
        except RuntimeError: 
            attribute_pylib.breakConnection( shape+".visibility" )
            cmds.setAttr( shape+".visibility", True )

    if ".ma" in filename:
        cmds.file(filename, exportSelected=True, force=True, typ="mayaAscii")
    else:
        cmds.file(filename, exportSelected=True, force=True, typ="mayaBinary")

    cmds.delete(shape_root)
    
    

def importShapes(filename, relative=True):
    
    if not exists(filename):
        cmds.warning("{} does not exist.".format(filename))
        return False
        
    
    cmds.file( filename, i=True, loadReferenceDepth="none")
    main = cmds.ls( "importShapes" )
    
    shapes = cmds.listRelatives( main, c=True )
    for ss in shapes:
        if isComponentOptions(ss):
            continue
            
        current_control = ss.replace( "nurbs", "" )
        # Delete the old shape
        if cmds.objExists( current_control ):
            oldshapes = cmds.listRelatives( current_control, s=True )
            
            for os in oldshapes:
                if not (isComponentOptions(os)):
                    cmds.delete(os)
                
            spans = cmds.getAttr(ss+".spans")
            degrees = cmds.getAttr(ss+".degree")

            cvCount = spans + degrees
            
            if relative:
                xform_pylib.align(ss, current_control)
            
            pa = []
            for ii in range(cvCount):
                pa.append(cmds.xform("{}.cv[{}]".format(ss, ii), q=1, ws=1, t=1))
            
            nshape = current_control+"nurbsShape"
            cmds.parent( nshape, current_control, s=True, r=1)
            
            if not relative:
                for ii, position in enumerate(pa):
                    cmds.xform("{}.cv[{}]".format(nshape, ii), ws=1, t=position)
                    
            cmds.rename(nshape, nshape.replace( "CtrlnurbsShape", "CtrlShape") )
            
    cmds.delete( main )

# valid colors: "blue", "red", "yellow"
def setColor(control, color="blue"):
    colorval = 6
    if color == "red":
        colorval = 13
    elif color == "yellow":
        colorval = 17
    if control.find("Shape") == -1:
        control = control+"Shape"
    
    cmds.setAttr(control+".overrideEnabled", 1)
    cmds.setAttr(control+".overrideColor", colorval)

def setRGBColor(shape, color = (1,1,1)):
    rgb = ("R","G","B")
    
    cmds.setAttr(shape + ".overrideEnabled",1)
    cmds.setAttr(shape + ".overrideRGBColors",1)
    


def mirrorShapes(controls, shapefile=True, searchreplace=["Lf","Rt"], useExistingColor=True):
    for ctrl in controls:
        # If we are in the shape file, then 
        # we are using mirror joints to get the transform of the other sides control.
        rgb = None
        color = None
        
        original_exists = False
        
        ctrl_name = MayaName(ctrl)
        
        if ctrl_name.side == "Lf":
            searchreplace=["Lf","Rt"]
        else:
            searchreplace=["Rt","Lf"]
            mirror_color = 15
        
        target_control = ctrl.replace(searchreplace[0], searchreplace[1])
        
        # If the rig is open
        if ctrl_name.category != "Exp":
            cmds.delete(target_control+"Shape")

        else: # If the control_shapes is open
            if cmds.objExists(target_control):
            
                original_exists = True
                
                shape = cmds.listRelatives(target_control, shapes=True)[0]
                rgb = [cmds.getAttr(shape+".overrideColorR"), cmds.getAttr(shape+".overrideColorG"), cmds.getAttr(shape+".overrideColorB")]
                color = cmds.getAttr(shape+".overrideColor")
                
                cmds.delete(target_control)
            
            temp_controls = []
            cmds.select(cl=True)
            temp_controls.append(cmds.joint())
            cmds.select(cl=True)
            temp_controls.append(cmds.joint())
            cmds.parent(temp_controls[1], temp_controls[0])
            
            xform_pylib.align(temp_controls[1], ctrl)
            
            # mirror the joint
            temp_controls = temp_controls + (cmds.mirrorJoint(temp_controls[0], mirrorYZ=True, mirrorBehavior=True))
            new_joint = cmds.listRelatives(temp_controls[2], ad=True)[0]
            
            # create the new transform
            cmds.createNode("transform", n=target_control)                
            xform_pylib.align(target_control, new_joint)

            # Delete all of the temp joints
            cmds.delete(temp_controls)            
            
        new_transform = cmds.createNode("transform", n=target_control+"xform")
        cmds.setAttr(new_transform+".rotateOrder", cmds.getAttr(ctrl+".rotateOrder"))
        
        position = cmds.xform(ctrl, query=True, worldSpace=True, translation=True)
        rotation = cmds.xform(ctrl, query=True, worldSpace=True, rotation=True)
        cmds.setAttr(new_transform+".translate", position[0], position[1], position[2])
        cmds.setAttr(new_transform+".rotate", rotation[0], rotation[1], rotation[2])
        
        dup_control = cmds.duplicate(ctrl)[0]
        dup_shape = dup_control+"Shape"
        cmds.parent(dup_shape, new_transform, relative=True, shape=True)
        new_shape = cmds.rename(dup_shape, target_control+"TmpShape")
        cmds.delete(dup_control)
        
        zero = cmds.createNode("transform", name="ZEROMIRROR")
        cmds.parent(new_transform, zero)
        cmds.setAttr(zero+".scaleX", -1)
        
        temp = cmds.parent(new_shape, target_control, shape=True)[0]
        temp_parent = cmds.listRelatives(temp, parent=True)[0]
        cmds.makeIdentity(temp_parent, apply=True)
        
        cmds.parent(new_shape, target_control, relative=True, shape=True)
        cmds.delete(temp_parent)
        
        cmds.rename(new_shape, target_control+"Shape")
        

        if useExistingColor and original_exists:
            cmds.setAttr(target_control+"Shape.overrideColorR", rgb[0])
            cmds.setAttr(target_control+"Shape.overrideColorG", rgb[1])
            cmds.setAttr(target_control+"Shape.overrideColorB", rgb[2])
            
            cmds.setAttr(target_control+"Shape.overrideColor", color)
        else:
            color = controlshape_pylib.getColorBySide(target_control)
            
            cmds.setAttr(target_control+"Shape.overrideColor", controlshape_pylib.getMayaColor(color))
        
        # thickness
        cmds.setAttr(target_control+"Shape.lineWidth", cmds.getAttr(ctrl+"Shape.lineWidth"))

        cmds.delete(zero)

def tagAsControlShape(shape):
    if not(cmds.objExists(shape+".controlShapeTag")):
        cmds.addAttr(shape, longName="controlShapeTag", keyable=False, attributeType="message")
        return True
        
    return False

def isControlShape(shape):
    return cmds.objExists(shape+".controlShapeTag")

def tagAsComponentOptions(shape):
    if not(cmds.objExists(shape+".componentOptionsTag")):
        cmds.addAttr(shape, longName="componentOptionsTag", keyable=False, attributeType="message")
        return True
    return False

def isComponentOptions(shape):
    return cmds.objExists(shape+".componentOptionsTag")
        

def constrain_halfway_controls(controls):
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
        
    
    even, odd = split_list(transforms, [], [])
    
    if len(odd) == 3:
        cmds.parentConstraint(odd[0], odd[1])
        cmds.parentConstraint(odd[2], odd[1])

        cmds.parentConstraint(odd[0], even[0])
        cmds.parentConstraint(odd[1], even[0])
        
        cmds.parentConstraint(odd[1], even[1])
        cmds.parentConstraint(odd[2], even[1])
    else:
        half_index = int((len(transforms) + 1) / 2)
        
        # Constrain the middle and ends
        cmds.parentConstraint(transforms[0], transforms[half_index-1])
        cmds.parentConstraint(transforms[-1], transforms[half_index-1])

        leftovers = [transforms[:half_index], transforms[half_index-1:]]
    
        if len(leftovers[0]) == 2:
            return True
    
        constrain_halfway_transforms(leftovers[0])
        constrain_halfway_transforms(leftovers[1])

def duplicate(control, side=None, description=None, iterator=None, category=None):
    ''' duplicate the control only '''
    
    new_control_name = MayaName(control.name)
    
    if not side and not description and not iterator and not category:
        print ("control.duplicate(): Atleast one maya name member required.")
        return False
    
    if side:
        new_control_name.side = side
    
    if description:
        new_control_name.descriptor = description
        
    if iterator:
        new_control_name.iterator = iterator
        
    if category:
        new_control_name.category = category
    
    duplicate_control = cmds.duplicate( control.name, name=str(new_control_name) )[0]
    new_control = Control(duplicate_control)
    
    for child in cmds.listRelatives(new_control.name, fullPath=True):
        shape_name = child.split("|")[-1]
        if shape_name != new_control.shape:
            cmds.delete(child)
    
    return new_control