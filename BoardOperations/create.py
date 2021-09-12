import lxml.etree as etree
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *
from collections import namedtuple

def rectangle(x1,y1,x2,y2,layer):
   rectangle = etree.Element(RECTANGLE)
   rectangle.set(X1, str(x1))
   rectangle.set(Y1, str(y1))
   rectangle.set(X2, str(x2))
   rectangle.set(Y2, str(y2))
   rectangle.set(LAYER, str(layer))

   return rectangle

def circle(xC,yC,width,radius,layer):
   circle = etree.Element(CIRCLE)
   circle.set(X, str(xC))
   circle.set(Y, str(yC))
   circle.set(WIDTH, str(width))
   circle.set(RADIUS, str(radius))
   circle.set(LAYER, str(layer))

   return circle

def hole(x,y,drill):
   hole = etree.Element(HOLE)
   hole.set(X, str(x))
   hole.set(Y, str(y))
   hole.set(DRILL, str(drill))

   return hole

def via(x,y,drill,shape,hasStop=False):
   via = etree.Element(VIA)

   via.set(X, str(x))
   via.set(Y, str(y))
   via.set('extent', '1-16')
   via.set(DRILL, str(drill))
   via.set(SHAPE, str(shape))
   via.set('alwaysstop', 'yes' if hasStop else 'no')

   return via

def wire(x1,y1,x2,y2,width,layer):
   wire = etree.Element(WIRE)

   wire.set(X1, str(x1))
   wire.set(Y1, str(y1))
   wire.set(X2, str(x2))
   wire.set(Y2, str(y2))
   wire.set(WIDTH, str(width))
   wire.set(LAYER, str(layer))

   return wire
