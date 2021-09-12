import lxml.etree as etree
import sys, os
from enum import Enum
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
from BoardOperations.constants import *
from collections import deque
from collections import namedtuple
from BoardTokenize.BaseBoardTokenizer import BaseBoardTokenizer

class TranslationPhase(Enum):
   Top = 1,      # elements outside <plain> and <signal>
   Plains = 2,   # elements inside <plain> (excluding <plain> itself)
   Signals = 3   # elements inside <signals> (excluding <signals> itself)

class CompactBoardTokenizer(BaseBoardTokenizer):
   # element tags and their encoding that can appear outside <plain> and <signals>
   _TOP_TAGS = {
      EAGLE: 'E',
      DRAWING: 'D',
      PLAIN: 'N',
      SIGNALS: 'G',
      BOARD: 'B'
   }

   # element tags and their encoding for elements that can only appear in the <plain> section
   _PLAINS_TAGS = {
      WIRE: 'W',
      CIRCLE: 'C',
      RECTANGLE: 'R',
      HOLE: 'H',
      POLYGON: 'P',
      VERTEX: 'X',
   }

   # element tags and their encoding for elements that can only appear in the <signals> section
   _SIGNALS_TAGS = {
      SIGNAL: 'S',
      WIRE: 'w',
      POLYGON: 'p',
      VERTEX: 'x',
      VIA: 'v'
   }

   _TAGS_TO_LEVELS = {
      VERTEX: 0,
      POLYGON: 1,
      WIRE: 1,
      RECTANGLE: 1,
      HOLE: 1,
      VIA: 1,
      CIRCLE: 1,
      SIGNAL: 2,
      SIGNALS: 3,
      PLAIN: 3,
      BOARD: 4,
      DRAWING: 5,
      EAGLE: 6
   }

   ###########################################################
   #### board to tokens translation
   ###########################################################

   def __init__(self, verbosity=0):
      super(CompactBoardTokenizer, self).__init__(verbosity)

   def _TokenizeElement(self, elem):
      return self.__TokenizeElementByPhase(elem, TranslationPhase.Top)

   def __TokenizeElementByPhase(self, elem, phase):
      tokens = []
      beginElemToken, newPhase = self.__getTokenForElement(elem, phase)
      tokens.append(beginElemToken)

      stringAttributes = self._TokenizeAttributes(elem)
      if stringAttributes:
         tokens.append(stringAttributes)

      # recurse on children elements
      for child in elem:
         tokens.append(self.__TokenizeElementByPhase(child, newPhase))

      stringResult = self._WORD_SEPARATOR.join(tokens)
      return stringResult

   def __getTokenForElement(self, elem, phase):
      tag = elem.tag
      token = None
      newPhase = phase
      if phase is TranslationPhase.Top:
         if tag in self._TOP_TAGS:
            token = self._TOP_TAGS[tag]
         if tag == PLAIN:
            newPhase = TranslationPhase.Plains
         elif tag == SIGNALS:
            newPhase = TranslationPhase.Signals
      elif phase is TranslationPhase.Plains:
         if tag in self._PLAINS_TAGS:
            token = self._PLAINS_TAGS[tag]
      elif phase is TranslationPhase.Signals:
         if tag in self._SIGNALS_TAGS:
            token = self._SIGNALS_TAGS[tag]

      if token is None:
         raise Exception("Tag {} is not legal for phase {}".format(tag, phase))

      return token, newPhase

   #####################################################
   #### Tokens to board translation
   #####################################################

   def TokenStringToBoard(self, tokenString):
      '''Translates an encoded string into an Eagle board'''
      root = etree.Element(EAGLE)
      if (self._END_OF_BOARD in tokenString):
         tokenString = tokenString.replace(self._END_OF_BOARD, '')

      tokens = tokenString.split(self._WORD_SEPARATOR)
      tokenStack = namedtuple('TokenStack', ['tokens', 'stack', 'idx'])
      tokenStack.tokens = tokens
      tokenStack.idx = 0
      self.__tokens_to_elements(root, tokenStack)

      return root

   def __tokens_to_elements(self, parent, ts):
      element_token = ts.tokens[ts.idx]
      ts.idx += 1

      tag = self.__TokenMapsToElementTag(element_token)
      if tag is None:
         raise Exception('unexpected token {} in context {}'.format(element_token, ' '.join(ts.tokens[ts.idx-2:ts.idx+2])))

      child = etree.SubElement(parent, tag)
      if (tag == SIGNAL):
         # add the name attribute
         child.attrib[NAME] = f'sig{self._signalIndex}'
         self._signalIndex += 1
      if self._verbosity > 0:
         print(f"Opening tag '{tag}' at position {ts.idx}")
      while True:
         # there's no 'end element' token, so if at the end, just pop and return
         if ts.idx >= len(ts.tokens):
            self._CleanElement(child)
            return

         crtToken = ts.tokens[ts.idx]
         tag = self.__TokenMapsToElementTag(crtToken)
         if tag is None:
            # the token did not map to an element tag, assuming attribute code
            self._DecodeAndAddAttributeToken(crtToken, child, ts.idx)
            ts.idx += 1
         else:
            # have to either dive recursively or return to above
            levelDifference = self.__GetLevelDifference(child.tag, tag)
            if levelDifference <= 0:
               self._CleanElement(child)
               return
            else:
               self.__tokens_to_elements(child, ts)

   def __GetLevelDifference(self, crtTag, nextTag):
      crtTagLevel = self._TAGS_TO_LEVELS[crtTag]
      nextTagLevel = self._TAGS_TO_LEVELS[nextTag]
      return crtTagLevel - nextTagLevel

   def __TokenMapsToElementTag(self, token):
      dict = self._PLAINS_TAGS
      tags = [tag for tag,code in dict.items() if code==token]
      if len(tags) > 0:
         return tags[0]
      
      dict = self._SIGNALS_TAGS
      tags = [tag for tag,code in dict.items() if code==token]
      if len(tags) > 0:
         return tags[0]

      dict = self._TOP_TAGS
      tags = [tag for tag,code in dict.items() if code==token]
      if len(tags) > 0:
         return tags[0]
      return None

   def _AddToVocab(self, vocab, crt_idx):
      start_idx = crt_idx
      for idx, val in enumerate(self._TOP_TAGS.values()):
         vocab[val] = start_idx+idx
      start_idx += len(self._TOP_TAGS)

      for idx, val in enumerate(self._PLAINS_TAGS.values()):
         vocab[val] = start_idx+idx
      start_idx += len(self._PLAINS_TAGS)

      for idx, val in enumerate(self._SIGNALS_TAGS.values()):
         vocab[val] = start_idx + idx
      start_idx += len(self._SIGNALS_TAGS)

      crt_idx = start_idx
      for idx, val in enumerate(self._ATTRIBUTES_TO_TOKENS.values()):
         vocab[val] = start_idx + idx
      start_idx += len(self._ATTRIBUTES_TO_TOKENS)

      for idx, val in enumerate(self._ATTRIBUTE_VALUES_TO_TOKENS.values()):
         vocab[val] = start_idx + idx





