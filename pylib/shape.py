 

import maya.cmds as cmds
import maya.api.OpenMaya as om

from rigpie.pylib.mayaname import MayaName

import rigpie.pylib.shape as shape_pylib
import rigpie.pylib.rmath as rmath_pylib
import rigpie.pylib.xform as xform_pylib


# CONSTANTS
LFCOLOR = "dark blue"
RTCOLOR = "red"
CNCOLOR = "yellow"

def getRgbBySide(name, alternate=True):
    ''' Given a control name, return an HSV value '''
    if name[0:2] == "Lf":
        if alternate:
            return [0.0, 0.1, 1.0]
        else:
            return [0.0, 0.0, .3]
    elif name[0:2] == "Rt":
        if alternate:
            return [0.4, 0.0, 0.0]
        else:
            return [1.0, 0.0, 0.0]
    else:
        if alternate:
            return [1.0, 0.75, 0.0]
        else:
            return [1.0, 1.0, 0.0]

def getColorBySide(name):
    ''' Given a control name, return a color '''
    if name[0:2] == "Lf":
        return LFCOLOR
    elif name[0:2] == "Rt":
        return RTCOLOR
    else:
        return CNCOLOR
        
def getMayaColor(color):
    '''Convert the a color into the maya display color value, if a int is given a string is returned and vice versa'''
    colors = ["grey","black","dark grey","light grey","burgundy","navy blue","blue",
              "dark green","dark purple","magenta","dark orange","dark brown",
              "dark red","red","green","dark blue","white","yellow","light blue",
              "aquamarine", "pink", "peach", "light yellow", "sea green", "light brown",
              "barf","lime green","light green","turquoise","royal blue","dark violet",
              "dark magenta"]
    
    if isinstance(color, int):
        return colors[color]
    else:
        try:
            return(colors.index(color))
        except ValueError:
            print ("shape_pylib.getColor(): %s not found in color dictionary\n" % color)
            return False


def create(shapeType="cube", type="transform", size=1.0, name="custom", color="yellow", rot=[0,0,0], thickness=-1):
    ''' create shape for controls
        shapeType: cube, rectangle, square, diamond2d, circle, sphere, turtle
    '''
    
    if isinstance(size, float) or isinstance(size, int):
        x = float( size )
        y = float( size )
        z = float( size )
        nx = float( size * -1.0)
        ny = float( size * -1.0)
        nz = float( size * -1.0)
    else:
        x = float( size[0] )
        y = float( size[1] )
        z = float( size[2] )
        nx = float( size[0] * -1.0)
        ny = float( size[1] * -1.0)
        nz = float( size[2] * -1.0)
    
    # create transform
    if type=="joint":
        newnode = cmds.joint( n=name )
        cmds.setAttr(newnode+".drawStyle", 2)
    else:
        newnode = cmds.createNode("transform", n=name)

    # create shape
    if shapeType == "cube":
        pointary = ( [x,y,z],[nx,y,z],[nx,ny,z],[nx,ny,nz],[nx,y,nz],[x,y,nz],[x,y,z],[x,ny,z],
                     [x,ny,nz],[x,y,nz],[nx,y,nz],[nx,y,z],[nx,ny,z],[x,ny,z],[x,ny,nz],[nx,ny,nz] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )
    
    elif shapeType == "triangle":
        pointary = ( [0,0,nz/2.0],[nx/2.0,0,z/2.0],[x/2.0,0,z/2.0],[0,0,nz/2.0])
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )
        
    elif shapeType == "turtle":
        pointary = ( [.75*x,0,0],[0,1.5*y,0],[.75*nx,0,0],[.75*x,0,0],[0,0,z],[.75*nx,0,0],[0,1.5*y,0],[0,0,z] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )

    elif shapeType == "pyramid":
        pointary = ( [x,0,z],[nx,0,z],[nx,0,nz],[x,0,nz],[x,0,z],[0,1*y,0],[nx,0,z],[nx,0,nz],[0,1*y,0],[x,0,nz])
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )

    elif shapeType == "square":
        pointary = ( [x,0,z],[nx,0,z],[nx,0,nz],[x,0,nz], [x,0,z])
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )
        
    elif shapeType == "diamond2d":
        pointary = ( [(x/2),0,(2*nz/3)],[(nx/2),0,(2*nz/3)],[nx,0,nz/3],[0,0,z],[x,0,nz/3],[(x/2),0,(2*nz/3)] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )
    
    elif shapeType == "circle":
        pointary = ( [(x/4),0,(nz)],[3*x/4,0,3*nz/4],[x,0,nz/4],[x,0,z/4],[3*x/4,0,3*z/4],
                     [(x/4),0,z],[(nx/4),0,z],[3*nx/4,0,3*z/4],[nx,0,z/4],[nx,0,nz/4],[3*nx/4,0,3*nz/4],
                     [(nx/4),0,(nz)],[(x/4),0,(nz)] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )

    elif shapeType == "shell":
        pointary = ( [(x/4),.4*y,(nz)],[3*x/4,.1*y,3*nz/4],[x,0,nz/4],[x,0,z/4],[3*x/4,.1*y,3*z/4],
                     [(x/4),.4*y,z],[(nx/4),.4*y,z],[3*nx/4,.1*y,3*z/4],[nx,0,z/4],[nx,0,nz/4],[3*nx/4,.1*y,3*nz/4],
                     [(nx/4),.4*y,(nz)],[(x/4),.4*y,(nz)] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )
        
    elif shapeType == "cross":
        pointary = ( [(.25*x),0,.75*z], [(.25*x),0,(.25*z)], [.75*x,0,.25*z], [.75*x,0,-.25*z], [.25*x,0,-.25*z], [(.25*x),0,(-.75*z)], [(.25*x),0,-.75*z], [(-.25*x),0,-.75*z], 
                     [(-.25*x),0,(-.25*z)], [-.75*x,0,(-.25*z)], [-.75*x,0,(.25*z)], [(-.25*x),0,(.25*z)], [-.25*x,0,(.75*z)], [(.25*x),0,.75*z] )
        pointary = rotatePointArray(pointary, rot)
        tmpnode  = cmds.curve( n="TmpShape", degree=1, p=pointary )

    elif shapeType == "sphere":
        # Make circles
        pointary = ([x,0,0],[0,0,z],[nx,0,0],[0,0,nz],[x,0,0],[0,0,z],[nx,0,0])
        tmpnode  = cmds.curve( per=True, p=pointary, k=[-2,-1,0,1,2,3,4,5,6] )
        pointary = ([0,y,0],[nx,0,0],[0,ny,0],[x,0,0],[0,y,0],[nx,0,0], [0,ny,0])
        tmpnode  = cmds.curve( tmpnode, append=True, per=True, p=pointary, k=[-2,-1,0,1,2,3,4,5,6] )
        pointary = ([0,y,0],[0,0,nz],[0,ny,0],[0,0,z],[0,y,0],[0,0,nz], [0,ny,0])
        tmpnode  = cmds.curve( tmpnode, append=True, per=True, p=pointary, k=[-4,-3,-2,-1,0,1,2,3,4,5,6,7,8,9,10,11] )
        
    else:
        print ("shape.createShape(): shapeType %s not found!\n" % shapeType)
        return False
    
    tmpshape = cmds.listRelatives( tmpnode, s=True )[0]

    if isinstance(name, MayaName):
        name = str(name)

    # copy shape to new transforms
    shape = str(name) + "Shape"

    cmds.rename( tmpshape, shape )        
    cmds.parent( shape, newnode, r=True, s=True )
        
    # rename and set the color
    cmds.setAttr( shape+".overrideEnabled", 1 )
    
    if isinstance(color, str):
        cmds.setAttr( shape+".overrideRGBColors", 0)
        cmds.setAttr( shape+".overrideColor", getMayaColor(color) )
    elif isinstance(color, int):
        cmds.setAttr( shape+".overrideRGBColors", )
        cmds.setAttr( shape+".overrideColor", color)
    else:
        cmds.setAttr( shape+".overrideRGBColors", 1)
        cmds.setAttr( shape+".overrideColorR", color[0])
        cmds.setAttr( shape+".overrideColorG", color[1])
        cmds.setAttr( shape+".overrideColorB", color[2])    

    # line thickness
    cmds.setAttr( newnode+".lineWidth", thickness )

    # reset xform
    cmds.setAttr( newnode+".r",0,0,0,type="float3" )

    # cleanup temp nodes
    cmds.delete(tmpnode)

    return newnode


def rotatePointArray(parray, rot):
    newpointary = []
    
    # If no rotation, don't compute.
    if rot == [0,0,0]:
        return parray

    # create temp transform to rotate points
    tmpxform = cmds.createNode("transform", n="TmpXform")
    
    # rotate based the shape based on rot
    cmds.setAttr( tmpxform+".rx", rot[0] )
    cmds.setAttr( tmpxform+".ry", rot[1] )
    cmds.setAttr( tmpxform+".rz", rot[2] )

    for pp in parray:
        pXform = rmath_pylib.Transform()
        tXform = rmath_pylib.Transform(tmpxform)
        
        pXform.translate(pp)
        newpointary.append( ((pXform * tXform).getTranslation()).get() )
    
    cmds.delete(tmpxform)
    return tuple(newpointary)

def changeControlShape(ctrl, shapeType="cube", color="yellow"):
    original_shape = cmds.listRelatives(ctrl, shapes=True)[0]
    
    cmds.delete(original_shape)
    
    new_shape = create(shapeType=shapeType, color=color)
    new_shape = cmds.rename(new_shape, original_shape)
    
    cmds.parent(new_shape, ctrl, shape=True, relative=True)


def copyShape(source, target):
    target_shape = None
    try:
        # delete old shape if exists
        target_shapes = cmds.listRelatives(target, shapes=True)[0]
        target_shape = target_shapes
        cmds.delete(target_shapes)
    except TypeError:
        pass

    source_shape = cmds.listRelatives(source, shapes=True)[0]
    thickness = cmds.getAttr(source_shape+".lineWidth")

    source_duplicate = cmds.duplicate(source, name=source+"_DELETEME")[0]
    
    source_shape = None
    duplicate_children = cmds.listRelatives(source_duplicate, children=True, fullPath=True)
    for child in duplicate_children:
        if cmds.objectType(child) != "nurbsCurve":
            cmds.delete(child)
        else:
            if not source_shape:
                source_shape = child

    cmds.rename(source_shape, target_shape)

    # thickness
    cmds.setAttr(target_shape+".lineWidth", thickness)
    
    cmds.parent(target_shape, target, relative=True, shape=True)
    cmds.delete(source_duplicate)
    

def moveShapesToBottom(shapes):
    ''' given a list of shapes under the same transform, re-organize them to the bottom.
    
        first shapes transform is used, any shape that is not a child of the first shape transform will be ignored.
    '''
    
    temp_transform = cmds.createNode("transform", name="IMG_TEMP_XFORM_DELETEME")
    
    current_transform = cmds.listRelatives(shapes[0], parent=True)[0]
    
    xform_pylib.align(temp_transform, current_transform)
        
    for shape in shapes:
        if cmds.listRelatives(shape, parent=True)[0] != current_transform:
            continue
            
        cmds.parent(shape, temp_transform, shape=True, absolute=False, relative=True)

    for shape in shapes:
        cmds.parent(shape, current_transform, shape=True, absolute=False, relative=True)

    cmds.delete(temp_transform)
    
    
