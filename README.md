# loop-subdivision

PyOpenGL implementation of Loop Subdivision.

This program was written in about a week as a class assignment. Hence, it hasn't been completed and is still pretty buggy. Currently, the winged-halfedge data structure that holds verticies does not correctly link new vertices, so doing more than one subdivision will cause errors. I will fix this eventually :)

Implements Loop Subdivision: https://graphics.stanford.edu/~mdfisher/subdivision.html

REQUIREMENTS:
This program requires Python3, PyOpenGL, Numpy, and Freeglut.
It has been tested on Ubuntu Linux ONLY. Instructions below are for
Ubuntu:

To install Python3, Pip3, and Freeglut:
sudo apt-get install python3 freeglut3 pip3

To install numpy and PyOpenGl:
sudo pip3 install numpy
sudo pip3 install PyOpenGL

USAGE:

Example:

python3 newview.py object/icos.obj 1 -w 

This will display the icos.obj object after 1 subdivision, as a wireframe (-w)


To run, cd into the project base directory (location of newview.py) and:

python3 newview.p <PATH_TO_OBJ> <OPTIONAL: DIVS> <OPTIONAL: -w>

PATH_TO_OBJ is the path to a .obj file. You could use any .obj file (with
uncertain results), but several .obj files are included for your enjoyment
in the objects/ directory.

DIVS is the number of subdivisions to do, an integer.

-w is an optional flag. Including it displays the object as a wireframe 
(usually prettier.)

CONTROLS:

Dragging the mouse rotates the object.

Arrow keys move the light source. Check it out, the object has a shadow!