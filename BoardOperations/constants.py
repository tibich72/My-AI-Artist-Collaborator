# attributes of interest
X1 =        'x1'
Y1 =        'y1'
X2 =        'x2'
Y2 =        'y2'
X =         'x'
Y =         'y'
DX =        'dx'
DY =        'dy'
RADIUS =    'radius'
DRILL =     'drill'
LAYER =     'layer'
WIDTH =     'width'
ISOLATE =   'isolate'
SPACING =   'spacing'
ROTATION =  'rot'
POUR =      'pour'
STOP =      'stop'
NAME =      'name'
ROUNDNESS = 'roundness'
CAP =       'cap'
CURVE =     'curve'
STYLE =     'style'
EXTENT =    'extent'
RANK =      'rank'

# element tags of interest
WIRE =        'wire'
POLYGON =     'polygon'
VERTEX =      'vertex'
CIRCLE =      'circle'
RECTANGLE =   'rectangle'
HOLE =        'hole'
VIA =         'via'
PACKAGE =     'package'
SMD =         'smd'
PAD =         'pad'
TEXT =        'text'
DIMENSION =   'dimension'
CONTACTREF =  'contactref'
ELEMENT =     'element'
DESCRIPTION = 'description'
LIBRARY =     'library'
DIAMETER =    'diameter'
SHAPE =       'shape'
SIGNAL =      'signal'
SIGNALS =     'signals'
EAGLE =       'eagle'
PLAIN =       'plain'
DRAWING =     'drawing'
BOARD =       'board'

# not Eagle keywords
REFDES = 'refdes'

# layers to keep, element on all other layers are eliminated
# add 51, 52 if silkscreen layers desired
LAYERS_TO_KEEP = [
   1,  # Top
   16, # Bottom
   17, # Pads
   18, # Vias
   20, # Dimension
   29, # tStop
   30, # bStop
   44, # Drill
   45, # Hole
   46  # Milling
]

# dictionary for layers and their mirrors. If a layer is not in, it is not mirrored
MIRROR_LAYERS = {
   1: 16,
   16: 1,
   29: 30,
   30: 29,
   51: 52,
   52: 51
}

# how many digits to round results to
ROUNDING_PRECISION = 3