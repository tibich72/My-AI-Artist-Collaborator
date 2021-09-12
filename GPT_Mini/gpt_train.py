"""
Title: Text generation with a miniature GPT
Author: [Apoorv Nandan](https://twitter.com/NandanApoorv)
Date created: 2020/05/29
Last modified: 2020/05/29
Description: Implement a miniature version of GPT and train it to generate text.
"""
"""
## Introduction
This example demonstrates how to implement an autoregressive language model
using a miniature version of the GPT model.
The model consists of a single Transformer block with causal masking
in its attention layer.
We use the text from the IMDB sentiment classification dataset for training
and generate new movie reviews for a given prompt.
When using this script with your own dataset, make sure it has at least
1 million words.
This example should be run with `tf-nightly>=2.3.0-dev20200531` or
with TensorFlow 2.3 or higher.
**References:**
- [GPT](https://www.semanticscholar.org/paper/Improving-Language-Understanding-by-Generative-Radford/cd18800a0fe0b668a1cc19f2ec95b5003d0a5035)
- [GPT-2](https://www.semanticscholar.org/paper/Language-Models-are-Unsupervised-Multitask-Learners-Radford-Wu/9405cc0d6169988371b2755e573cc28650d14dfe)
- [GPT-3](https://arxiv.org/abs/2005.14165)
"""
"""
## Setup
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
import numpy as np
import os.path
import re
import string
import random

from gpt_model import create_gpt_model
from gpt_dataset import read_dataset





vocab_size = 20000      # Only consider the top 20k words
maxlen = 160            # Max sequence size
embed_dim = 256         # Embedding size for each token
num_heads = 2           # Number of attention heads
feed_forward_dim = 256  # Hidden layer size in feed forward network inside transformer



"""
## Prepare the data for word-level language modelling
Data will be read from the folders listed in 'directories'
"""

batch_size = 4096

# The list of folders with text files for the dataset
# The paths should be relative to the location of this file
dataset_folders = [
   "../data/dataset"
]
dataset_folders = [os.path.abspath(os.path.join(os.path.dirname(__file__), _)) for _ in dataset_folders]
vocab, text_ds = read_dataset(dataset_folders, maxlen)
vocab_size = len(vocab)
"""
## Implement a Keras callback for generating text
"""


class TextGenerator(keras.callbacks.Callback):
   """A callback to generate text from a trained model.
   1. Feed some starting prompt to the model
   2. Predict probabilities for the next token
   3. Sample the next token and add it to the next input
   Arguments:
      max_tokens: Integer, the number of tokens to be generated after prompt.
      start_tokens: List of integers, the token indices for the starting prompt.
      index_to_word: List of strings, obtained from the TextVectorization layer.
      top_k: Integer, sample from the `top_k` token predictions.
      print_every: Integer, print after this many epochs.
   """

   def __init__(
      self, max_tokens, start_tokens, index_to_word, top_k=10, print_every=1
   ):
      self.max_tokens = max_tokens
      self.start_tokens = start_tokens
      self.index_to_word = index_to_word
      self.print_every = print_every
      self.k = top_k

   def sample_from(self, logits):
      logits, indices = tf.math.top_k(logits, k=self.k, sorted=True)
      indices = np.asarray(indices).astype("int32")
      preds = keras.activations.softmax(tf.expand_dims(logits, 0))[0]
      preds = np.asarray(preds).astype("float32")
      return np.random.choice(indices, p=preds)

   def detokenize(self, number):
      return self.index_to_word[number]

   def on_epoch_end(self, epoch, logs=None):
      start_tokens = [_ for _ in self.start_tokens]
      if (epoch + 1) % self.print_every != 0:
         return
      num_tokens_generated = 0
      tokens_generated = []
      while num_tokens_generated <= self.max_tokens:
         pad_len = maxlen - len(start_tokens)
         sample_index = len(start_tokens) - 1
         if pad_len < 0:
               x = start_tokens[:maxlen]
               sample_index = maxlen - 1
         elif pad_len > 0:
               x = start_tokens + [0] * pad_len
         else:
               x = start_tokens
         x = np.array([x])
         y, _ = self.model.predict(x)
         sample_token = self.sample_from(y[0][sample_index])
         tokens_generated.append(sample_token)
         start_tokens.append(sample_token)
         num_tokens_generated = len(tokens_generated)
      txt = "".join(
         [self.detokenize(_) for _ in self.start_tokens + tokens_generated]
      )
      print(f"generated text:\n{txt}\n")


# Tokenize starting prompt
word_to_index = {}
for index, word in enumerate(vocab):
    word_to_index[word] = index

start_prompt = "D B N C Ӿ50.0"
start_tokens = [word_to_index.get(_, 1) for _ in list(start_prompt)]
num_tokens_generated = 80
text_gen_callback = TextGenerator(num_tokens_generated, start_tokens, vocab)


"""
## Train the model
Note: This code should preferably be run on GPU.
"""

model = create_gpt_model(vocab_size, maxlen, embed_dim, num_heads, feed_forward_dim)
model.summary()

epochs = 300
model.fit(text_ds, verbose=2, epochs=epochs)#, callbacks=[text_gen_callback])
model_path = os.path.join(os.path.dirname(__file__), "..", "models")
model_name = f"gpt{epochs}_{num_heads}_{maxlen}_{embed_dim}"
model_path = os.path.join(model_path, model_name)
model.save(model_path, save_format='tf')
