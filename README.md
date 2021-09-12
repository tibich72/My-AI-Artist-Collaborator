# My-AI-Artist-Collaborator

The source files for an AI Eagle board generator. The ML model is trained on a dataset created from my ["PCB Drawings"](https://tibichelcea.net/pcb-drawings) works.

## Requirements
The code was run on a Windows machine, with Tensorflow 2.3.0, CUDA 10.1, and numpy 1.19.3. Tensorflow > 2.3 and numpy > 1.19.x does not seem to work (there is a defect in initializing LSTM layers in Keras), but perhaps that's because I'm using a fairly old CUDA version.

Other requirements:
* [Imagemagick 7.1.0](https://imagemagick.org/index.php) (its binaries should be on the system PATH)
* [Eagle2svg](https://github.com/at-wat/eagle2svg) 0.1.4 (the only python package I could find that translates Eagle boards into SVG files). This repo includes a clone of _eagle2svg_ with some fixes, as, unfortunately, work on _eagle2svg_ has stopped a few years back.
* [textgenrnn](https://github.com/minimaxir/textgenrnn) for AI training and text generation. This repo includes a clone of that project with a small fix in initializing the model with a vocabulary that is not a subset of the default _textgenrnn_ vocabulary.
* [Eagle CAD](https://www.autodesk.com/products/eagle/overview) in case you want to edit the generated boards (Autodesk offers a free version with some limitations)

Even though I've tried to make the code platform independent, the code has not been run on Linux/Mac platforms, so it comes as is.

## Usage

To run the Flask server, open a terminal, change to the _Web_ folder an type:
```shell
set FLASK_APP=pcb_main
flask run
```

Then open a browser at http://127.0.0.1:5000/ to see the app.

The app has two modes:
1. Generate boards:
![Generate](/images/generate_boards.png)
Simply click on "Generate New Board". It takes some time to generate a new board. When done, an image of the Eagle board image is displayed below:
![Generated Image](/images/img_generated_board.png)
If you are satisfied with the generated board, simply click the image and an Eagle CAD .brd file will be downloaded to your computer.
2. Suggest completion for a partial board:
![Suggest completion](/images/suggest_completion.png)
To use this mode, simply drag-and-drop the partial Eagle file in the "Drop Eagle file here" area and wait for a board to be generated.
![Suggested image](/images/img_suggested_board.png)
If you don't like the suggested completion, press "New Suggestion" button to generate a new board based on the same partial one. If you are satisfied with the result, simply click the image and an Eagle CAD .brd file will be downloaded to your computer.

