import lxml.etree as etree
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *
from collections import deque
from collections import namedtuple
from shapely.geometry import *
from shapely.validation import explain_validity
from shapely.ops import polygonize, unary_union


class BaseBoardTokenizer:
   # token for the end of the board string
   _END_OF_BOARD = '|'
   # word separator string
   _WORD_SEPARATOR = ' '
   # default values for various attributes. 
   # A None value means the attribute must exist (exception will be thrown if attribute missing)
   _DEFAULT_ATTRIBUTE_VALUES = {
      WIRE: {X1:None, Y1:None, X2:None, Y2:None, WIDTH:None, LAYER:None, STYLE:'continuous',CURVE:'0',CAP:'round'},
      CIRCLE: {X:None, Y:None, RADIUS:None, WIDTH:None, LAYER:None},
      RECTANGLE: {X1:None, Y1:None, X2:None, Y2:None, LAYER:None, ROTATION:'R0'},
      HOLE: {X:None, Y:None, DRILL:None},
      VIA: {X:None, Y:None, DRILL:None, EXTENT:None, DIAMETER:'0', SHAPE:'round'},
      POLYGON: {WIDTH: None, LAYER:None, SPACING:'0', POUR: 'solid', RANK:'1', ISOLATE:'0'},
      VERTEX: {X:None, Y:None, CURVE:'0'},
      BOARD: {},
      DRAWING: {},
      EAGLE: {},
      PLAIN: {},
      SIGNALS: {},
      SIGNAL: {}
   }
   # what attributes should be excluded from the output
   _ATTRIBUTES_TO_SKIP = {
      'orphans',    # in conductive polygons
      'thermals',   # in conductive polygons
      'alwaysstop', # in vias
      NAME,         # should show only in signals
      'class'       # in signals
   }

   # attributes encodings
   _ATTRIBUTES_TO_TOKENS = {
      X:       'Ӿ',
      X1:      'Ẋ',
      X2:      'Ẍ',
      Y:       'Ұ',
      Y1:      'Ẏ',
      Y2:      'Ῡ',
      WIDTH:   'Ẁ',
      DRILL:   'Ḓ',
      DIAMETER:'Ɵ',
      CURVE:   'Ḉ',
      CAP:     'Ո',  # U+0548
      SPACING: 'Ṧ',
      STYLE:   'Ϫ',
      SHAPE:   '§',
      ISOLATE: 'ḹ',
      POUR:    'Ṕ',
      RADIUS:  '₨',
      ROTATION:'Ṝ',
      RANK:    '₭',
      LAYER:   'Ḽ',
      EXTENT:  '↔'   # U+2194
   }

   # common, non-numeric, attribute values and their encoding
   _ATTRIBUTE_VALUES_TO_TOKENS = {
      'round': '○',
      'flat': '╥',
      'continuous': 'ↄ',
      'longdash': '―',  # U+2015
      'shortdash': '⁞', # U+205E
      'dashdot': '…',   # U+2026
      'square': '□',    # U+25A1
      'octagon': '◊',
      'solid': '⌂',     # U+2302
      'hatch': '╬',
      'cutout': 'Ø',
      'no': '№',
      'yes': '√'
   }


   def __init__(self, verbosity=0):
      # so far, do nothing, added just in case
      self.__tokenizer = ""
      self._verbosity = verbosity
      self._signalIndex = 0

   def BoardToTokenString(self, root):
      '''Returns the token string of an entire board'''
      top_elem = root[0]
      stringResult = self._TokenizeElement(top_elem) + self._END_OF_BOARD
      return stringResult

   def _TokenizeElement(self, elem):
      raise NotImplementedError()

   def _TokenizeAttributes(self, elem):
      '''Tokenizes all attributes of an element (with defaults, when necessary)'''
      attribute_defaults = self._DEFAULT_ATTRIBUTE_VALUES[elem.tag]
      attribute_values = []
      for attr in attribute_defaults:
         attrToken = self._ATTRIBUTES_TO_TOKENS[attr]
         value = self.__GetAttributeValueOrDefault(elem,attr)
         if value is None:
            continue
         valueTokens = self._ATTRIBUTE_VALUES_TO_TOKENS.get(value, value)
         attribute_values.append(attrToken+valueTokens)

      stringResult = self._WORD_SEPARATOR.join(attribute_values)
      return stringResult

   def __GetAttributeValueOrDefault(self, elem, attribute_name):
      '''Returns the value of the attribute or its default value. None is returned when the attribute must be skipped

      If attribute must exist and is not present, an exception is thrown'''
      if attribute_name in self._ATTRIBUTES_TO_SKIP:
         return None

      if attribute_name in elem.attrib:
         return elem.attrib[attribute_name]

      attribute_defaults = self._DEFAULT_ATTRIBUTE_VALUES[elem.tag]
      attribute_value = attribute_defaults[attribute_name]
      if attribute_value is None:
         raise Exception("Element {} missing required attribute {}".format(elem.tag,attribute_name), 
            etree.tostring(elem, encoding='unicode'))

      return attribute_value

   def TokenStringToBoard(self, tokenString):
      raise NotImplementedError("TokenStringToBoard")

   def _DecodeAndAddAttributeToken(self, token, elem, idx):
      '''Decodes an attribute token and adds the attribute to the XML element'''
      tokensToAttributeNames = {v: k for k,v in self._ATTRIBUTES_TO_TOKENS.items()}
      attributeValuesToValues = {v: k for k,v in self._ATTRIBUTE_VALUES_TO_TOKENS.items()}
      if token[0] not in tokensToAttributeNames:
         raise Exception(f"Unrecognized attribute {token} at index {idx} in element {elem.tag}")
      attributeName = tokensToAttributeNames[token[0]]
      value = token[1:]
      if (value in attributeValuesToValues):
         value = attributeValuesToValues[value]
      elem.attrib[attributeName] = value

   def GenerateTextgenrnnVocab(self):
      vocab = {
         "0":2, "1":3, "2":4,
         "3":5, "4":6, "5":7,
         "6":8, "7":9, "8":10,
         "9":11, ".":12, "-":13
      }
      if (self._END_OF_BOARD != ''):
         vocab[self._END_OF_BOARD] = 14
      if (self._WORD_SEPARATOR != ''):
         vocab[self._WORD_SEPARATOR] = 1

      self._AddToVocab(vocab, 15)

      return vocab

   def _AddToVocab(self, vocab, crt_idx):
      raise NotImplementedError()

   def _CleanElement(self, element):
      if element.tag == SIGNAL:
         self.FixPolygons(element)

      if element.tag == POLYGON:
         if RANK not in element.attrib or element.attrib[RANK] == "0":
            element.attrib[RANK] = "1"

   ######### Polygon fixes ##################
   def FixPolygons(self, signalElem):
      # transform all signal polygons into Shapely polygons
      polys = signalElem.findall(".//"+POLYGON)
      for polyElem in polys:
         self.__FixPolygon(signalElem, polyElem)

   def __FixPolygon(self, signalElem, polyElem):
      assert(polyElem.tag == POLYGON)
      childPolygon = self.__PolyElementToPolygon(polyElem)

      if childPolygon is None:
         polyElem.getparent().remove(polyElem)
         return

      newPolygons = []
      if childPolygon.is_valid:
         # use simplify to eliminate duplicate points
         newPolygons.append(childPolygon.simplify(0, False))
      else:
         # fix it, it may result in multiple polygons
         smth = explain_validity(childPolygon)
         coords = childPolygon.exterior.coords
         lineString = LineString(coords[:]+coords[0:0])
         multiLineString = unary_union(lineString)
         # polygons with only collinear vertices will be eliminated by polygonize
         # polygonize also eliminates duplicated vertices
         newPolygons.extend(list(polygonize(multiLineString)))

      for poly in newPolygons:
         self.__AddFixedPolygon(signalElem, polyElem, poly)

      # remove the original polygon
      polyElem.getparent().remove(polyElem)

   def __PolyElementToPolygon(self, polyElem):
      assert(polyElem.tag == POLYGON)
      vertices = []
      for vertexElem in polyElem:
         x = float(vertexElem.attrib[X])
         y = float(vertexElem.attrib[Y])
         vertices.append((x,y))

      # polygons must have at least 3 vertices
      if len(vertices) < 3:
         return None

      polygon = Polygon(vertices)
      return polygon

   def __AddFixedPolygon(self, signalElem, originalPolyElem, poly):
      childElem = etree.SubElement(signalElem, POLYGON)
      # copy the original attributes of the polygon
      for attribName in originalPolyElem.attrib:
         childElem.attrib[attribName] = originalPolyElem.attrib[attribName]

      for point in poly.exterior.coords:
         vertexElem = etree.SubElement(childElem, VERTEX)
         vertexElem.attrib[X] = str(point[0])
         vertexElem.attrib[Y] = str(point[1])

