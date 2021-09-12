from flask import Flask, render_template
from flask import request, jsonify, Response
import uuid
import os
import sys
import uuid
import os, json
import random

from flask.globals import current_app
from flask.helpers import send_from_directory

#import my libs
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from BoardOperations import render, brdFile
from BoardTokenize.CompactBoardTokenizer import CompactBoardTokenizer
from BoardTokenize.TreeBoardTokenizer import TreeBoardTokenizer
from Textgenrnn import textgenrnn

app = Flask(__name__)

# load the ML model
TEMP_FILES_FOLDER = "static/files"

@app.route("/")
def main_page():
   return render_template('main.html')

@app.route("/sendfile", methods=["POST"])
def send_file():
   fileob = request.files["file2upload"]
   guid = uuid.uuid4()
   filename = f"{str(guid)}_{fileob.filename}"
   save_path = f"{TEMP_FILES_FOLDER}/{filename}"
   fileob.save(save_path)

   response = {'path': filename}
   return jsonify(response)

@app.route("/renderboard", methods=["POST"])
def render_board_file():
   jsonData = request.get_json()
   fileName = jsonData['fileName']
   print("Filename:", fileName)
   base = os.path.splitext(fileName)[0]
   output_png = os.path.join(TEMP_FILES_FOLDER, base+".png")

   try:
      root = brdFile.read_board_root(os.path.join(TEMP_FILES_FOLDER, fileName))
      svgString = render.convertCondensedBoardToSvgString(root)
      render.convertSvgStringToPng(svgString, output_png)
   except:
      return Response("Error in rendering the generated board", status=500, mimetype='text/plain')

   response = {'path': output_png}
   return jsonify(response)

@app.route("/generateboard", methods=["GET"])
def generate_board_file():
   try:
      board_file = generate_board()
   except:
      return Response("Error in generating a board", status=500, mimetype='text/plain')   

   response = {'path': board_file}
   return jsonify(response)

@app.route("/completeboard", methods=["POST"])
def suggest_board_completion():
   jsonData = request.get_json()
   fileName = jsonData['fileName']
   print("Filename:", fileName)

   board_root = brdFile.read_board_root(os.path.join(TEMP_FILES_FOLDER, fileName))
   board_root = brdFile.getCondensedBoardFromEagle(board_root, flatten_board=True)
   
   tokenizer = TreeBoardTokenizer()
   prefix_tokens = tokenizer.BoardToTokenString(board_root)

   try:
      board_file = generate_board(prefix=prefix_tokens)
   except:
      return Response("Error in completing the suggested board", status=500, mimetype='text/plain')
   response = {'path': board_file}
   return jsonify(response)

@app.route("/downloadfile", methods=["POST"])
def download_file():
   bytesData = request.get_data()   
   my_json = bytesData.decode('utf8').replace("'", '"')
   jsonData = json.loads(my_json)
   fileName = jsonData['fileName']

   fileFolder = os.path.join(current_app.root_path, TEMP_FILES_FOLDER)
   return send_from_directory(directory=fileFolder, filename=fileName, as_attachment=True)

############################################################################
############### ML Model operations
############################################################################

# the actual object that will do the completion
textgen = None

def init_ml_model():
   global textgen
   print("\n\n creating object \n\n")
   parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
   textgenrnn_folder = os.path.join(parent_folder, "Textgenrnn")
   config_file = os.path.join(textgenrnn_folder, "eagleCompact128bi_config.json")
   vocab_file = os.path.join(textgenrnn_folder, 'eagleCompact_vocab.json')
   weights_file = os.path.join(parent_folder, "models", "eagleCompact128bi_30.h5")

   textgen = textgenrnn(name="eagleCompact128bi",
                        weights_path=weights_file,
                        config_path=config_file,
                        vocab_path=vocab_file)
   textgen.META_TOKEN = '|'
   
def generate_board(prefix=None):
   global textgen
   # lazy initialization TODO: figure out how to initialize when server starts
   if textgen is None:
      init_ml_model()

   if prefix is None:
      # encoding for the beginning of each board's XML <drawing> <board> <plain> ... </plain> ... </board> </drawing>
      prefix = 'D B N '   

   guid = uuid.uuid4()
   tokens_file_name = f"{str(guid)}.tokens"
   board_file_name = os.path.splitext(tokens_file_name)[0]+".brd"
   tokens_file_path = os.path.join(TEMP_FILES_FOLDER, tokens_file_name)
   board_file_path = os.path.join(TEMP_FILES_FOLDER, board_file_name)

   # TODO: this should be a parameter sent from the UI, for now random in the interval (0.25, 0.35).
   #       at higher temperatures, the chances of an incorrect board increase
   random_temperature = 0.25 + random.random()
   temperature = [random_temperature]

   # TODO: how many tokens to generate (unless '|' is generated) should be sent from the UI too
   max_length = 1500

   textgen.generate_to_file(tokens_file_path, n=1, max_gen_length=max_length, temperature=temperature, prefix=prefix)

   # decode the generated string
   tokenizer = CompactBoardTokenizer()
   with open(tokens_file_path, 'r', encoding='utf-8') as tf:
      token_string = tf.read()
   board_root_elem = tokenizer.TokenStringToBoard(token_string)
   brdFile.getEagleBoardFromCondensed(board_root_elem)
   brdFile.write_board(board_root_elem, board_file_path)

   # TODO: automatically cleanup the temp folder every now and then to free up space

   return board_file_name