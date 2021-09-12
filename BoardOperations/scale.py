import lxml.etree as etree
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *

def scale_elements(elements, factor):
   ''' Scales a list of elements by 'factor'. Assumes the board has been aligned to origin (0,0) '''
   for element in elements:
      if (element.tag == WIRE):
         scale_wire(element, factor)
      elif (element.tag == POLYGON):
         scale_polygon(element, factor)
      elif (element.tag == CIRCLE):
         scale_circle(element, factor)
      elif (element.tag == RECTANGLE):
         scale_rectangle(element, factor)
      elif (element.tag == HOLE):
         scale_hole(element, factor)
      elif (element.tag == VIA):
         scale_via(element, factor)
      else:
         raise Exception("Unhandled element in 'ScaleElements'", etree.tostring(element, encoding='unicode'))

def scale_wire(eWire, factor):
   scale_attribute(eWire, X1, factor)
   scale_attribute(eWire, Y1, factor)
   scale_attribute(eWire, X2, factor)
   scale_attribute(eWire, Y2, factor)

   if (eWire.attrib[LAYER] != '20'):
      scale_attribute(eWire, WIDTH, factor)

def scale_polygon(ePoly, factor):
   scale_attribute(ePoly, WIDTH, factor)
   scale_attribute(ePoly, ISOLATE, factor)

   if (POUR in ePoly.attrib and ePoly.attrib[POUR]=='hatch'):
      if (SPACING not in ePoly.attrib):
         ePoly.set(SPACING, "1.27")
      scale_attribute(ePoly, SPACING, factor)

   for eVertex in ePoly.xpath('vertex'):
      scale_attribute(eVertex, X, factor)
      scale_attribute(eVertex, Y, factor)

def scale_circle(eCircle, factor):
   scale_attribute(eCircle, X, factor)
   scale_attribute(eCircle, Y, factor)
   scale_attribute(eCircle, RADIUS, factor)
   scale_attribute(eCircle, WIDTH, factor)

def scale_rectangle(eRect, factor):
   scale_attribute(eRect, X1, factor)
   scale_attribute(eRect, X2, factor)
   scale_attribute(eRect, Y1, factor)
   scale_attribute(eRect, Y2, factor)

def scale_hole(eHole, factor):
   scale_attribute(eHole, X, factor)
   scale_attribute(eHole, Y, factor)
   scale_attribute(eHole, DRILL, factor)

def scale_via(eVia, factor):
   scale_attribute(eVia, X, factor)
   scale_attribute(eVia, Y, factor)
   scale_attribute(eVia, DRILL, factor)

def scale_attribute(element, attribute, factor):
   if (attribute in element.attrib):
      crt_value = float(element.attrib[attribute])
      scaled_value = round(crt_value*factor, ROUNDING_PRECISION)
      element.attrib[attribute] = str(scaled_value)
