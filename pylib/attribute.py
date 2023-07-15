 
import maya.cmds as cmds

# attributes
def lockAndHide(obj, attrs):
    for attr in attrs:
        if (attr == "r"):
            cmds.setAttr( obj+".rotateX", keyable=False, lock=True )
            cmds.setAttr( obj+".rotateY", keyable=False, lock=True )
            cmds.setAttr( obj+".rotateZ", keyable=False, lock=True )
        elif (attr == "t"):
            cmds.setAttr( obj+".translateX", keyable=False, lock=True )
            cmds.setAttr( obj+".translateY", keyable=False, lock=True )
            cmds.setAttr( obj+".translateZ", keyable=False, lock=True )
        elif (attr == "s"):
            cmds.setAttr( obj+".scaleX", keyable=False, lock=True )
            cmds.setAttr( obj+".scaleY", keyable=False, lock=True )
            cmds.setAttr( obj+".scaleZ", keyable=False, lock=True )
        else:
            cmds.setAttr( obj+"."+attr, keyable=False, lock=True )

def unlockAndShow(obj, attrs):
    for attr in attrs:
        if (attr == "r"):
            cmds.setAttr( obj+".rotateX", keyable=True, lock=False )
            cmds.setAttr( obj+".rotateY", keyable=True, lock=False )
            cmds.setAttr( obj+".rotateZ", keyable=True, lock=False )
        elif (attr == "t"):
            cmds.setAttr( obj+".translateX", keyable=True, lock=False )
            cmds.setAttr( obj+".translateY", keyable=True, lock=False )
            cmds.setAttr( obj+".translateZ", keyable=True, lock=False )
        elif (attr == "s"):
            cmds.setAttr( obj+".scaleX", keyable=True, lock=False )
            cmds.setAttr( obj+".scaleY", keyable=True, lock=False )
            cmds.setAttr( obj+".scaleZ", keyable=True, lock=False )
        else:
            cmds.setAttr( obj+"."+attr, keyable=True, lock=False )            

# attributes
def lock(obj, attrs):
    for attr in attrs:
        if (attr=="r"):
            cmds.setAttr(obj+".rotateX", lock=True )
            cmds.setAttr(obj+".rotateY", lock=True )
            cmds.setAttr(obj+".rotateZ", lock=True )
        elif (attr=="t"):
            cmds.setAttr(obj+".translateX", lock=True )
            cmds.setAttr(obj+".translateY", lock=True )
            cmds.setAttr(obj+".translateZ", lock=True )
        elif (attr=="s"):
            cmds.setAttr(obj+".scaleX", lock=True )
            cmds.setAttr(obj+".scaleY", lock=True )
            cmds.setAttr(obj+".scaleZ", lock=True )
        else:
            cmds.setAttr(obj+"."+attr, lock=True )

def unlock(obj, attrs):
    for attr in attrs:
        if (attr=="r"):
            cmds.setAttr(obj+".rotateX", lock=False )
            cmds.setAttr(obj+".rotateY", lock=False )
            cmds.setAttr(obj+".rotateZ", lock=False )
        elif (attr=="t"):
            cmds.setAttr(obj+".translateX", lock=False )
            cmds.setAttr(obj+".translateY", lock=False )
            cmds.setAttr(obj+".translateZ", lock=False )
        elif (attr=="s"):
            cmds.setAttr(obj+".scaleX", lock=False )
            cmds.setAttr(obj+".scaleY", lock=False )
            cmds.setAttr(obj+".scaleZ", lock=False )
        else:
            cmds.setAttr(obj+"."+attr, lock=False )

def connectInverse(source, target):
    ''' muliply source by -1 '''
    
    md_name = MayaName(source)
    md_name.descriptor = md_name.descriptor+"Inverse"
    md_name.category = "Multiplydivide"
    
    multiply_divide = cmds.createNode( "multiplyDivide", n=md_name )
    
    cmds.setAttr( multiply_divide+".input2X", -1 )
    cmds.connectAttr( source, multiply_divide+".input1X" )
    cmds.connectAttr( multiply_divide+".outputX", target )
    
    return multiply_divide
    
def add(attr, type="long", max=1, min=0, value=0, keyable=True, niceName="", node="", lock=False, dv=None, en="" ):
    ''' node.attr instead of separating node and attr name and it returns that value '''
    
    attr = attr.split(".")
    if len(attr) > 1:
        node = attr[0]
        attr = attr[1]
    else:
        if cmds.objExists(node) != True:
            print ("Error attribute.add(): Invalid 'node' specified.\n")
            return False
        attr = attr[0]

    if dv == None:
        dv = value
        
    if max == None:
        max = 9223372036854775800.0
    if min == None:
        min = -9223372036854775800.0
        
    if type == "message":
        cmds.addAttr(node, ln=attr, at=type)
    elif type == "string":
        cmds.addAttr(node, dt="string", ln=attr, nn=niceName)
        cmds.setAttr(node+"."+attr, value, type="string")
    elif type == "enum":
        cmds.addAttr(node, at="enum", ln=attr, en=en, keyable=True, nn=niceName)
    else:
        cmds.addAttr(node, nn=niceName, ln=attr, k=keyable, min=min, max=max, at=type, dv=dv )
    
    new_attr = "{}.{}".format(node, attr)  
    
    try:
        cmds.setAttr(new_attr, value)
    except RuntimeError:
        pass
        
    cmds.setAttr(new_attr, lock=lock)
    return new_attr
    
    
def getAttrLocks(node):
    ''' Given an object, check to see if the t and r attrs are locked '''
    locks = []
    
    # Translate Keyables
    locks.append( cmds.getAttr(node+".translate", keyable=True) )
    locks.append( cmds.getAttr(node+".translateX", keyable=True) )
    locks.append( cmds.getAttr(node+".translateY", keyable=True) )
    locks.append( cmds.getAttr(node+".translateZ", keyable=True) )
    
    # Translate Locks
    locks.append( cmds.getAttr(node+".translate", lock=True) )
    locks.append( cmds.getAttr(node+".translateX",lock=True) )
    locks.append( cmds.getAttr(node+".translateY",lock=True) )
    locks.append( cmds.getAttr(node+".translateZ",lock=True) )
    
    # Translate Channel Box visibility
    locks.append( cmds.getAttr(node+".translate", channelBox=True) )
    locks.append( cmds.getAttr(node+".translateX", channelBox=True) )
    locks.append( cmds.getAttr(node+".translateY", channelBox=True) )
    locks.append( cmds.getAttr(node+".translateZ", channelBox=True) )

    # Rotation Keyables
    locks.append( cmds.getAttr(node+".translate", keyable=True) )
    locks.append( cmds.getAttr(node+".translateX", keyable=True) )
    locks.append( cmds.getAttr(node+".translateY", keyable=True) )
    locks.append( cmds.getAttr(node+".translateZ", keyable=True) )
    
    # Rotation Locks
    locks.append( cmds.getAttr(node+".rotate", lock=True) )
    locks.append( cmds.getAttr(node+".rotateX", lock=True) )
    locks.append( cmds.getAttr(node+".rotateY", lock=True) )
    locks.append( cmds.getAttr(node+".rotateZ", lock=True) )
    

    
    # Rotation Channel Box visibility
    locks.append( cmds.getAttr(node+".rotate", channelBox=True) )
    locks.append( cmds.getAttr(node+".rotateX", channelBox=True) )
    locks.append( cmds.getAttr(node+".rotateY", channelBox=True) )
    locks.append( cmds.getAttr(node+".rotateZ", channelBox=True) )
        
    return locks
    
def setAttrLocks(node, locks):
    ''' Given an object and its lock Array set the attr locks '''

    # Translate Keyables
    cmds.setAttr( node+".translate",  keyable=locks[0] )
    cmds.setAttr( node+".translateX", keyable=locks[1] )
    cmds.setAttr( node+".translateY", keyable=locks[2] )
    cmds.setAttr( node+".translateZ", keyable=locks[3] )
    
    # Translate Locks
    cmds.setAttr( node+".translate",  lock=locks[4] )
    cmds.setAttr( node+".translateX", lock=locks[5] )
    cmds.setAttr( node+".translateY", lock=locks[6] )
    cmds.setAttr( node+".translateZ", lock=locks[7] )
    
    
    # Translate Channel Box visibility
    # the if statement is to get rid of the annoying warning that comes up
    if locks[0] == False: cmds.setAttr(node+".translate",  channelBox=locks[8])
    if locks[1] == False: cmds.setAttr(node+".translateX", channelBox=locks[9])
    if locks[2] == False: cmds.setAttr(node+".translateY", channelBox=locks[10])
    if locks[3] == False: cmds.setAttr(node+".translateZ", channelBox=locks[11])

    # Rotation Keyables
    cmds.setAttr(node+".rotate",  keyable=locks[12])
    cmds.setAttr(node+".rotateX", keyable=locks[13])
    cmds.setAttr(node+".rotateY", keyable=locks[14])
    cmds.setAttr(node+".rotateZ", keyable=locks[15])

    # Rotation Locks
    cmds.setAttr(node+".rotate",  lock=locks[16])
    cmds.setAttr(node+".rotateX", lock=locks[17])
    cmds.setAttr(node+".rotateY", lock=locks[18])
    cmds.setAttr(node+".rotateZ", lock=locks[19])
    
    
    # Rotation Channel Box visibility
    if locks[12] == False: cmds.setAttr(node+".rotate",  channelBox=locks[20])
    if locks[13] == False: cmds.setAttr(node+".rotateX", channelBox=locks[21])
    if locks[14] == False: cmds.setAttr(node+".rotateY", channelBox=locks[22])
    if locks[15] == False: cmds.setAttr(node+".rotateZ", channelBox=locks[23])
    
    return True
    
def connectAttr(source_attr, target_attr):

    # if the target attr is locked unlock, connect, relock
    if cmds.getAttr(target_attr, l=True):
        node = target_attr.split(".")[0]
        attr = target_attr.split(".")[1]
        if attr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:
            lary = getAttrLocks(node)
            unlockAndShow(node, ["t","r","s"])
            cmds.connectAttr(source_attr, target_attr)
            setAttrLocks(node, lary)
        else:
            cmds.setAttr(target_attr, l=False)
            cmds.connectAttr(source_attr, target_attr)
            cmds.setAttr(target_attr, l=True)
    else: 
        cmds.connectAttr(source_attr, target_attr)
    
def disconnectAttr(source_attr, target_attr):

    # if the target attr is locked unlock, connect, relock
    if cmds.getAttr(target_attr, l=True):
        obj = target_attr.split(".")[0]
        attr = target_attr.split(".")[1]
        if attr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:
            lary = getAttrLocks(obj)
            unlockAndShow(obj, ["t","r","s"])
            cmds.disconnectAttr(source_attr, target_attr)
            setAttrLocks(obj, lary)
        else:
            cmds.setAttr(target_attr, l=False)
            cmds.disconnectAttr(source_attr, target_attr)
            cmds.setAttr(target_attr, l=True)
    else: 
        cmds.disconnectAttr(source_attr, target_attr)

def breakConnection(attr):
    ''' break the connection given the attribute '''
    
    inplug = cmds.listConnections(attr, source=True, plugs=True, destination=False)
    
    if inplug:
        cmds.disconnectAttr(inplug[0], attr)
        return True
        
    else:
        return False
        

        
def visibilityAttr(attr, nodes, enum_string, add_none=True, add_all=True):
    ''' create an enum list that controls it's visiblity of the nodes. 
    
        nodes can be a list of a list of objects
    '''
    
    node_list = list(nodes)
    
    if add_none:
        enum_string = "none:" + enum_string
        node_list.insert(0, "")
        none_add_count = 1
    
    if add_all:
        enum_string += ":all"

    add(attr, type="enum", en=enum_string)

    # Set driven key
    nodes_count = len(node_list)
    for ii, node in enumerate(node_list):
        if node == "":
            continue
        
        for jj in range(nodes_count):
            if ii == jj:
                if isinstance(node, list):
                    for nn in node:
                        cmds.setDrivenKeyframe(nn+".visibility", currentDriver=attr, value=1, driverValue=jj)
                else:
                    cmds.setDrivenKeyframe(node+".visibility", currentDriver=attr, value=1, driverValue=jj)
            else:
                if isinstance(node, list):
                    for nn in node:
                        cmds.setDrivenKeyframe(nn+".visibility", currentDriver=attr, value=0, driverValue=jj)
                else:
                    cmds.setDrivenKeyframe(node+".visibility", currentDriver=attr, value=0, driverValue=jj)
            
    if add_all:
        for ii, node in enumerate(node_list):
            if node == "":
                continue
                
            if isinstance(node, list):
                for nn in node:
                    cmds.setDrivenKeyframe(nn+".visibility", currentDriver=attr, value=1, driverValue=nodes_count+1)
            else:
                cmds.setDrivenKeyframe(node+".visibility", currentDriver=attr, value=1, driverValue=nodes_count+1)  