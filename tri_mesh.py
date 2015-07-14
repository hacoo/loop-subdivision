#
# tri_mesh.py
#
# Defines a triangle mesh / "winged edge" data structure
# For use in defining 3d objects.

# This file is responsible for loading and storing the triangle mesh, and
# doing operations on the whole mesh.


from geometry import vector, point, ORIGIN
from math import sqrt
from numpy import matrix, dot, array, ndarray
from numpy.linalg import inv, solve
from mesh_geometry import *
import sys


class mesh:
    # Represents a surface as a mesh of winged half edge triangles.
    # Some code adapted from Jim Fix' objects.py
    
    def __init__(self):
        
        self.triangles = [] # A list of triangle objects.
        self.verts = [] # A list of vertices (vertex objects)
        self.edges = {} # a dictionary of edge objects.
        self.shadows = [] # a list of triangle objects, that will
        # be shadows. For testing (should be done in hardware later)
        self.radius = 0.0 
        self.vindex = 0 # Current max vertex index
        self.tindex = 0 # Current max triangle index
        self.sindex = 0 # Current shadow triangle index
        self.p1 = point(10.0, -0.001, 10.0) # point on floor
        self.p2 = point(-10.0, -0.001, -10.0) # another point on the floor
        self.p3 = point(-10.0, -0.001, 10.0) # third point on floor
        
        

    
    def load(self, filename):
        """ Loads a list of triangles from a .obj file FILENAME """
        global vindex, tindex
        vindex = 0
        tindex = 0
        newedge = [None, None, None]
         #dictionary of edges, each should appear only once
        obj_file = open(filename, 'r')
        max = 0.0

        for line in obj_file:
            parts = line.split()
            if len(parts) > 0:
                if parts[0] == 'v':
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    p = vertex(x,y,z, vindex)
                    d2 = (p.loc - ORIGIN).norm2()
                    if d2 > max:
                        max = d2
                
                    vindex = vindex + 1
                    self.verts.append(p)

                    
                elif parts[0] == 'f':
                    i0 = int(parts[1])
                    if len(parts) < 5:
                        # Import as a regular triangle
                        i2 = int(parts[2])-1
                        # We can map f values directly to vertex list indicies
                        i1 = int(parts[1])-1 # my list is indexed from 0 (hence
                        # -1)
                        i3 = int(parts[3])-1
                        #print("Adding triangle: " + str(tindex))
                        newtri = triangle(self.verts[i1], self.verts[i2], self.verts[i3], tindex)

                        # Add the triangles edges and check for pairing
                        newedge[0] = edge(self.verts[i1], self.verts[i2])
                        newedge[1] = edge(self.verts[i2], self.verts[i3])
                        newedge[2] = edge(self.verts[i3], self.verts[i1])

                        for i in range(0,3):
                            newedge[i].triangle = newtri
                            if repr(newedge[i]) not in self.edges:
                                #print("Adding edge: " + repr(newedge[i]))
                                self.edges[repr(newedge[i])] = newedge[i]
                            else:
                                #print("DUPLICATE: " + repr(newedge[i]))
                                newedge[i].pair = self.edges[repr(newedge[i])]
                                # connect the edges
                                self.edges[repr(newedge[i])].pair = newedge[i]
                            #add the edge to the triangle
                            newtri.edge[i] = newedge[i]

                        # Try adding the new edges to the dictionary. If
                        # already there, link the edges.
                        self.triangles.append(newtri) # add to triangles list
                        tindex = tindex + 1

                        # next, we need to go through and recursively
                        # assign triangle "spins".

        self.radius = sqrt(max)
        self.tindex = tindex
        self.vindex = vindex
        self.projectShadows()
       
        self.assignSpins()
    
    def assignSpins(self):
        """ Recursively assign "spin" - internal linking of each triangle
        edge - to each triangle in the surface. """

        sys.setrecursionlimit(5000)
        # first, assign edges for the first triangle
        for i in range(0,3):
            self.triangles[0].edge[i].nextEdge = self.triangles[0].edge[(i+1) % 3]
            
        self.triangles[0].visited = True
        for i in range (0,3):
            self.recAssignSpin(self.triangles[0].edge[i])
            
    def recAssignSpin(self,startEdge):
        """ Takes startEdge, the connected edge in a triangle that
        already has assigned spins. Uses this to set spin in the
        current triangle, and recursively goes to all neightbors. """

        if startEdge == None:
            return # No paired triangle to this edge
        if startEdge.pair == None:
            return
            
        currentTri = startEdge.pair.triangle
        pairedEdge = startEdge.pair
        
        if currentTri.visited == True:
            return # triangle already set

        # find the "second vertex" of the edge - determines
        # its direction
        currentTri.visited = True
        secondVertex = startEdge.sharedVertex(startEdge.nextEdge)

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

        #for edge in currentTri.edge:
                #self.recAssignSpin(edge)

        if secondEdge.pair != None:
            if secondEdge.pair.triangle.visited != True:
                self.recAssignSpin(secondEdge)

        if thirdEdge.pair != None:
            if thirdEdge.pair.triangle.visited != True:
                self.recAssignSpin(thirdEdge)
              
                
            
        return

    def projectShadows(self):
        """ Projects each triangle onto the FLOOR to create a shadow.
        Since the position of the floor is currently fixed, this isn't
        dynamic (it just assumes the floor is a plane containing the points
        set in compile()) Also keeps the light position static for now. """

        p1 = self.p1
        p2 = self.p2
        p3 = self.p3

        p1v = p1.minus(p2)
        p2v = p2.minus(p3) # these are two vectors on the plane
    

        l = point(1.0, 1.0, 0.0) # position of the light
        nv = p1v.cross(p2v) # plane normal vector
        nv = nv.unit()

        # First, we need to compute a vector that is normal to the plane
        # and intersects with l. This is computed by adding two vectors on the
        # plane, and seeing where the intersect with a l + d*nv.

        lp = l.minus(p1)

        # create matrices to solve
        a = array([[p2v.dx, p1v.dx, nv.dx], [p2v.dy, p1v.dy, nv.dy], [p2v.dz, p1v.dz, nv.dz]])
        b = array([[lp.dx],[lp.dy], [lp.dz]])

        solution = solve(a,b)
        d = solution[2,0]

        # Now we know how far l is from the plane. Next, compute the
        # distance object vertices to the plane, and use this information
        # to project each vertex onto the plane.

        for tri in self.triangles:
            for vert in tri.verts:
                v = vert.loc
                pv = v.minus(p1)
                b = array([[pv.dx],[pv.dy], [pv.dz]])

                solution = solve(a,b)
                j = solution[2,0]


                # We know how far the vertex is from the plane.
                # Now project it onto the plane.

                lv = v.minus(l)
                ratio = (float) (d/(d-j))

                vprime = l.plus(ratio*lv) # this is the projected point on the
                # plane
                self.shadows.append(vprime)
    
        
        
    def compile(self):
        """ returns compiled vertices, normals, colors for VBO """
            
        vbuf = []
        nbuf = []
        cbuf = []
        sbuf = []

        #self.triangles[38].verts[0].color = [1.0, 0.0, 0.0]
#        for tri in self.triangles[38].verts[0].adj_tris:
 #           for v in tri.verts:
  #              v.color = [1.0, 0.0, 0.0]
        
        for tri in self.triangles:
            for i in range(0,3):
                tri.verts[i].setNormal()
                vbuf.extend(tri.verts[i].loc.components())
                cbuf.extend(tri.verts[i].color)
                nbuf.extend(tri.verts[i].normal.components())
                                 

        # make a floor
        # vbuf.extend([-10.0,-0.001,-10.0])
        # vbuf.extend([ 10.0,-0.001,-10.0])
        # vbuf.extend([ 10.0,-0.001, 10.0])
        # vbuf.extend([-10.0,-0.001,-10.0])
        # vbuf.extend([ 10.0,-0.001, 10.0])
        # vbuf.extend([-10.0,-0.001, 10.0])
        # nbuf.extend([0.0,1.0,0.0])
        # nbuf.extend([0.0,1.0,0.0])
        # nbuf.extend([0.0,1.0,0.0])
        # nbuf.extend([0.0,1.0,0.0])
        # nbuf.extend([0.0,1.0,0.0])
        # nbuf.extend([0.0,1.0,0.0])
        # cbuf.extend([0.4,0.65, 0.45])
        # cbuf.extend([0.4,0.65, 0.45])
        # cbuf.extend([0.4,0.65, 0.45])
        # cbuf.extend([0.4,0.65, 0.45])
        # cbuf.extend([0.4,0.65, 0.45])
        # cbuf.extend([0.4,0.65, 0.45])


        return vbuf, nbuf, cbuf


    def intersect_ray(self,R,d):
        """ Returns facet hit by a ray. Written by Jim Fix
        fix@reed.edu """
        selected = None
        dist = sys.float_info.min
        mouse_ray = ray(R, d)
        for tri in self.triangles:
            sect = tri.ray_intersect(mouse_ray)

            if sect:
                #if sect[2] > dist:
                  #  dist = sect[2] 
                   # selected = tri
                return tri
                        
                        
                        

def main(argc, argv):
    #t1 = triangle(point(0,0,0), point(1,1,1), point(2,2,2))
    print("hello")
    #print(repr(t1))
    mesh1 = mesh()
    mesh1.load(argv[1])

    print("#################################################\n")
    for vert in mesh1.verts:
        print(repr(vert))
        print("\n")

    print("#################################################\n")

    print(len(mesh1.triangles))
    for tri in mesh1.triangles:
        print(repr(tri))
        for i in range(0,3):
            print(str(tri.edge[i].pair.triangle.index))
            #if(tri.edge[i].pair == None):
             #   print("Null edge in triangle: " + str(tri.index))
        print("\n")

    print("#################################################\n")
    print(len(mesh1.edges))
    for edge in mesh1.edges:
        #print(edge)
        print(repr(mesh1.edges[edge]))
        #print("\n")
    
    

    return 0
    


if __name__ == '__main__': main(len(sys.argv),sys.argv)