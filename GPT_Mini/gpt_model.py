
"""
## Implements a miniature GPT model
Follows example from https://keras.io/examples/generative/text_generation_with_miniature_gpt/
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

def causal_attention_mask(batch_size, n_dest, n_src, dtype):
    """
    Mask the upper half of the dot product matrix in self attention.
    This prevents flow of information from future tokens to current token.
    1's in the lower triangle, counting from the lower right corner.
    """
    i = tf.range(n_dest)[:, None]
    j = tf.range(n_src)
    m = i >= j - n_src + n_dest
    mask = tf.cast(m, dtype)
    mask = tf.reshape(mask, [1, n_dest, n_src])
    mult = tf.concat(
        [tf.expand_dims(batch_size, -1), tf.constant([1, 1], dtype=tf.int32)], 0
    )
    return tf.tile(mask, mult)


class TransformerBlock(layers.Layer):
   """
   ## Implement a Transformer block as a layer
   """
   def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
      super(TransformerBlock, self).__init__()
      self.att = layers.MultiHeadAttention(num_heads, embed_dim)
      self.ffn = keras.Sequential(
         [layers.Dense(ff_dim, activation="relu"), layers.Dense(embed_dim),]
      )
      self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
      self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
      self.dropout1 = layers.Dropout(rate)
      self.dropout2 = layers.Dropout(rate)

   def call(self, inputs):
      input_shape = tf.shape(inputs)
      batch_size = input_shape[0]
      seq_len = input_shape[1]
      causal_mask = causal_attention_mask(batch_size, seq_len, seq_len, tf.bool)
      attention_output = self.att(inputs, inputs, attention_mask=causal_mask)
      attention_output = self.dropout1(attention_output)
      out1 = self.layernorm1(inputs + attention_output)
      ffn_output = self.ffn(out1)
      ffn_output = self.dropout2(ffn_output)
      return self.layernorm2(out1 + ffn_output)

class TokenAndPositionEmbedding(layers.Layer):
   """
   ## Implements an embedding layer
   Create two seperate embedding layers: one for tokens and one for token index (positions).
   """
   def __init__(self, maxlen, vocab_size, embed_dim):
      super(TokenAndPositionEmbedding, self).__init__()
      self.token_emb = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
      self.pos_emb = layers.Embedding(input_dim=maxlen, output_dim=embed_dim)

   def call(self, x):
      maxlen = tf.shape(x)[-1]
      positions = tf.range(start=0, limit=maxlen, delta=1)
      positions = self.pos_emb(positions)
      x = self.token_emb(x)
      return x + positions

def create_gpt_model(
      vocab_size: int, maxlen: int, embed_dim: int,
      num_heads: int, feed_forward_dim: int) -> keras.Model:
   """ Creates and returns a mini GPT model
   
   Parameters
   ----------
   vocab_size: int    
      The size of the vocabulary
   maxlen: int        
      Maximum sequence size
   embed_dim: int
      Embedding size for each token
   num_heads: int
      Number of attention heads
   feed_forward_dim: int
      Hidden layer size in feed forward network inside transformer
   """
   inputs = layers.Input(shape=(maxlen,), dtype=tf.int32, name="InputLayer")
   embedding_layer = TokenAndPositionEmbedding(maxlen, vocab_size, embed_dim)
   x = embedding_layer(inputs)
   transformer_block = TransformerBlock(embed_dim, num_heads, feed_forward_dim)
   x = transformer_block(x)
   outputs = layers.Dense(vocab_size)(x)
   model = keras.Model(inputs=inputs, outputs=[outputs, x])
   loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
   model.compile(
      "adam", loss=[loss_fn, None],
   )  # No loss and optimization based on word embeddings from transformer block
   return model
