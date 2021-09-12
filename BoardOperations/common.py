import lxml.etree as etree
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *


def get_element_layer(element):
   if LAYER in element.attrib:
      return int(element.attrib[LAYER])

   if element.tag == PAD:
      return 17
   if element.tag == HOLE:
      return 45
   if element.tag == VIA:
      return 18
   # vertices do not have layers (they belong to polygons, which do), return -1
   if element.tag == VERTEX:
      return -1

   raise Exception("Cannot determine layer of {}".format(element.tag), etree.tostring(element, encoding='unicode'))
