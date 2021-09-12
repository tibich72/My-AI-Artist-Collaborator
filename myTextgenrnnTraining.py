from Textgenrnn.model import config
from Textgenrnn import textgenrnn
import pathlib
import os
import numpy as np
import json

do_training = True
encoder = 'eagleCompact'
epochs = 30
META_TOKEN = '|'

this_dir = os.path.abspath(os.path.dirname(__file__))
dataset_dir = os.path.join(this_dir, 'data', 'textgenrnn_dataset')
vocab_file = os.path.join(this_dir, 'Textgenrnn', f'{encoder}_vocab.json')
config_file = os.path.join(this_dir, 'Textgenrnn', 'eagle_config.json')

biSuffix = None
rnn_size = None
with open(config_file, 'r', encoding='utf-8', errors='ignore') as json_file:
   config = json.load(json_file)
   rnn_size = config['rnn_size']
   biSuffix = "bi" if config['rnn_bidirectional'] == True else ""
assert(rnn_size is not None)
assert(biSuffix is not None)

modelName = f'{encoder}{rnn_size}{biSuffix}'
print('############################################')
print("Model name", modelName)
print('############################################')
weights_file = os.path.join(this_dir, 'models', f'{modelName}_{epochs}.h5')

def saveConfigForGeneration(currentConfigFile, modelName):
   with open(config_file, 'r', encoding='utf-8', errors='ignore') as json_file:
      config = json.load(json_file)
   output_config = os.path.join(this_dir, 'textgenrnn', f'{modelName}_config.json')
   with open(output_config, 'w', encoding='utf-8') as json_file:
      json_file.write(json.dumps(config, indent=3)) 

def generate_strings(textgen, num_samples, temperature, max_gen_length=10000):
   print('####################','\n','Temperature=',temperature,'\n####################')
   if not isinstance(temperature, list):
      temperature = [temperature]

   temperatureSuffix = '_'.join(str(x) for x in temperature)  
   outfile = os.path.join(this_dir, 'outputs', f'{modelName}_gen{epochs}_{temperatureSuffix}.txt')
   textgen.generate_to_file(outfile, 
                            n=num_samples, 
                            max_gen_length=max_gen_length, 
                            temperature=temperature)


if do_training:
   saveConfigForGeneration(config_file, modelName)
   textgen = textgenrnn(
      #weights_path='textgenrnn\\eagleCompact_weights.hdf5',
      name=modelName,
      vocab_path=vocab_file,
      config_path=config_file,
      weights_path="Skip"
      )
   textgen.META_TOKEN = META_TOKEN
   textgen.train_from_file(
      os.path.join(dataset_dir, f'{encoder}.txt'), 
      header=False,
      num_epochs=epochs, 
      batch_size=256, 
      gen_epochs = 0,
      save_epochs=1)
   textgen.save(weights_path=weights_file)
else:
   config_file = os.path.join(this_dir, 'textgenrnn', f'{modelName}_config.json')
   #weights_file = 'textgenrnn_weights_epoch_9.hdf5'
   textgen = textgenrnn(
      name=modelName,
      weights_path=weights_file, 
      config_path=config_file,
      vocab_path=vocab_file)
   textgen.META_TOKEN = META_TOKEN
   
   generate_strings(textgen, 1, 0.3, max_gen_length=2000)
