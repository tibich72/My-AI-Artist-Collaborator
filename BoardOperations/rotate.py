import lxml.etree as etree
import sys, math
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *
from collections import namedtuple
from BoardOperations.common import get_element_layer

def rotate_elements(elements, rot, origin=(0,0)):
   '''Rotates a list of elements by a rotation (angle+mirror) around an origin (by default 0,0)'''
   # very common case, no rotation
   if (rot.angle == 0 and rot.mirror is False):
      return elements
   
   for element in elements:
      if (element.tag == WIRE):
         rotate_xy_pair(element, rot, origin)
      elif (element.tag == POLYGON):
         rotate_polygon(element, rot, origin)
      elif (element.tag == CIRCLE):
         rotate_xy(element, rot, origin)
      elif (element.tag == RECTANGLE):
         rotate_xy_pair(element, rot, origin)
      elif (element.tag == HOLE):
         rotate_xy(element, rot, origin)
      elif (element.tag == VIA):
         rotate_xy(element, rot, origin)
      else:
         raise Exception("Unhandled element in 'move_elements'", etree.tostring(element, encoding='unicode'))

   return elements

def rotate_xy(element, rot, origin):
   '''Rotates an element defined by a single x,y coordinate. Includes mirroring, if needed'''
   x = float(element.attrib[X])
   y = float(element.attrib[Y])

   rx, ry = rotate((x,y),rot,origin)

   element.attrib[X] = str(rx)
   element.attrib[Y] = str(ry)

   if rot.mirror is True:
      mirror(element)

def rotate_xy_pair(element, rot, origin):
   '''Rotates an element defined by a pair of (x1,y1) and (x2,y2) coordinates. Includes mirroring, if needed'''
   x1 = float(element.attrib[X1])
   y1 = float(element.attrib[Y1])
   x2 = float(element.attrib[X2])
   y2 = float(element.attrib[Y2])

   rx1, ry1 = rotate((x1,y1),rot,origin)
   rx2, ry2 = rotate((x2,y2),rot,origin)

   element.attrib[X1] = str(rx1)
   element.attrib[Y1] = str(ry1)
   element.attrib[X2] = str(rx2)
   element.attrib[Y2] = str(ry2)

   if rot.mirror is True:
      mirror(element)

def rotate_polygon(ePoly, rot, origin):
   '''Rotates a polygon and its vertices, recursively'''
   # the polygon element itself is mirrored. Its child vertices are rotated
   if rot.mirror is True:
      mirror(ePoly)
   for eVertex in ePoly.xpath('vertex'):
      rotate_xy(eVertex, rot, origin)

def mirror (element):
   '''Mirrors a board element'''
   layer = get_element_layer(element)
   if (layer in MIRROR_LAYERS):
      opposite_layer = MIRROR_LAYERS[layer]
      element.set(LAYER, str(opposite_layer))

def rotate(point, rot, origin=(0,0)):
   ''' Rotates a point around an origin, using a rotation namedtuple (mirror+angle)'''
   ox,oy = origin
   px,py = point

   # if the rotation also includes mirroring, rotate CW
   angle = rot.angle if rot.mirror == False else 360-rot.angle
   radians = math.radians(angle)

   # rotate CCW
   rx = ox + math.cos(radians) * (px - ox) - math.sin(radians) * (py - oy)
   ry = oy + math.sin(radians) * (px - ox) + math.cos(radians) * (py - oy)

   # round the results, want to keep the number of decimals down
   rx = round(rx, ROUNDING_PRECISION)
   ry = round(ry, ROUNDING_PRECISION)

   return rx,ry

def read_rotation(element):
   '''Extracts the rotation of an element. Returns nametuple with 'mirror' (bool) and 'angle' (int) fields'''
   rotation = namedtuple('Rotation', ['mirror', 'angle'])
   rotation.mirror = False
   rotation.angle = int(0)

   tmp = element.get(ROTATION)
   if tmp is None:
      return rotation

   # haven't been able to determine what S does (looks like nothing)
   if ("S" in tmp):
      tmp = tmp.replace('S','')
   if ("M" in tmp):
      rotation.mirror = True
      tmp = tmp.replace('M', '')
   if ("R" in tmp):
      # 'R' simply indicates there's a rotation, but older eagle versions may not have it
      tmp = tmp.replace('R', '')
   # at this point, only the rotation angle remains (CCW, degrees)
   rotation.angle = int(tmp)

   return rotation