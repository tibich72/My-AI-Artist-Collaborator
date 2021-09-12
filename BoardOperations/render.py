import os, sys, uuid
import io
import lxml.etree as etree
import cairosvg
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from BoardOperations.constants import *
from BoardOperations import brdFile

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from eagle2svg.eagle_parser import Eagle
#from eagle2svg import eagle_parser

def convertCondensedBoardToSvgString(root):
   '''Converts a condensed board XML object into an SVG string'''
   brdFile.getEagleBoardFromCondensed(root)
   return convertEagleBoardToSvgString(root)   

def convertEagleBoardToSvgString(root):
   '''Converts a full Eagle board XML object into an SVG string'''
   tempFolder = os.environ['TEMP']
   fileName = os.path.join(tempFolder, str(uuid.uuid4())+".brd")

   brdFile.write_board(root, fileName)

   svgString = convertBrdFileToSvgString(fileName)

   os.remove(fileName)
   return svgString

def convertBrdFileToSvgString(file_name):
   '''Converts an Eagle board file into an SVG string'''
   eagleData = Eagle(file_name)
   sheet = 0
   layers = {x:True for x in LAYERS_TO_KEEP}

   old_stdout = sys.stdout
   sys.stdout = mystdout = io.StringIO()

   eagleData.render(sheet,layers)

   sys.stdout = old_stdout

   svgString = mystdout.getvalue()
   return svgString

def convertSvgStringToPng(svgString, output_png, use_cairo=False):
   '''Converts an SVG (string representation) into a PNG file'''
   if use_cairo:
      #stringArray = array.array('B', svgString)
      cairosvg.svg2png(bytestring=svgString, write_to=output_png, scale=3)
   else:   #imagemagick
      temp_svg_file = os.path.splitext(output_png)[0] + ".svg"
      with open(temp_svg_file, 'w') as f:
         f.write(svgString)
      cmd = f'"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\convert.exe" -density 400 {temp_svg_file} -scale 1000 {output_png}'
      subprocess.call(cmd, shell=False)
      os.remove(temp_svg_file)

if __name__ == "__main__":
   CWD_FOLDER = os.path.dirname(__file__)
   DATA_FOLDER = os.path.realpath(os.path.join(CWD_FOLDER, "..", "data") )

   # some test input file
   input_file_name = os.path.join(DATA_FOLDER, 'generated_boards', 'gen22_0.2_3.brd')
   root = brdFile.read_board_root(input_file_name)
   svgString = convertCondensedBoardToSvgString(root)

   output_svg_name = os.path.splitext(input_file_name)[0] + ".svg"
   with open(output_svg_name, 'w') as f:
      f.write(svgString)

   output_png_name = os.path.splitext(input_file_name)[0] + ".png"
   convertSvgStringToPng(svgString, output_png_name)
#   print(svgString)
