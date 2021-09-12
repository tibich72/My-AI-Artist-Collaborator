import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *

TAGS_TO_REMOVE = {
   PLAIN: [TEXT, DIMENSION],
   SIGNAL: [CONTACTREF],
   PACKAGE: [TEXT, DESCRIPTION, DIMENSION]
}

ATTRIBUTE_DEFAULTS = {
   WIRE: {'curve':'0', 'style': 'continuous', 'cap': 'round'},
   VIA: {'shape': 'round'},
   POLYGON: {'pour': 'solid', 'rank': '1', 'spacing': '1.27', 'isolate': '0'}
}

def cleanup_tags(element, category):
   '''Removes all child elements that are not needed from a category (e.g. signals, plain)'''
   tags_to_remove = TAGS_TO_REMOVE[category]
   for tag in tags_to_remove:
      regex = './/{}/{}'.format(category,tag)
      elements = element.findall(regex)
      for elem in elements:
         elem.getparent().remove(elem)

def add_default_attributes(root):
   '''Adds defaults to elements, as defined in ATTRIBUTE_DEFAULTS'''
   for tag in ATTRIBUTE_DEFAULTS:
      expr = './/{}'.format(tag)
      for element in root.findall(expr):
         for attr in ATTRIBUTE_DEFAULTS[tag]:
            if (attr not in element.attrib):
               element.set(attr, ATTRIBUTE_DEFAULTS[tag][attr])