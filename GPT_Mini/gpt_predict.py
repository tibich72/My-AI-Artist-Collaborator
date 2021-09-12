
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
import numpy as np
from keras.models import load_model
import os.path
import re
import string
import random

from gpt_dataset import read_dataset

class GptTextGenerator():
   """A class to generate circuit boards using a pre-trained GPT Mini model"""
   # the default maximum numbers of tokens to generate
   DEFAULT_MAX_TOKENS = 10000

   def __init__(self, model_name, dataset_folders = ["../data/dataset"]):
      # load the model first
      model_path = os.path.join(os.path.dirname(__file__), "..", "models")
      model_path = os.path.join(model_path, model_name)
      self.model = load_model(model_path)
      self.maxlen = self.model.get_layer(name="InputLayer").output_shape[0][1]

      # load the vocabulary
      dataset_folders = [os.path.abspath(os.path.join(os.path.dirname(__file__), _)) for _ in dataset_folders]
      self.vocab, _ = read_dataset(dataset_folders, self.maxlen)

      # some internal variables
      self.max_tokens = 10000
      self.top_k = 5

   def map_vocabulary_to_index(self, vocab):
      word_to_index = {}
      for index, word in enumerate(self.vocab):
         word_to_index[word] = index
      return word_to_index

   def sample_from(self, logits):
      top_k = 5  # how many possibilities to generate
      logits, indices = tf.math.top_k(logits, k=self.top_k, sorted=True)
      indices = np.asarray(indices).astype("int32")
      preds = keras.activations.softmax(tf.expand_dims(logits, 0))[0]
      preds = np.asarray(preds).astype("float32")
      return np.random.choice(indices, p=preds)

   def generate(self, start_prompt, max_tokens_to_generate=None, termination_token = "|"):
      max_tokens = max_tokens_to_generate if max_tokens_to_generate is not None else self.DEFAULT_MAX_TOKENS
      print(max_tokens)
      word_to_index = self.map_vocabulary_to_index(self.vocab)
      start_tokens = [word_to_index.get(_, 1) for _ in list(start_prompt)]

      num_tokens_generated = 0
      tokens_generated = []

      while num_tokens_generated <= max_tokens:
         pad_len = self.maxlen - len(start_tokens)
         sample_index = len(start_tokens) - 1
         if pad_len < 0:
            x = start_tokens[:self.maxlen]
            sample_index = self.maxlen - 1
         elif pad_len > 0:
            x = start_tokens + [0] * pad_len
         else:
            x = start_tokens
         x = np.array([x])
         y, _ = self.model.predict(x)
         sample_token = self.sample_from(y[0][sample_index])
         tokens_generated.append(sample_token)
         start_tokens.append(sample_token)
         if (num_tokens_generated % 10 == 0):
            print(".", end="", flush=True)
         if (self.vocab[sample_token] == termination_token):
            break
         num_tokens_generated = len(tokens_generated)
      txt = "".join(
         [self.vocab[_] for _ in start_tokens + tokens_generated]
      )
      print("")
      return txt

# the starting prompt
start_prompt = "D B N C Ӿ50.0"

generator = GptTextGenerator("gpt4096")
generated_text = generator.generate(start_prompt, max_tokens_to_generate=200)
print(f"generated text:\n{generated_text}\n")
