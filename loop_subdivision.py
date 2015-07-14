# Henry Cooney, Math 385 -- loop_subdivision.py
# 
# Implements loop subdivision on a winged half-edge data structure.
#
# Takes a triangle MESH object, and subdivides it into
# a smoother mesh.
#
# See http://research.microsoft.com/en-us/um/people/cloop/thesis.pdf
# if you would like an in-depth explanation of the math behind this.

from tri_mesh import *
from mesh_geometry import *
from geometry import vector, point, ORIGIN
from math import sin, cos, pi
import sys



# Collection of methods for implementing loop subdivision.
# Class is merely used as a convenient way of sharing variables between
# functions 
    
tris = [] # list of triangles
edges = {} # Dictionary of edges
vertices = [] # list of vertex objects
tindex = 0 # Current maximum triangle index
vindex = 0 # current maximum vertex index
    
    
def subdivide(oldmesh):
    """ Wrapper function that initiates loop subdivision on triangle
    mesh MESH. Returns subdivided mesh (or None if subdivision could
    not be performed). """

    global tris, edges, vertices, tindex, vindex

    newmesh = mesh() # This is the subdivided mesh object, will be
    # populated and returned


    newmesh.radius = oldmesh.radius
    # Start the triangle subdivision on newmesh.
    subdivideTriangles(newmesh, oldmesh)

    # Fix triangle adjacencies in the mesh. This should be disabled
    # in the future, when I get the mesh to import this information
    # during mesh construction. This method will run into problems
    # with incomplete fans.

#    for t in newmesh.triangles:
 #       for v in t.verts:
  #          addAdjTris(v)

    
    return newmesh
    
def subdivideTriangles(newmesh, oldmesh):
    """ Wrapper function, starts triangle subdivision on NEWMESH. and
    begins recursive walk across facets of old mesh. New triangles
    are linked appropriately and added to NEWMESH. """
    
    # First, reset the visited status of the mesh
    for tri in oldmesh.triangles:
        tri.visited = False


    # Subidivide the first triangle. This will be a "seed" to start recursive
    # subdivision of the remaining triangles.
    print("Subdividing " + str(len(oldmesh.triangles)) + " triangles.")
    tri = oldmesh.triangles[0]
    tri.visited = True
    new_v = list(range(6)) # This will contain the new smoothed vertices,
    # which will be linked into new triangles.
    temp1 = None # temporary vertex
    temp2 = None # temporary vertex
        
    # start with the first edge and work around.
    curr_ed = tri.edge[0]
    for i in range(0,3):
        # Select a vertex to work on. Each edge is
        # responsible for 1 tip vertex and the midpoint.
        if curr_ed.verts[0] in curr_ed.nextEdge.verts:
            temp1 = subdivide_vertex(curr_ed.verts[1])
            temp1.color = curr_ed.verts[1].color
            new_v[2*i] = temp1
        else:
            temp1 = subdivide_vertex(curr_ed.verts[0])
            temp1.color = curr_ed.verts[0].color
            new_v[2*i] = temp1
            # now subdivide the edge itself
            
        temp2 = subdivide_edge(curr_ed)
        # the color of the split edge vertex is the mean
        # of the two edge vertices
        temp2.color = blendColor(curr_ed)
        new_v[2*i + 1] = temp2
        curr_ed = curr_ed.nextEdge

    # Add the new vertices to the new mesh
    for vert in new_v:
        newmesh.verts.append(vert)
        vert.index = newmesh.vindex
        newmesh.vindex += 1
        
    # Now assign the new vertices new triangles

    new_t = list(range(4))
    new_t[0] = triangle(new_v[0], new_v[1], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[0])
    newmesh.tindex += 1

    new_t[1] = triangle(new_v[1], new_v[2], new_v[3], newmesh.tindex)
    newmesh.triangles.append(new_t[1])
    newmesh.tindex += 1

    new_t[2] = triangle(new_v[3], new_v[4], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[2])
    newmesh.tindex += 1

    new_t[3] = triangle(new_v[1], new_v[3], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[3])
    newmesh.tindex += 1

    # Now create triangle edges
    newedge = [None, None, None]
    for ntri in new_t:
        newedge[0] = edge(ntri.verts[0], ntri.verts[1])
        newedge[1] = edge(ntri.verts[1], ntri.verts[2])
        newedge[2] = edge(ntri.verts[0], ntri.verts[2])

        ntri.edge[0] = newedge[0]
        ntri.edge[1] = newedge[1]
        ntri.edge[2] = newedge[2]

        # add the new edges to the mesh edge dictionary, also, set
        # their triangle link
        for i in range(3):
            newedge[i].triangle = ntri
            if repr(newedge[i]) not in newmesh.edges:
                newmesh.edges[repr(newedge[i])] = newedge[i]
                            
    # The triangles edges need to be given proper next edge linking and
    # pair linking. Because we know how the triangle was constructed, this
    # can be done manually, which is faster (no need to look up edge paris, etc).
    # Draw a diagram of the subdivided triangles and you will understand how this
    # works.

    new_t[0].edge[1].pair = new_t[3].edge[2]
    new_t[3].edge[2].pair = new_t[0].edge[1]

    new_t[1].edge[2].pair = new_t[3].edge[0]
    new_t[3].edge[0].pair = new_t[1].edge[2]
    
    new_t[2].edge[2].pair = new_t[3].edge[1]
    new_t[3].edge[1].pair = new_t[2].edge[2]

    # Now link the edges in the right order. Edges are already
    # in the proper order.
    
    for ntri in new_t:
        ntri.edge[0].nextEdge = ntri.edge[1]
        ntri.edge[1].nextEdge = ntri.edge[2]
        ntri.edge[2].nextEdge = ntri.edge[0]


    # The edge splits that result from subdivision need to be linked
    # to the edge that created them. Send the subdivided edges to the
    # correspoding oldmesh edge:

    curr_ed = tri.edge[0]
              
    curr_ed.subdivision[0] = new_t[0].edge[0]
    curr_ed.subdivision[1] = new_t[1].edge[0]
    curr_ed = curr_ed.nextEdge

    curr_ed.subdivision[0] = new_t[1].edge[1]
    curr_ed.subdivision[1] = new_t[2].edge[0]
    curr_ed = curr_ed.nextEdge

    curr_ed.subdivision[0] = new_t[2].edge[1]
    curr_ed.subdivision[1] = new_t[0].edge[2]
      
    
    # The first triangle has been set, so we can recursively visit
    # other triangles and subdivide them using a similar process (but linking
    # back to the previous triangle). Parameter assignment is not
    # straightforward, draw the triangle mesh if you want to understand
    # this.

    # Recursion depth limit? HA
    sys.setrecursionlimit(1000000)
        
    recursive_subdivide(newmesh, oldmesh, tri.edge[0].pair, 
                        new_t[0].edge[0], new_t[1].edge[0], 
                        new_v[0], new_v[2], new_v[1])
    
    recursive_subdivide(newmesh, oldmesh, tri.edge[1].pair,
                        new_t[1].edge[1], new_t[2].edge[0],
                        new_v[2], new_v[4], new_v[3])

    recursive_subdivide(newmesh, oldmesh, tri.edge[2].pair,
                        new_t[2].edge[1], new_t[0].edge[2],
                        new_v[4], new_v[0], new_v[5])

    sys.setrecursionlimit(10000)

    return

 
    
    
def recursive_subdivide(newmesh, oldmesh, startedge, e0, e1, v0, v1, midpoint):
    """ Uses information from the previously subdivided triangle to initiate
    subdivision in the neighboring triangle.
    NEWMESH is the new mesh to add to, OLDMESH is the old mesh to subdivide.
    TRI is the triangle to be subdivided.
    E0, E1, V0, V1, and MIDPOINT are the peices of the subdivided triangle
    edge that borders TRI. E0 and E1 are edges, V0, V1 and MIDPOINT are vertices.
    E0 and V0 come first in the previous triangles mesh-edge orderint (i.e, v0's
    edge's next edge contains v1 in the previous triangle prior to subdivision).
    MIDPOINT is the subdivided midpoint vertex. """

    if startedge == None:
        return

    tri = startedge.triangle

    if tri == None:
        
        return
        
    if tri.visited == True:
        # The triangle is already done. However, it may need to be
        # linked back to the previous triangle. Do that now.

        if e0.pair != None and e1.pair != None:
            # the triangle are already linked.
            return

              
        otherEdges = startedge.subdivision
        if otherEdges[0] == None or otherEdges[1] == None:
            print ("Error - other edge not set")
            
        e0.pair = otherEdges[1]
        otherEdges[1].pair = e0
        e1.pair = otherEdges[0]
        otherEdges[0].pair = e1

        # share adjacent triangle information with
        # vertices in the other edges
        for e in otherEdges:
            for v in e.verts:
                v.adj_tris.append(e.pair.triangle)


        # Determine which is the midpoint vertex. This one needs
        # to have the central triangle of the other subdivision
        # added to its adj_tris.

        if otherEdges[0].verts[1] in otherEdges[1].verts:
            mp = otherEdges[0].verts[1]
        else:
            mp = otherEdges[0].verts[0]

        # figure out the middle triangle
        mp.adj_tris.append(e0.nextEdge.pair.triangle)



        # import vertices from the other triangle

        e0.verts[0] = otherEdges[1].verts[1]
        e0.verts[1] = otherEdges[1].verts[0]

        e1.verts[0] = otherEdges[0].verts[1]
        e1.verts[1] = otherEdges[0].verts[0]

        # Test recoloring
        for e in otherEdges:
            for v in e.verts:
                v.color = [0.0, 1.0, 1.0]


        return
        
    tri.visited = True
    new_v = list(range(6)) # This will contain the new smoothed vertices,
    # which will be linked into new triangles.
    temp1 = None # temporary vertex
    temp2 = None # temporary vertex

    # First 3 vertexes are imported from previous triangle.
    new_v[2] = v0
    new_v[1] = midpoint
    new_v[0] = v1
        
    # The first edge is done. Do the next two
    curr_ed = startedge.nextEdge
    for i in range(1,3):
        # Select a vertex to work on. Each edge is
        # responsible for only 1 vertex (and the midpoint)

        # First, check if the edge has already been done. If so,
        # import the corresponding vertices
        #if False:
        if curr_ed.pair != None and curr_ed.pair.triangle.visited == True and i != 1:
            # Import edge information from the corresponding triangle
            # and link
            otherEdges = curr_ed.pair.subdivision
            
            new_v[2*i] = otherEdges[0].verts[0]
            new_v[2*i + 1] = otherEdges[0].verts[1]
            
            
            
        else:
            if i != 1:
                if curr_ed.verts[0] in curr_ed.nextEdge.verts:
                    temp1 = subdivide_vertex(curr_ed.verts[1])
                    temp1.color = curr_ed.verts[1].color
                    new_v[2*i] = temp1
                else:
                    temp1 = subdivide_vertex(curr_ed.verts[0])
                    temp1.color = curr_ed.verts[0].color
                    new_v[2*i] = temp1

            # now subdivide the edge itself
            temp2 = subdivide_edge(curr_ed)
            # the color of the split edge vertex is the mean
            # of the two edge vertices
            temp2.color = blendColor(curr_ed)
            new_v[2*i + 1] = temp2
            curr_ed = curr_ed.nextEdge

    # Add the new vertices to the new mesh
    for i in range(3,6):
        newmesh.verts.append(new_v[i])
        new_v[i].index = newmesh.vindex
        newmesh.vindex += 1

    # Now assign the new vertices new triangles

    new_t = list(range(4))
    new_t[0] = triangle(new_v[0], new_v[1], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[0])
    newmesh.tindex += 1

    new_t[1] = triangle(new_v[1], new_v[2], new_v[3], newmesh.tindex)
    newmesh.triangles.append(new_t[1])
    newmesh.tindex += 1

    new_t[2] = triangle(new_v[3], new_v[4], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[2])
    newmesh.tindex += 1

    new_t[3] = triangle(new_v[1], new_v[3], new_v[5], newmesh.tindex)
    newmesh.triangles.append(new_t[3])
    newmesh.tindex += 1

    # Now create triangle edges. 
    newedge = [None, None, None]
    for ntri in new_t:
        newedge[0] = edge(ntri.verts[0], ntri.verts[1])
        newedge[1] = edge(ntri.verts[1], ntri.verts[2])
        newedge[2] = edge(ntri.verts[0], ntri.verts[2])

        ntri.edge[0] = newedge[0]
        ntri.edge[1] = newedge[1]
        ntri.edge[2] = newedge[2]

        # add the new edges to the mesh edge dictionary, also, set
        # their ntriangle link
        for i in range(3):
            newedge[i].triangle = ntri
            if repr(newedge[i]) not in newmesh.edges:
                newmesh.edges[repr(newedge[i])] = newedge[i]
            else:
                # we need to link it to the equivalent edge already in dict
                newedge[i].pair = newmesh.edges[repr(newedge[i])]
                newmesh.edges[repr(newedge[i])].pair = newedge[i]
                
    # pair the first two triangles to the edges that were passed in
    
    new_t[0].edge[0].pair = e1
    e1.pair = new_t[0].edge[0]
    new_t[1].edge[0].pair = e0
    e0.pair = new_t[1].edge[0]

    # In addition to this, check the other two triangles and see if
    # they need to be linked. This occurs if the adjacent triangle


    # The triangles edges need to be given proper next edge linking and
    # pair linking. Because we know how the triangle was constructed, this
    # can be done manually, which is faster (no need to look up edge paris, etc).
    # Draw a diagram of the subdivided triangles and you will understand how this
    # works.

    new_t[0].edge[1].pair = new_t[3].edge[2]
    new_t[3].edge[2].pair = new_t[0].edge[1]

    new_t[1].edge[2].pair = new_t[3].edge[0]
    new_t[3].edge[0].pair = new_t[1].edge[2]
    
    new_t[2].edge[2].pair = new_t[3].edge[1]
    new_t[3].edge[1].pair = new_t[2].edge[2]

    # Now link the edges in the right order. Edges are already
    # in the proper order.
    
    for ntri in new_t:
        ntri.edge[0].nextEdge = ntri.edge[1]
        ntri.edge[1].nextEdge = ntri.edge[2]
        ntri.edge[2].nextEdge = ntri.edge[0]

        
    # The edge splits that result from subdivision need to be linked
    # to the edge that created them. Send the subdivided edges to the
    # correspoding oldmesh edge:

    curr_ed = startedge
              
    curr_ed.subdivision[0] = new_t[0].edge[0]
    curr_ed.subdivision[1] = new_t[1].edge[0]
    curr_ed = curr_ed.nextEdge

    curr_ed.subdivision[0] = new_t[1].edge[1]
    curr_ed.subdivision[1] = new_t[2].edge[0]
    curr_ed = curr_ed.nextEdge

    curr_ed.subdivision[0] = new_t[2].edge[1]
    curr_ed.subdivision[1] = new_t[0].edge[2]
      

    # Now subdivide adjacent triangles.

    recursive_subdivide(newmesh, oldmesh, startedge.pair, 
                        new_t[0].edge[0], new_t[1].edge[0], 
                        new_v[0], new_v[2], new_v[1])
    
    recursive_subdivide(newmesh, oldmesh, startedge.nextEdge.pair,
                        new_t[1].edge[1], new_t[2].edge[0],
                        new_v[2], new_v[4], new_v[3])

    recursive_subdivide(newmesh, oldmesh, startedge.nextEdge.nextEdge.pair,
                        new_t[2].edge[1], new_t[0].edge[2],
                        new_v[4], new_v[0], new_v[5])


    

        
def subdivide_vertex(vertex):
    """ Performs Loop subdivision to reposition a vertex. Determines
    whether the vertex exists on a complete or boundary fan. Then
    computes and returns the smoothed vertex position. """


    # Error check. If the vertex can't be repositioned, leave it alone
    if len(vertex.adj_tris) == 0 or len(vertex.adj_tris) == 1:
        return vertex
        
     # First, determine if we are on a complete or boundary fan.
    for tri in vertex.adj_tris:
        
        for e in tri.edge:
            if e.pair == None:
                # this could be a boundary fan. Check to see if this edge
                # contains the vertex.
                if vertex in e.verts:
                    return subdivide_boundary_fan_vertex(vertex)

    # If you get through this loop, the fan shouldn't be a boundary fan.
    return subdivide_interior_fan_vertex(vertex)

    #vertex.color = [0.0, 0.0, 1.0]
    #return vertex


def subdivide_boundary_fan_vertex(vertex):
    """ Repositions a boundary fan vertex VERTEX. A boundary fan is defined
    as a fan containin a triangle that has a boundary edge conatining the
    center vertex (i.e., it is a fan around VERTEX that is incomplete). """

    # Boundary fan vertex formula: 1/8v0 + 3/4v + 1/8vn-1
    # v is central vertex, v0 and vn-1 are the edge vertices

    # First, determine v0 and vn-1

    
    
    
    
    
    return vertex


def subdivide_interior_fan_vertex(vert):
    """ Repositions an interior fan vertex VERTEX. A interior fan is defined
    as a fan made up of a contiguous ring of triangles. """

    
    # c1 and c2 are constants used to move the vertex
    n = len(vert.adj_tris)

    # generate constants to multiply each vertex by
    b = Beta(n)
    k = 1 - n*(b)

    # Create a list of vertices at the edge of the fan.
    # Do this by starting with one fan triangle, then
    # using winged data structure to go around the fan.
    
    vi = list(range(n))

    # find a starting edge
    tri = vert.adj_tris[0]

    for e in tri.edge:
        if vert in e.verts:
            if vert not in e.nextEdge.verts:
                current_edge = e
                break

    # Get the ring verts
    for i in range(n):
        if current_edge.verts[0] == vert:
            vi[i] = current_edge.verts[1]
        else:
            vi[i] = current_edge.verts[0]
        # Go to the next triangle in the fan
        current_edge=current_edge.pair.nextEdge

    # Now sum all the fan edge vertices:
    x = 0
    y = 0
    z = 0
    for i in vi:
        x += i.loc.x
        y += i.loc.y
        z += i.loc.z
        
    x *= b
    y *= b
    z *= b
    
    x += (k * vert.loc.x)
    y += (k * vert.loc.y)
    z += (k * vert.loc.z)
    
    vprime = vertex(x, y, z, vert.index)
    
    return vprime
    
                
            
def Beta(n):
    """ Generates the Loop subdivision constant, beta, for an interior
    triangle fan of N vertices. This formula was obtained from Priceton
    slides (http://www.cs.princeton.edu/courses/archive/fall02/cs526/lectures/subdivision.pdf)
    The formula we derived in class did not seem to work :P """
    
    return (1/n)*((5/8) - pow(((3/8)+0.25*(cos(2*pi/n))),2))

            


def subdivide_edge(edge):
    """ Performs Loop subdivision to split edge EDGE. Computes
    and returns vertex VPRIME, which is the subdivided midpoint of
    edge EDGE. """

    # determine if this an interior or boundary edge, and
    # return the appropriate vertex.

    v0 = edge.verts[0].loc
    v1 = edge.verts[1].loc
    
    if edge.pair == None:
        # compute as boundary edge.
        # v' = 1/2 v0 + 1/2 v1
        p = addPoints(scalePoint(v0, 0.5), scalePoint(v1, 0.5))
        return vertex(p.x, p.y, p.z, 0)
    
    else:
        # compute as interior edge
        # v' = 1/8 f0 + 3/4 v0 + 3/4 v1 + 1/8 f1
        # (f0 and f1 are verticies in triangles on either side of edge,
        #  opposite to edge)

        f0 = [a for a in edge.triangle.verts if a not in edge.verts]
        f0 = f0[0].loc
        f1 = [a for a in edge.pair.triangle.verts if a not in edge.verts]
        f1 = f1[0].loc
        p = addPoints(addPoints(scalePoint(f0, (1/8)), scalePoint(v0, (3/8))), 
                      addPoints(scalePoint(v1, (3/8)), scalePoint(f1, (1/8))))
                      
        return vertex(p.x, p.y, p.z, 0)
    
        

def isFanContinuous(vertex):
    """ Tests whether a triangle fan is continuous (interior) or
    non-continuous (boundary) around vertex VERTEX.
    If it is continuous, returns True, if not, returns False,
    if there is an error, returns None. """

    
    # Start at one adjacent triangle and go around the fan. If you
    # can get back around to a triangle that's been visited before,
    # the fan is continuous.
    count = 0
    numTriangles = len(vertex.adj_tris)
    
    # Figure out what edge to start on
    curr_ed = getFanStartEdge(vertex)
    startTri = curr_ed.triangle

    # Go around the fan, report whether it is continuous
    while count < numTriangles:
        curr_ed = curr_ed.pair
        if curr_ed == None:
            return False
        curr_ed = curr_ed.nextEdge
        count = count + 1

    # If you could move around the whole fan without encountering
    # a boundary, the fan is continuous.

    if curr_ed.triangle.index != startTri.index:
        print("Error in isFanContinuous")
        return None

    return True
        
        

                      
def getFanStartEdge(vertex):
    """ Finds the "starting" edge of a fan around vertex VERTEX.
    The starting edge is defined as the edge paired to an edge who's
    paired edge contains VERTEX, but whose next edge does not contain
    VERTEX. If such and edge cannot be found, returns None. """

    for e in vertex.adj_tris[0].edge:
        if vertex in e.verts and vertex in e.nextEdge.verts:
            return e.nextEdge

    return None

def addPoints(p0, p1):
    """ Adds two points, p1 and p0, component wise. """
    return point(p0.x + p1.x, p0.y + p1.y, p0.z + p1.z)

def scalePoint(p, scalar):
        """ Scales all coordinates of the point by scalar and returns.
        the resulting point. """
        
        return point(scalar*p.x, scalar*p.y, scalar*p.z)

def blendColor(edge):
        """ computes the mean of the colors of and edge's two vertices,
            component-wise. Returns as RGB array """

        c0 = edge.verts[0].color
        c1 = edge.verts[1].color

        return [1/2*(c0[0] + c1[0]), 1/2*(c0[0] + c1[1]), 1/2*(c0[0] + c1[2])]

        

def addAdjTris(vertex):
    """ Adds all triangles in the contiguous fan around the vertex VERTEX
    to that vertex's adj_tris list. This method is mostly for debugging,
    avoid it, since it will NOT work for incomplete fans, and isn't
    very efficient. """

    # First find the next triangle in the fan

    startedge = None
    
    for e in vertex.adj_tris[0].edge:
        if vertex in e.verts:
            if vertex not in e.nextEdge.verts:
                startedge = e
                break

    if startedge != None:
        addAdjTris_rec(vertex, vertex.adj_tris[0], startedge)

    return

def addAdjTris_rec(vertex, start_tri, startedge):
    """ Attempts to add TRI to VERTEX's adj_tri's field, and moves
    on to the next triangle in the fan. """


    if startedge.pair == None or startedge.pair.triangle == None:
        return

    tri = startedge.pair.triangle

    if start_tri == tri:
        # we have made it all the way around the fan.
        return
    
    
    if tri not in vertex.adj_tris:
        vertex.adj_tris.append(tri)

    # move to the next vertex

    addAdjTris_rec(vertex, start_tri, startedge.nextEdge.pair)
    

    return
    
    
                      

                
            
            

        

    
    

    
    