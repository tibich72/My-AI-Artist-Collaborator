import lxml.etree as etree
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *

def move_elements(elements, offsetX, offsetY):
   '''Moves a list of elements by (offsetX,offsetY)'''
   for element in elements:
      if (element.tag == WIRE):
         move_xy_pair(element, offsetX, offsetY)
      elif (element.tag == POLYGON):
         move_polygon(element, offsetX, offsetY)
      elif (element.tag == CIRCLE):
         move_xy(element, offsetX, offsetY)
      elif (element.tag == RECTANGLE):
         move_xy_pair(element, offsetX, offsetY)
      elif (element.tag == HOLE):
         move_xy(element, offsetX, offsetY)
      elif (element.tag == VIA):
         move_xy(element, offsetX, offsetY)
      else:
         raise Exception("Unhandled element in 'move_elements'", etree.tostring(element, encoding='unicode'))

   return elements

def move_xy_pair(eWire, offsetX, offsetY):
   '''Moves an element (e.g. 'wire') whose position is defined by two pairs of coordinates (X1,Y1)(X2,Y2)'''
   add_to_attribute(eWire, X1, offsetX)
   add_to_attribute(eWire, Y1, offsetY)
   add_to_attribute(eWire, X2, offsetX)
   add_to_attribute(eWire, Y2, offsetY)

def move_polygon(ePoly, offsetX, offsetY):
   for eVertex in ePoly.xpath('vertex'):
      move_xy(eVertex, offsetX, offsetY)

def move_xy(element, offsetX, offsetY):
   '''Moves an element (e.g. 'circle', 'vertex') whose position is defined by one pair of X,Y coordinates'''
   add_to_attribute(element, X, offsetX)
   add_to_attribute(element, Y, offsetY)


def add_to_attribute(element, attribute, offset):
   if (attribute in element.attrib):
      crt_value = float(element.attrib[attribute])
      crt_value = round(crt_value+offset, ROUNDING_PRECISION)
      element.attrib[attribute] = str(crt_value)