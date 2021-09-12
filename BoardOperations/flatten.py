import lxml.etree as etree
from sys import stdout
import os, math
import copy
from BoardOperations.constants import *
from BoardOperations import move, rotate, create, brdFile, common
from collections import namedtuple

def flatten_board(root):
   '''Flattens a board by folding all package elements into either the \<plain> or \<signals> elements'''
   libraries = get_all_library_packages(root)

   # first transform all packages into elements suitable for plain/signals
   for library in libraries:
      library_packages = libraries[library]
      for package in library_packages:
         filtered_package = filter_child_elements(library_packages[package])
         transformed_package = transform_package(filtered_package)
         library_packages[package] = transformed_package

   elements = get_all_elements(root) # Eagle elements = package placements
   for package_ref in elements:
      lib_name = package_ref[LIBRARY]
      package_name = package_ref[PACKAGE]
      refdes = package_ref[REFDES]

      # read the package definition
      if lib_name not in libraries:
         raise Exception("Library {} not defined".format(lib_name))
      if package_name not in libraries[lib_name]:
         raise Exception("Package {} referenced in {} not defined".format(package_name, lib_name))
      package_definition = libraries[lib_name][package_name]

      # manipulate and place the package definition
      duplicated_package = copy.deepcopy(package_definition)
      rotated_package = rotate_package(duplicated_package, package_ref[ROTATION])
      placed_package = place_package(rotated_package, package_ref[X], package_ref[Y])
      dispatch_elements(root, placed_package, refdes)

   return root

def get_all_library_packages(root):
   '''Reads all the libraries and packages in these libraries defined in the board'''
   result = {}
   libraries = root.findall(".//"+LIBRARY)
   for library in libraries:
      library_name = library.attrib['name']
      packages_dict = {}
      packages = library.findall(".//"+PACKAGE)
      for package in packages:
         package_name = package.attrib['name']
         if (package_name in packages_dict):
            raise Exception("Package {} already found".format(package_name), etree.tostring(package, encoding='unicode') )
         packages_dict[package_name] = package

      # it's possible a library declaration would be split into multiple <library> elems   
      if library_name in result:
         result[library_name].update(packages_dict)
      else:
         result[library_name] = packages_dict

   return result

def get_all_elements(root):
   '''Returns all package references (i.e. \<element>) found in the board definition'''
   result = []

   elements = root.findall('.//'+ELEMENT)
   for element in elements:
      element_data = {
         REFDES: element.attrib[NAME],
         LIBRARY: element.attrib[LIBRARY],
         PACKAGE: element.attrib[PACKAGE],
         X: float(element.attrib[X]),
         Y: float(element.attrib[Y]),
         ROTATION: rotate.read_rotation(element)
      }
      result.append(element_data)

   return result

def filter_child_elements(element):
   '''Filters out child elements from an XML node based on their tags (e.g. \<description>) or layer.'''
   tags_to_skip = [DESCRIPTION, TEXT, DIMENSION, CONTACTREF]

   for child in element:
      # filter by tag
      if (child.tag in tags_to_skip):
         child.getparent().remove(child)
         continue
      # filter by layer
      layer = common.get_element_layer(child)
      if (layer not in LAYERS_TO_KEEP):
         child.getparent().remove(child)
         continue

   return element

def transform_package(package):
   '''Transforms package elements (e.g. \<smd>, \<pad>) into non-package elements (e.g. \<rectangle>,\<via>,\<hole>)
      Assumes that all unwanted elements have been filtered out (e.g. \<description>,...)
   '''
   transformed_elements = []
   tags_to_duplicate = [WIRE, POLYGON, CIRCLE, VIA, HOLE]
   for element in package:
      new_elements = None

      if (element.tag in tags_to_duplicate):
         new_elements = [copy.deepcopy(element)]
      elif (element.tag == RECTANGLE):
         new_elements = transform_rectangle(element)
      elif (element.tag == SMD):
         new_elements = transform_smd(element)
      elif (element.tag == PAD):
         new_elements = transform_pad(element)
      else:
         raise Exception("Element {} not processed".format(element.tag), etree.tostring(element, encoding='unicode') )

      if new_elements is not None:
         transformed_elements.extend(new_elements)

   # make a copy of the package (if package used twice, there may be problems)
   duplicate = copy.deepcopy(package)
   # remove the original elements from the package
   for element in duplicate:
      duplicate.remove(element)
   for element in transformed_elements:
      duplicate.append(element)

   return duplicate

def transform_rectangle(rectangle):
   '''Transforms a rectangle from a package definition. If the rectangle has rotation, it's applied and 
   the rotation attribute is set to zero'''
   # for now, deepcopy, but it needs to be rotated if necessary
   rotation = rotate.read_rotation(rectangle)
   # some paranoia, so far have not seen a non-multiple of 90 degrees rotation
   if (rotation.angle % 90 != 0):
      raise Exception("Non-90 degrees rotation found {}".format(rectangle), etree.tostring(rectangle, encoding='unicode') )

   duplicate = copy.deepcopy(rectangle)
   duplicate.attrib.pop(ROTATION, None) # remove the rotation attribute
   
   # mirror if necessary
   if (rotation.mirror):
      rotate.mirror(duplicate)
   # if the rectangle is not rotated, nothing else to do
   if (rotation.angle == 0):
      return [duplicate]

   x1 = float(rectangle.attrib[X1])
   x2 = float(rectangle.attrib[X2])
   y1 = float(rectangle.attrib[Y1])
   y2 = float(rectangle.attrib[Y2])
   # compute center
   cx = (x1+x2)/2.0
   cy = (y1+y2)/2.0
   rx1,ry1 = rotate.rotate((x1,y1),rotation,(cx,cy))
   rx2,ry2 = rotate.rotate((x2,y2),rotation,(cx,cy))
   duplicate.set(X1, str(rx1))
   duplicate.set(Y1, str(ry1))
   duplicate.set(X2, str(rx2))
   duplicate.set(Y2, str(ry2))

   return [duplicate]

def transform_smd(element):
   '''Creates new elements based on an SMD element'''
   # compute info for the current SMD
   centerX = float(element.attrib[X])
   centerY = float(element.attrib[Y])
   dX = float(element.attrib[DX])
   dY = float(element.attrib[DY])
   rotation = rotate.read_rotation(element)
   roundness = 0 if ROUNDNESS not in element.attrib else float(element.attrib[ROUNDNESS])

   make_smd_circle = True if (roundness == 100 and dX==dY) else False

   layer = element.attrib[LAYER]
   # paranoia, just in case dX or dY are negative
   x1 = min(centerX-dX/2, centerX+dX/2)
   x2 = max(centerX-dX/2, centerX+dX/2)
   y1 = min(centerY-dY/2, centerY+dY/2)
   y2 = max(centerY-dY/2, centerY+dY/2)

   # create the metal rectangle
   if make_smd_circle:
      radius = dX/2.0
      width = dX
      smd = create.circle(centerX, centerY, width, radius, layer)
   else:
      smd = create.rectangle(x1,y1,x2,y2,layer)
   new_elements = [smd]

   if STOP not in element.attrib or element.attrib[STOP].lower()=="yes":
      # create the tStop rectangle
      tRectOffset = 0.1
      tStopLayer = "30" if layer=="16" else "29" # usually layer=="1"
      if make_smd_circle:
         radius = dX/2 + tRectOffset/2
         width = dX+tRectOffset
         tStop = create.circle(centerX, centerY, width, radius, tStopLayer)
      else:
         tStop = create.rectangle(x1-tRectOffset,y1-tRectOffset,
            x2+tRectOffset, y2+tRectOffset, tStopLayer)
      new_elements.append(tStop)
   
   # apply transform rectangle to each element
   rotate.rotate_elements(new_elements,rotation,(centerX,centerY))
   return new_elements

def transform_pad(element):
   '''Creates new elements based on an SMD element'''
   # compute info for the current SMD
   cX = float(element.attrib[X])
   cY = float(element.attrib[Y])
   drill = float(element.attrib[DRILL])
   diameter = float(element.attrib.get(DIAMETER,drill+0.5))
   shape = element.attrib.get(SHAPE, 'round')
   hasStop = (element.attrib.get(STOP,'yes').lower() == 'yes')
   rotation = rotate.read_rotation(element)

   new_elements = []
   if (shape == 'square'):
      x1 = cX-diameter/2.0
      x2 = cX+diameter/2.0
      y1 = cY-diameter/2.0
      y2 = cY+diameter/2.0
      layer = 1
      new_elements.append(create.rectangle(x1,y1,x2,y2,layer))
      if (hasStop):
         new_elements.append(create.rectangle(x1-0.1,y1-0.1,x2+0.1,y2+0.1,29))  # tStop rectangle
      new_elements.append(create.hole(cX,cY,drill))
   elif (shape == 'round'):
      new_elements.append(create.circle(cX,cY,diameter/2.0,diameter/4.0, 1))
      if hasStop:
         tStopDiameter = diameter+2*0.1
         new_elements.append(create.circle(cX,cY,tStopDiameter/2.0,tStopDiameter/4.0, 29))
      new_elements.append(create.hole(cX,cY,drill))
   elif (shape == 'octagon'):
      new_elements.append(create.via(cX,cY,drill,shape,hasStop))
   elif (shape == 'long'):
      new_elements.append(create.wire(cX-diameter/2,cY,cX+diameter/2,cY,diameter, 1))
      if hasStop:
         tStopDiameter = diameter+2*0.1
         new_elements.append(create.wire(cX-diameter/2,cY,cX+diameter/2,cY,tStopDiameter, 1))
      new_elements.append(create.hole(cX,cY,drill))
   elif (shape == 'offset'):
      new_elements.append(create.wire(cX,cY,cX+diameter+drill/2,cY,diameter, 1))
      if hasStop:
         tStopDiameter = diameter+2*0.1
         new_elements.append(create.wire(cX,cY,cX+diameter+drill/2,cY,tStopDiameter, 1))
      new_elements.append(create.hole(cX,cY,drill))
      
   # rotate newly created elements
   rotate.rotate_elements(new_elements, rotation, (cX,cY))
   return new_elements

def rotate_package(package, rot):
   '''Rotates a package around its (0,0) center'''
   rotate.rotate_elements(package, rot, (0,0))
   return package

def place_package(package, x, y):   
   '''Moves a package elements to the x,y location'''
   move.move_elements(package, x, y)
   return package

def should_append_element_to_signal(element):
   '''Determines whether an element should be part of a \<signal> or of \<plain>''' 
   layer = common.get_element_layer(element)
   if (layer != 1 and layer != 16):
      return False

   TAGS_FOR_SIGNALS = [WIRE, POLYGON]
   if (element.tag in TAGS_FOR_SIGNALS):
      return True

   return False

def dispatch_elements(root, placed_and_rotated_package, refdes):
   '''Copies the elements of a placed, rotated, and transformed package into the appropriate \<plain> or \<signals> elements'''
   plains = root.findall('.//drawing/board/plain')[0]
   plains = filter_child_elements(plains)
   signals = root.findall('.//drawing/board/signals')[0]
   for signal in signals:
      filter_child_elements(signal)

   new_signal = etree.Element(SIGNAL)
   new_signal.set(NAME, 'sig_'+refdes)

   for element in placed_and_rotated_package:
      if should_append_element_to_signal(element):
         new_signal.append(element)
      else:
         plains.append(element)

   if len(new_signal):
      signals.append(new_signal)

   return 

if __name__ == "__main__":
   CWD_FOLDER = os.path.dirname(__file__)
   DATA_FOLDER = os.path.realpath(os.path.join(CWD_FOLDER, "data") )

   # some test input file
   input_file_name = os.path.join(DATA_FOLDER, "scraped", "gatorBytes_Sensor_board_e6493c899cbd994f7a1e6d0865b944cb0ac004e2.brd")
   root = brdFile.read_board_root(input_file_name)

   # flatten the board
   root = flatten_board(root)

   # read the template and merge the flattened board into the template
   empty_ml_file = os.path.join(os.path.dirname(__file__), 'templates', 'ml_empty_board.brd')
   template = brdFile.read_board_root(empty_ml_file)
   root = brdFile.merge_board_into_template(template, root)

   # write the transformed template
   output_file = os.path.join(os.path.dirname(__file__), 'data', 'temp', 'gigi.brd')
   brdFile.write_board(root, output_file)

#   all_libraries = get_all_library_packages(root)
#   for library_name in all_libraries:
#      for package_name in all_libraries[library_name]:
#         transformed_package = transform_package(all_libraries[library_name][package_name])
#         mystr = etree.tostring(transformed_package, encoding='unicode')
#         print(mystr)
#         print("--------------------------")
