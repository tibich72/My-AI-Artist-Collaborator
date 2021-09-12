import lxml.etree as etree
from sys import stdout
import copy, os, sys, pathlib

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from BoardOperations.constants import *
from BoardOperations import brdFile, flatten, cleanup

def read_board(file_name):
   '''Parses a board from file_name and returns its tree'''
   parser = etree.XMLParser(remove_blank_text=True)
   tree = etree.parse(file_name, parser=parser)
   return tree

def read_board_root(file_name):
   '''Parses a board from file_name and returns its root element.'''
   root = read_board(file_name).getroot()
   return root

def write_board(root, output_file):
   '''Writes a pretty formatted root board element to the output_file'''
   with open(output_file, 'w', encoding='utf-8') as f:
      mystr = etree.tostring(root, encoding='unicode', pretty_print=True)
      f.write(mystr)
      f.flush()

def read_utf8_file_to_string(file_name):
   '''Reads the contents of a file as an UTF-8 string'''
   stringValue = None
   with open(file_name, 'r', encoding='utf-8') as f:
      stringValue = f.read()

   return stringValue

def write_utf8_string_to_file(file_name, token_string):
   '''Writes a string to a file, UTF-8 encoded'''
   with open(file_name, 'w', encoding='utf-8') as f:
      f.write(token_string)
      f.flush()

def merge_plains_and_signals_into_template(template, plains, signals):
   '''Merges the \<plain> and \<signals> elements from a processed board into an empty template'''
   template = copy.deepcopy(template)
   # get the empty plains/signals from the template
   empty_plains = template.findall('.//drawing/board/plain')[0]
   empty_signals = template.findall('.//drawing/board/signals')[0]
   
   # replace the empty plains/signals in the template
   if plains is not None:
      empty_plains.getparent().replace(empty_plains, plains)
   if signals is not None:
      empty_signals.getparent().replace(empty_signals, signals)

   return template

def merge_board_into_template(template, board):
   '''Extracts the \<plain> and \<signals> elements from a processed board and merges them into an empty template'''
   # get the plains/signals from the board
   plains_elements = board.findall('.//drawing/board/plain')
   plains = None if len(plains_elements) == 0 else plains_elements[0]

   signals_elements = board.findall('.//drawing/board/signals')
   signals = None if len(signals_elements) == 0 else  signals_elements[0]

   return merge_plains_and_signals_into_template(template, plains, signals)

def getEagleBoardFromCondensed(root):
   '''Adds missing elements to a board (in case it's ML-generated) to make rendering work'''
   drawing = root.findall('.//drawing')[0]
   board = root.findall('.//drawing/board')[0]

   layers = root.findall('.//drawing/layers')
   if len(layers) == 0:
      layers = etree.SubElement(drawing, 'layers')
      empty_brd_template = os.path.join(pathlib.Path(__file__).parent.parent.absolute(), 'templates', 'empty_board.brd')
      empty_board_root = brdFile.read_board_root(empty_brd_template)
      template_layers = empty_board_root.findall('.//drawing/layers')[0]
      for layer in template_layers:
         new_layer = etree.SubElement(layers, LAYER)
         for attrib in layer.attrib:
            new_layer.attrib[attrib] = layer.attrib[attrib]

   libraries = root.findall('.//drawing/libraries')
   etree.SubElement(board, 'libraries') if len(libraries) == 0 else None
   elements = root.findall('.//drawing/elements')
   etree.SubElement(board, 'elements') if len(elements) == 0 else None

def getCondensedBoardFromEagle(root, flatten_board=False):
   '''Takes a full Eagle board and returns a condensed XML tree suitable for tokenizing'''
   # cleanup elements
   cleanup.cleanup_tags(root, PLAIN)
   cleanup.cleanup_tags(root, SIGNAL)

   if flatten_board:
      flatten.flatten_board(root)

   # construct the condensed ML-ready board from the empty template
   empty_ml_file = os.path.join(pathlib.Path(__file__).parent.parent.absolute(), 'templates', 'ml_empty_board.brd')
   template = brdFile.read_board_root(empty_ml_file)
   root = brdFile.merge_board_into_template(template, root)

   return root