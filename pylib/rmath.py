 

import maya.cmds as cmds
import math
import maya.OpenMaya as om


class Vector(object):
    ''' float3 vector.  given a maya object will start with position.'''
    
    def __init__(self,*args):
        object.__init__(self)
        if args:
            self.set(*args)
        else:
            self.zero()
            
    def __str__(self):
        return '[%.3f,%.3f,%.3f]'%(self.x,self.y,self.z)
        
    def __len__(self):
        return 3
        
    def __iter__(self):
        return iter([self.x,self.y,self.z])
        
    def __add__(self,vector):
        newV = Vector()
        newV.fromList([self.x + vector.x,self.y + vector.y,self.z + vector.z])
        return newV
    
    def __sub__(self,vector):
        newV = Vector()
        newV.fromList([self.x - vector.x, self.y - vector.y, self.z - vector.z])
        return newV
        
    def __mul__(self,vector):
        newV = Vector()
        if isinstance(vector,Vector):
            newV.fromVector(self.x * vector.x, self.y * vector.y, self.z * vector.z)
        elif isinstance(vector,Transform):
            xform_a_1,xform_a_2,xform_a_3 = self.get()
            xform_b_11,xform_b_12,xform_b_13,xform_b_14,xform_b_21,xform_b_22,xform_b_23,xform_b_24,xform_b_31,xform_b_32,xform_b_33,xform_b_34,xform_b_41,xform_b_42,xform_b_43,xform_b_44 = vector.get()
            newV.fromList(
                [
                xform_b_11*xform_a_1 + xform_b_21*xform_a_2 + xform_b_31*xform_a_3 + xform_b_41,
                xform_b_21*xform_a_1 + xform_b_22*xform_a_2 + xform_b_22*xform_a_3 + xform_b_42,
                xform_b_31*xform_a_2 + xform_b_32*xform_a_2 + xform_b_33*xform_a_3 + xform_b_43
                ]
            )
        else:
            newV.fromList([self.x*vector,self.y*vector,self.z*vector])
        return newV
        
    def __truediv__(self, vector):
        newV = Vector()
        
        if isinstance(vector,Vector):
            newV.fromList([self.x / vector.x, self.y / vector.y, self.z / vector.z])
        else:
            newV.fromList([self.x / vector, self.y / vector, self.z / vector])
        
        return newV

    def __lt__(self,vector):
        return self.sqLength() < vector        
        
    def __gt__(self,vector):
        return self.sqLength() > vector
        

    def fromVector(self, v):
        self.x = v.x
        self.y = v.y
        self.z = v.z

    def fromList(self, v):
        self.x = float(v[0])
        self.y = float(v[1])
        self.z = float(v[2])

    def zero(self):
        self.x=0
        self.y=0
        self.z=0
    
    def set(self,*args):
        '''
            float: set all values to this.
            float3: xyz
            maya object: world space position
        '''

        if len(args) == 1:
            if isinstance(args[0], list):
                self.fromList(args[0])
            elif hasattr(args[0], 'x') and hasattr(args[0],'y') and hasattr(args[0],'z'):
                self.fromVector(args[0])
            elif cmds.objExists(args[0]):
                self.fromMayaObj(args[0])
            elif hasattr(args[0], '_matrix'):
                self.setFromVector(args[0].getTranslation())
            else:
                raise RuntimeError("rmath.set(): invalid arguments {}".format(args))
        elif len(args) == 3:
            self.fromList(args)
            
    def copy(self):
        return Vector(self.x,self.y,self.z)
        
    def fromMayaObj(self,obj):
        '''set vector to a maya node world space position'''
        self.x,self.y,self.z = cmds.xform(obj,ws=True,q=True,t=True)
    
    def get(self):
        return [self.x,self.y,self.z]

        
    def normalize(self):
        length = self.length()
        self.x /= length
        self.y /= length
        self.z /= length
        
    def length(self):
        return math.sqrt(self.sqLength())
        
    def sqLength(self):
        return self.dot(self)
        
    def dot(self, vector):
        return self.x * vector.x + self.y * vector.y + self.z * vector.z
        
    def cross(self,vector):
        return Vector(
            self.y * vector.z - self.z * vector.y , 
            self.z * vector.x - self.x * vector.z , 
            self.x * vector.y - self.y * vector.x
            )
    def invert(self):
        self.x *= -1
        self.y *= -1
        self.z *= -1
        
    def reflect(self, plane=None):
        '''default plane: (-1,0,0)'''
        vector = self.copy()
        if not plane:
            plane = Vector(-1,0,0)
        else:
            plane = Vector(plane)
        dot = vector.dot(plane)

        self.fromVector(vector - plane * 2 * dot)

    def getMayaEnumInt(self, include_closest=False):
        ''' Get maya's enumerator index '''
        
        if not include_closest:
            if self.x == 1:
                return 0
            if self.x == -1:
                return 1

            if self.y == 1:
                return 2
            if self.y == -1:
                return 3

            if self.z == 1:
                return 4
            if self.z == -1:
                return 5
        else:
            if self.x == 1:
                return 6
            if self.x == -1:
                return 7

            if self.y == 1:
                return 0
            if self.y == -1:
                return 1

            if self.z == 1:
                return 3
            if self.z == -1:
                return 4
        
class Transform(object):
    '''4x4 object transform class'''
    def __init__(self,*args):
        object.__init__(self)
        self.identity()
        if args:
            self.set(*args)
            
    def __str__(self):
        return "%s %s %s %s\n%s %s %s %s\n%s %s %s %s\n%s %s %s %s" % (
            self._matrix[0], self._matrix[1], self._matrix[2], self._matrix[3],
            self._matrix[4], self._matrix[5], self._matrix[6], self._matrix[7],
            self._matrix[8], self._matrix[9], self._matrix[10], self._matrix[11],
            self._matrix[12], self._matrix[13], self._matrix[14], self._matrix[15]
        )  
    
    def __iter__(self):
        return iter([
            self._matrix[0], self._matrix[1], self._matrix[2], self._matrix[3],
            self._matrix[4], self._matrix[5], self._matrix[6], self._matrix[7],
            self._matrix[8], self._matrix[9], self._matrix[10], self._matrix[11],
            self._matrix[12], self._matrix[13], self._matrix[14], self._matrix[15]
        ])
        
    def __len__(self):
        return 16

    def __add__(self,transform):
        try:
            if len(transform) == 3: #matrix and vector
                self.translate(transform)
            elif len(transform) == 16: #matrix and matrix
                return Transform(map((lambda x,y: x+y),self.get(),transform.get()))
        except TypeError:
            return Transform(map((lambda x,y: x+y),self.get(),[float(transform)]*16))
        
        
    def __sub__(self,transform):
        try:
            if len(transform) == 3: #matrix and vector
                self.translate(transform * -1)
            elif len(transform) == 16: #matrix and matrix
                return Transform(map((lambda x,y: x-y),self.get(),transform.get()))
        except TypeError: # matrix and float
            return Transform(map((lambda x,y: x-y),self.get(),[float(transform)]*16))     
            
    def __mul__(self,transform):
        if isinstance(transform,Transform):
            xform_a_11, xform_a_12, xform_a_13, xform_a_14, xform_a_21, xform_a_22, xform_a_23, xform_a_24, xform_a_31, xform_a_32, xform_a_33, xform_a_34, xform_a_41, xform_a_42, xform_a_43, xform_a_44 = self.get()
            xform_b_11, xform_b_12, xform_b_13, xform_b_14, xform_b_21, xform_b_22, xform_b_23, xform_b_24, xform_b_31, xform_b_32, xform_b_33, xform_b_34, xform_b_41, xform_b_42, xform_b_43, xform_b_44 = transform.get()
            
            return Transform(
                xform_a_11*xform_b_11 + xform_a_12*xform_b_21 + xform_a_13*xform_b_31 + xform_a_14*xform_b_41, xform_a_11*xform_b_12 + xform_a_12*xform_b_22 + xform_a_13*xform_b_32 + xform_a_14*xform_b_42, xform_a_11*xform_b_13 + xform_a_12*xform_b_23 + xform_a_13*xform_b_33 + xform_a_14*xform_b_43, xform_a_11*xform_b_14 + xform_a_12*xform_b_24 + xform_a_13*xform_b_34 + xform_a_14*xform_b_44,
                xform_a_21*xform_b_11 + xform_a_22*xform_b_21 + xform_a_23*xform_b_31 + xform_a_24*xform_b_41, xform_a_21*xform_b_12 + xform_a_22*xform_b_22 + xform_a_23*xform_b_32 + xform_a_24*xform_b_42, xform_a_21*xform_b_13 + xform_a_22*xform_b_23 + xform_a_23*xform_b_33 + xform_a_24*xform_b_43, xform_a_21*xform_b_14 + xform_a_22*xform_b_24 + xform_a_23*xform_b_34 + xform_a_24*xform_b_44,
                xform_a_31*xform_b_11 + xform_a_32*xform_b_21 + xform_a_33*xform_b_31 + xform_a_34*xform_b_41, xform_a_31*xform_b_12 + xform_a_32*xform_b_22 + xform_a_33*xform_b_32 + xform_a_34*xform_b_42, xform_a_31*xform_b_13 + xform_a_32*xform_b_23 + xform_a_33*xform_b_33 + xform_a_34*xform_b_43, xform_a_31*xform_b_14 + xform_a_32*xform_b_24 + xform_a_33*xform_b_34 + xform_a_34*xform_b_44,
                xform_a_41*xform_b_11 + xform_a_42*xform_b_21 + xform_a_43*xform_b_31 + xform_a_44*xform_b_41, xform_a_41*xform_b_12 + xform_a_42*xform_b_22 + xform_a_43*xform_b_32 + xform_a_44*xform_b_42, xform_a_41*xform_b_13 + xform_a_42*xform_b_23 + xform_a_43*xform_b_33 + xform_a_44*xform_b_43, xform_a_41*xform_b_14 + xform_a_42*xform_b_24 + xform_a_43*xform_b_34 + xform_a_44*xform_b_44
            )
        elif isinstance(transform,Vector):
            xform_a_11,xform_a_12,xform_a_13,xform_a_14,xform_a_21,xform_a_22,xform_a_23,xform_a_24,xform_a_31,xform_a_32,xform_a_33,xform_a_34,xform_a_41,xform_a_42,xform_a_43,xform_a_44 = self.get()
            xform_b_1,xform_b_2,xform_b_3 = transform.get()
            return Transform(
                xform_a_11 * xform_b_1, xform_a_12 * xform_b_2, xform_a_13 * xform_b_3, xform_a_14,
                xform_a_21 * xform_b_1, xform_a_22 * xform_b_2, xform_a_23 * xform_b_3, xform_a_24,
                xform_a_31 * xform_b_1, xform_a_32 * xform_b_2, xform_a_33 * xform_b_3, xform_a_34,
                xform_a_41, xform_a_42, xform_a_43, xform_a_44
                )
        else:
            raise TypeError("rmath.Transform.__mul__(): {} and {} are unsupported.".format(self.__class__.__name__ ,transform.__class__.__name__))

    def copy(self):
        return Transform(self.get())
        
    def zero(self):
        self._matrix = [0]*16
        
    def identity(self):
        self._matrix = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        
    def get(self):
        return self._matrix[:]
        
    def set(self,*args):
        '''given a list, transform or position vector, set the matrix.
        
           else return identity
        '''
    
        if args:
            if len(args) == 1:
                if cmds.objExists(args[0]):
                    self.fromMayaObj(args[0])
                elif hasattr(args[0], 'x') and hasattr(args[0],'y') and hasattr(args[0],'z'):
                    self.setTranslation(args[0])
                elif isinstance(args[0],Transform):
                    self.fromList(args[0].get())
                elif hasattr(args[0],'__iter__'):
                    self.fromList(args[0])
                else:
                    raise RuntimeError("rmath.Transform.set(): invalid arguments '{}' ".format(args[0]))
            elif len(args) == 16:
                self.fromList(args)
            else:
                raise RuntimeError("rmath.Transform.set(): invalid arguments '{}' ".format(args[0]))
        else:
            self.identity()

    def fromMayaObj(self,obj):
        self._matrix = cmds.xform(obj,ws=True,m=True,q=True)
        return
        
    def fromList(self,transform):
        if not len(transform) == 16:
            raise TypeError("matrix must be set from 16 element list")
        self._matrix = list(transform[:])
        
    def getTranslation(self):
        '''get translation as a Vector'''
        return Vector(self._matrix[12],self._matrix[13],self._matrix[14])
        
    def setTranslation(self,transform):
        '''set translation from antransform object'''
        transform = Vector(transform)
        
        self._matrix[12] = transform.x
        self._matrix[13] = transform.y
        self._matrix[14] = transform.z
        
    def getRotation(self):
        '''list of the euler rotations. '''
        mMatrix = om.MMatrix() # MMatrix
        om.MScriptUtil.createMatrixFromList(list(self), mMatrix)
        mTransformMtx = om.MTransformationMatrix(mMatrix)
        eulerRot = mTransformMtx.eulerRotation() # MEulerRotation

        # Convert from radians to degrees:
        angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]        
        return angles

    def xAxis(self):
        return Vector(self._matrix[0],self._matrix[1],self._matrix[2])
    
    def yAxis(self):
        return Vector(self._matrix[4],self._matrix[5],self._matrix[6])

    def zAxis(self):
        return Vector(self._matrix[8],self._matrix[9],self._matrix[10])
        
    def getScale(self):
        return (self._matrix[0], self._matrix[5], self._matrix[10])
        
    def translate(self,transform):
        ''' move Transform the translation of antransform object, Vector or Transform'''
        
        if not isinstance(transform,Vector):
            transform = Vector(transform)

        self._matrix[12] += transform.x
        self._matrix[13] += transform.y
        self._matrix[14] += transform.z
        
 
    def reflect(self,plane=None):
        '''reflect the transform about a plane specified as a Vector. 
            Default:  yz plane
        '''
        
        x_axis = self.x_axisxis()
        x_axis.reflect(plane=plane)
        y_axis = self.y_axisxis()
        y_axis.reflect(plane=plane)
        z_axis = self.z_axisxis()
        z_axis.reflect(plane=plane)
        translation = self.getTranslation()
        translation.reflect(plane=plane)
        self.set(x_axis.x,x_axis.y,x_axis.z,0,y_axis.x,y_axis.y,y_axis.z,0,z_axis.x,z_axis.y,z_axis.z,0,translation.x,translation.y,translation.z,1)
        
        
    def det(self):
        '''return the determinate of the matrix'''
        xform11,xform12,xform13,xform14,xform21,xform22,xform23,xform24,xform31,xform32,xform33,xform34,xform41,xform42,xform43,xform44 = self.get()
        return (
            xform11*xform22*xform33*xform44 + xform11*xform23*xform34*xform42 + xform11*xform24*xform32*xform43 +
            xform12*xform21*xform34*xform43 + xform12*xform23*xform31*xform44 + xform12*xform24*xform33*xform41 +
            xform13*xform21*xform32*xform44 + xform13*xform22*xform34*xform41 + xform13*xform24*xform31*xform42 +
            xform14*xform21*xform33*xform42 + xform14*xform22*xform31*xform43 + xform14*xform23*xform32*xform41 -
            xform11*xform22*xform34*xform43 - xform11*xform23*xform32*xform44 - xform11*xform24*xform33*xform42 -
            xform12*xform21*xform33*xform44 - xform12*xform23*xform34*xform41 - xform12*xform24*xform31*xform43 -
            xform13*xform21*xform34*xform42 - xform13*xform22*xform31*xform44 - xform13*xform24*xform32*xform41 -
            xform14*xform21*xform32*xform43 - xform14*xform22*xform33*xform41 - xform14*xform23*xform31*xform42
            )
            
    def transpose(self):
        xform11,xform12,xform13,xform14,xform21,xform22,xform23,xform24,xform31,xform32,xform33,xform34,xform41,xform42,xform43,xform44 = self.get()
        self.set(
            xform11,xform21,xform31,xform41,
            xform12,xform22,xform32,xform42,
            xform13,xform23,xform33,xform43,
            xform14,xform24,xform34,xform44
            )

    def invert(self):
        '''invert the current matrix in place.'''
        inverted = [0]*16
        xform = self._matrix[:]
        inverted[0] = xform[5]*xform[10]*xform[15] - xform[5]*xform[11]*xform[14] - xform[9]*xform[6]*xform[15] + \
                 xform[9]*xform[7]*xform[14] + xform[13]*xform[6]*xform[11] - xform[13]*xform[7]*xform[10]
        inverted[4] = -xform[4]*xform[10]*xform[15] + xform[4]*xform[11]*xform[14] + xform[8]*xform[6]*xform[15] - \
                  xform[8]*xform[7]*xform[14] - xform[12]*xform[6]*xform[11] + xform[12]*xform[7]*xform[10]
        inverted[8] = xform[4]*xform[9]*xform[15] - xform[4]*xform[11]*xform[13] - xform[8]*xform[5]*xform[15] + \
                 xform[8]*xform[7]*xform[13] + xform[12]*xform[5]*xform[11] - xform[12]*xform[7]*xform[9]
        inverted[12] = -xform[4]*xform[9]*xform[14] + xform[4]*xform[10]*xform[13] + xform[8]*xform[5]*xform[14] - \
                   xform[8]*xform[6]*xform[13] - xform[12]*xform[5]*xform[10] + xform[12]*xform[6]*xform[9]
        inverted[1] = -xform[1]*xform[10]*xform[15] + xform[1]*xform[11]*xform[14] + xform[9]*xform[2]*xform[15] - \
                  xform[9]*xform[3]*xform[14] - xform[13]*xform[2]*xform[11] + xform[13]*xform[3]*xform[10]
        inverted[5] = xform[0]*xform[10]*xform[15] - xform[0]*xform[11]*xform[14] - xform[8]*xform[2]*xform[15] + \
                 xform[8]*xform[3]*xform[14] + xform[12]*xform[2]*xform[11] - xform[12]*xform[3]*xform[10]
        inverted[9] = -xform[0]*xform[9]*xform[15] + xform[0]*xform[11]*xform[13] + xform[8]*xform[1]*xform[15] - \
                  xform[8]*xform[3]*xform[13] - xform[12]*xform[1]*xform[11] + xform[12]*xform[3]*xform[9]
        inverted[13] = xform[0]*xform[9]*xform[14] - xform[0]*xform[10]*xform[13] - xform[8]*xform[1]*xform[14] + \
                  xform[8]*xform[2]*xform[13] + xform[12]*xform[1]*xform[10] - xform[12]*xform[2]*xform[9]
        inverted[2] = xform[1]*xform[6]*xform[15] - xform[1]*xform[7]*xform[14] - xform[5]*xform[2]*xform[15] + \
                 xform[5]*xform[3]*xform[14] + xform[13]*xform[2]*xform[7] - xform[13]*xform[3]*xform[6]
        inverted[6] = -xform[0]*xform[6]*xform[15] + xform[0]*xform[7]*xform[14] + xform[4]*xform[2]*xform[15] - \
                  xform[4]*xform[3]*xform[14] - xform[12]*xform[2]*xform[7] + xform[12]*xform[3]*xform[6]
        inverted[10] = xform[0]*xform[5]*xform[15] - xform[0]*xform[7]*xform[13] - xform[4]*xform[1]*xform[15] + \
                  xform[4]*xform[3]*xform[13] + xform[12]*xform[1]*xform[7] - xform[12]*xform[3]*xform[5]
        inverted[14] = -xform[0]*xform[5]*xform[14] + xform[0]*xform[6]*xform[13] + xform[4]*xform[1]*xform[14] - \
                   xform[4]*xform[2]*xform[13] - xform[12]*xform[1]*xform[6] + xform[12]*xform[2]*xform[5]
        inverted[3] = -xform[1]*xform[6]*xform[11] + xform[1]*xform[7]*xform[10] + xform[5]*xform[2]*xform[11] - \
                  xform[5]*xform[3]*xform[10] - xform[9]*xform[2]*xform[7] + xform[9]*xform[3]*xform[6]
        inverted[7] = xform[0]*xform[6]*xform[11] - xform[0]*xform[7]*xform[10] - xform[4]*xform[2]*xform[11] + \
                 xform[4]*xform[3]*xform[10] + xform[8]*xform[2]*xform[7] - xform[8]*xform[3]*xform[6]
        inverted[11] = -xform[0]*xform[5]*xform[11] + xform[0]*xform[7]*xform[9] + xform[4]*xform[1]*xform[11] - \
                   xform[4]*xform[3]*xform[9] - xform[8]*xform[1]*xform[7] + xform[8]*xform[3]*xform[5]
        inverted[15] = xform[0]*xform[5]*xform[10] - xform[0]*xform[6]*xform[9] - xform[4]*xform[1]*xform[10] + \
                  xform[4]*xform[2]*xform[9] + xform[8]*xform[1]*xform[6] - xform[8]*xform[2]*xform[5]

        det = xform[0]*inverted[0] + xform[1]*inverted[4] + xform[2]*inverted[8] + xform[3]*inverted[12];
        if (det == 0):
            raise ZeroDivisionError("rmath.Transform.invert(): matrix cannot be inverted.")
        det = 1.0 / det
        self._matrix=[a * det for a in inverted]

        
def getVectorFromAxis(axis):
    ''' return a 3 integer list from a axis string '''
    
    if axis == "x":
        return Vector([1,0,0])
    if axis == "y":
        return Vector([0,1,0])
    if axis == "z":
        return Vector([0,0,1])
        
def getAxisFromVector(vector):
    ''' return a axis string from a integer list '''
    
    if vector[0]:
        return "x"
    if vector[1]:
        return "y"
    if vector[2]:
        return "z"
