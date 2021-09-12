import lxml.etree as etree
import sys, os
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *
from collections import deque
from collections import namedtuple
from BoardTokenize.BaseBoardTokenizer import BaseBoardTokenizer

class TreeBoardTokenizer(BaseBoardTokenizer):
   _TAGS_TO_TOKENS = {
      WIRE:      ('W', 'w'),
      CIRCLE:    ('C', 'c'),
      POLYGON:   ('P', 'p'),
      RECTANGLE: ('R', 'r'),
      HOLE:      ('H', 'h'),
      VIA:       ('V', 'v'),
      SIGNAL:    ('S', 's'),
      VERTEX:    ('X', 'x'),
      EAGLE:     ('E', 'e'),
      DRAWING:   ('D', 'd'),
      PLAIN:     ('N', 'n'),
      SIGNALS:   ('G', 'g'),
      BOARD:     ('B', 'b')
   }
   
   ###############################################################################
   #####  board to tokens translation
   ###############################################################################

   def __init__(self, verbosity=0):
      super(TreeBoardTokenizer, self).__init__(verbosity)
   
   def _TokenizeElement(self, elem):
      '''Transforms an XML element into tokens'''
      tokens = []
      beginToken,endToken = self._TAGS_TO_TOKENS[elem.tag]
      tokens.append(beginToken)
      
      # append attributes only if not empty
      stringAttributes = self._TokenizeAttributes(elem)
      if stringAttributes:
         tokens.append(stringAttributes)
      
      #recurse on children elements
      for child in elem:
         tokens.append(self._TokenizeElement(child))

      tokens.append(endToken)

      stringResult = self._WORD_SEPARATOR.join(tokens)
      return stringResult

   ###############################################################################
   #####  tokens to board translation
   ###############################################################################

   def TokenStringToBoard(self, tokenString):
      '''Translates a string consisting of tokens into a board'''
      root = etree.Element(EAGLE)
      if (self._END_OF_BOARD in tokenString):
         tokenString = tokenString.replace(self._END_OF_BOARD, '')
      tokens = tokenString.split(self._WORD_SEPARATOR)

      tokenStack = namedtuple('TokenStack', ['tokens', 'stack', 'idx'])
      tokenStack.stack = deque()
      tokenStack.tokens = tokens
      tokenStack.idx = 0
      self.__tokens_to_elements(root,tokenStack)

      if len(tokenStack.stack) != 0:
         raise Exception("Unclosed elements {}".format(tokenStack.stack))

      return root

   def __tokens_to_elements(self, parent, ts):
      '''Translates recursively a list of tokens into an element'''

      # get element at idx
      element_token = ts.tokens[ts.idx]
      ts.idx+=1
      tag, startToken, endToken = self.__starts_element(element_token)
      if tag is None:
         raise Exception("Unrecognized token {} at index {}".format(element_token, ts.idx))

      ts.stack.append(startToken)
      child = etree.SubElement(parent, tag)
      if (tag == SIGNAL):
         # add the name attribute
         child.attrib[NAME] = f'sig{self._signalIndex}'
         self._signalIndex += 1
      while True:
         if ts.idx >= len(ts.tokens):
            raise Exception("Badly formatted string, unclosed element {}".format(ts.stack.pop()))

         crtToken = ts.tokens[ts.idx]

         # check if element is being closed
         if crtToken == endToken:
            ts.idx += 1
            ts.stack.pop()
            self._CleanElement(child)
            return

         # check if start of a new element
         childTag, _, _ = self.__starts_element(crtToken)
         if childTag is not None:
            self.__tokens_to_elements(child, ts)
            continue

         self._DecodeAndAddAttributeToken(crtToken, child, ts.idx)

         ts.idx += 1

   def __starts_element(self, token):
      for tag in self._TAGS_TO_TOKENS:
         if token == self._TAGS_TO_TOKENS[tag][0]:
            return tag, self._TAGS_TO_TOKENS[tag][0], self._TAGS_TO_TOKENS[tag][1]
      return None, None, None

   ###############################################################################
   #####  special functions
   ###############################################################################
   def _AddToVocab(self, vocab, crt_idx):
      for vals in self._TAGS_TO_TOKENS.values():
         vocab[vals[0]] = crt_idx
         crt_idx+=1
         vocab[vals[1]] = crt_idx
         crt_idx+=1
      for val in self._ATTRIBUTES_TO_TOKENS.values():
         vocab[val] = crt_idx
         crt_idx+=1
      for val in self._ATTRIBUTE_VALUES_TO_TOKENS.values():
         vocab[val] = crt_idx
         crt_idx+=1

if __name__ == "__main__":
   tk = TreeBoardTokenizer()
   assert(tk is not None)
