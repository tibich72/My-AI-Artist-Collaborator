"""
Creates a dataset from a list of folders
"""
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
import numpy as np
import os
import re
import string
import random


def custom_standardization(input_string):
   """ Remove html line-break tags and handle punctuation """
   lowercased = tf.strings.lower(input_string)
   stripped_html = tf.strings.regex_replace(lowercased, "<br />", " ")
   return tf.strings.regex_replace(stripped_html, f"([{string.punctuation}])", r" \1")

def custom_split(input_string):
   """ Splits the input string character by character """
   return tf.strings.unicode_split(input_string, 'UTF-8')

def read_dataset(directories, maxlen):
   batch_size = 1024

   filenames = []
   for dir in directories:
      for f in os.listdir(dir):
         filenames.append(os.path.join(dir, f))

   print(f"Read {len(filenames)} files")

   # Create a dataset from text files
   random.shuffle(filenames)
   text_ds = tf.data.TextLineDataset(filenames)
   text_ds = text_ds.shuffle(buffer_size=256)
   text_ds = text_ds.batch(batch_size)

   # Create a vectorization layer and adapt it to the text
   vectorize_layer = preprocessing.TextVectorization(
      standardize=None, # don't lower-case or strip any special characters
      max_tokens=None,  # no limit on the vocabulary (about 67 tokens for encoded boards)
      output_mode="int",
      split=custom_split, # split by character
      output_sequence_length=maxlen + 1,
   )
   vectorize_layer.adapt(text_ds)
   vocab = vectorize_layer.get_vocabulary()  # To get words back from token indices
   print("Vocabulary: ",vocab)

   def prepare_lm_inputs_labels(text):
      """
      Shift word sequences by 1 position so that the target for position (i) is
      word at position (i+1). The model will use all words up till position (i)
      to predict the next word.
      """
      text = tf.expand_dims(text, -1)
      tokenized_sentences = vectorize_layer(text)
      x = tokenized_sentences[:, :-1]
      y = tokenized_sentences[:, 1:]
      return x, y

   text_ds = text_ds.map(prepare_lm_inputs_labels)
   text_ds = text_ds.prefetch(tf.data.experimental.AUTOTUNE)

   return vocab, text_ds

