# Defines several geomteric objects for use in the windged half-edge data
# structure, for representing 3-d surfaces.
# Includes:
#
# Triangle: Contains 3 edges and 3 vertices. Has methods for computing normal,
# ray intersection, etc.
#
# Ray: Simple packaged class containing and source point and direction vector.
#
# Vertex: Triangle vertex, contains a position point and indexing information.
#
# Edge: Triangle edge, contains 2 vertices, a paired edge (adjacent edge in
# another triangle), and a next edge (next edge inside the local triangle).


from geometry import vector, point, ORIGIN
from math import sqrt
from numpy import matrix, dot, array, ndarray
from numpy.linalg import inv, solve
import sys


class triangle:
    def __init__(self, v1, v2, v3, i):
        # v1, v2, and v3 should be integer indicies into the vertext list!!
        self.index = i # index in container class list
        self.verts = [v1, v2, v3]
        self.visited = False
        self.edge = [None, None, None]
        self.normal = self.normal()

        for v in self.verts:
            v.adj_tris.append(self)

        # Functions below adapted from Jim Fix' objects.py
    def __getitem__(self,i):
        return self.verts[i]

    def __repr__(self):
        return("Index: " + str(self.index) + ', verts: ' + str(self.verts[0].index) + ' ' + str(self.verts[1].index) + ' ' + str(self.verts[2].index))

    def normal(self):
        p0 = self.verts[0].loc
        p1 = self.verts[1].loc
        p2 = self.verts[2].loc
        return (p1-p0).cross(p2-p0).unit()

    def ray_intersect(self, ray1):
        """ Computes intersection of this triangle facet and ray RAY1.
        MINUS_Z is a vector along the negative-z axis into the scene.
        returns a point on the triangle if they intersect, else returns
        none. """

        normalVec = self.normal.scale(-1)
        if (ray1.towards.dot(normalVec)<=1.0e-8):
            return None # the ray is parallel to the triangle,
            # thus, it either misses or hits the triangle edge-on.
            
        
        # The intersection of ray1 and this triangle is t times the
        # vector (ray1.source + unit). This is some point on the triangle,
        # t is computed as follows:

        t = -(normalVec.dot(ray1.source - self.verts[0].loc)) / (normalVec.dot(ray1.towards))
        P = ray1.source.plus(ray1.towards.scale(t)) # Point on plane that ray1 hits
        Pmat = array([[P.x],
                      [P.y],
                      [P.z]]) # t, in numpy format
        
       
    

        M = array([[self.verts[0].loc.x, self.verts[1].loc.x, self.verts[2].loc.x],
                    [self.verts[0].loc.y, self.verts[1].loc.y, self.verts[2].loc.y],
                    [self.verts[0].loc.z, self.verts[1].loc.z, self.verts[2].loc.z]])
        try:
            solution = solve(M, Pmat)
        except ValueError:
            if ValueError == LinAlgError:
                print("Linear Algebra Error \n")
                return None

        barycentric = point(solution[0,0], solution[1,0], solution[2,0])

        if barycentric.x < 0.0 or barycentric.y < 0.0 or barycentric.z < 0.0:
            return None

        if barycentric.x > 1.0 or barycentric.y > 1.0 or barycentric.z > 1.0:
            return None

        return P

        

    def recAssignSpin(self,startEdge):
        """ Takes startEdge, the connected edge in a triangle that
        already has assigned spins. Uses this to set spin in the
        current triangle, and recursively goes to all neightbors. """

        if startEdge == None:
            return # No paired triangle to this edge
            
        currentTri = startEdge.pair.triangle
        pairedEdge = startEdge.pair
        
        if currentTri.visited == True:
            return # triangle already set

        # find the "second vertex" of the edge - determines
        # its direction
        currentTri.visited = True
        secondVertex =startEdge.sharedVertex(startEdge.nextEdge)

        # find the edge in the new triangle that does not share
        # this vertex

        # This ugly code connects each edge to the appropriate next
        # edge. The logic is that the next edge should not
        # share the vertex shared with the preceeding edge.
        
        for i in range(0,3):
            if currentTri.edge[i].containsVertex(secondVertex) == False:
                secondEdge = currentTri.edge[i]
                pairedEdge.nextEdge = secondEdge
                break
        # Do the same thing (bascially) for the third edge:

        secondVertex = pairedEdge.sharedVertex(secondEdge)
        for i in range(0,3):
            if currentTri.edge[i].containsVertex(secondVertex) == False:
                thirdEdge = currentTri.edge[i]
                secondEdge.nextEdge = thirdEdge
                thirdEdge.nextEdge = pairedEdge
                break

        # now all triangle edge are connected! Go to neighboring triangles
        # and set them.

        for edge in currentTri.edge:
            self.recAssignSpin(edge)
            
        return


    def computeVertexNormals(self):
        """ Sets vertex normals for all 3 vertices """
        e1 = self.verts[0].loc.minus(self.verts[1].loc)
        e2 = self.verts[0].loc.minus(self.verts[2].loc)
        e3 = self.verts[1].loc.minus(self.verts[2].loc)

        n2 = e1.cross(e2)
        n3 = e2.cross(e3)
        n1 = e3.cross(e1)

        self.verts[0].normal = n1
        self.verts[1].normal = n2
        self.verts[2].normal = n3


        

class ray:
    def __init__(self, p1, direction):
        """ RAY class contains a point source and a unit vector
        towards. """ 
        self.source = p1
        self.towards = direction.unit()
        
        
        


class edge:
    # A half-edge for use in a windged-half-edge data structure
    def __init__(self, v1, v2):
        """Init: v1 and v2 are the vertices the edge spans between.
           Pair is half-edge in the corresponding adjacent triangle,
           next is the next edge in the current triangle. Don't initialize
           them. """
        if v1.index <= v2.index:
            self.verts = [v1, v2] # The vertices are always in order. So, shared
            # edges can easily be compared.
        else:
            self.verts = [v2, v1] # 
        self.triangle = None 
        self.pair = None
        self.nextEdge = None
        self.subdivision = [None, None] # Contains subdivided edges
        # for loop subdivision
        

    def isSharedEdge(self, i1, i2):
        """ Returns True if the vertices of this edge match indexes i1 and i2.
        Else, returns false. """

        if(i1 == v1 and i2 == v2) or (i1 == v2 and i2 == v1):
            return True

        else:
            return False
            

    def sharedVertex(self, otherEdge):
        """ returns the index of a vertex shared by this edge and
        otherEdge, or None if nothing shared (if they share two
        vertices, only returns one of them) """

        for vert in self.verts:

            for othervert in otherEdge.verts:
                if vert.index == othervert.index:
                    return vert

        return False

    def containsVertex(self, v):
        """ returns true if this edge contains vertex v, else
        returns false. """

        if self.verts[0].index == v.index or self.verts[1].index == v.index:
            return True
        else:
            return False
            
    def __repr__(self):
         return str(str(self.verts[0].index) + ' ' + str(self.verts[1].index))



class vertex:
    def __init__(self, x,y,z,i):
        self.index = i # index in list. 
        self.loc = point(x,y,z)
        self.adj_tris = [] # indices of triangles that are adjacent to this
        # triangle
        #self.color = [0.5,0.45,0.57] # default color - a nice stony white.
        self.color = [1.0, 0.0, 1.0] # bright purple!!!!
        self.normal = None
        self.subdivided = False # flag whether this edge has been subdivided yet

    def __repr__(self):
        return(repr(self.loc) + " index: " + str(self.index) + "\n Adjacent tris: " + ' '.join(str(self.adj_tris[e].index) for e in range(0, len(self.adj_tris))))

    def around(self):
        return fan(self)

    # def setSmoothNormal(self):
    #     for tri in self.adj_tris:
    #         n = 

    def setNormal(self):
        """ Set normal by summing normals of adjacent triangles """
        for tri in self.adj_tris:
            normalVec = vector(0.0, 0.0, 0.0)
            normalVec = normalVec + tri.normal
            
        self.normal = normalVec.unit()
        #self.normal = -1.0*self.normal
        return self.normal
            
 
