import warnings
warnings.filterwarnings('ignore') # ignore some numpy warnings
import numpy as np
import re
import os, glob, sys, pathlib
import tensorflow as tf

from keras.layers import Dense, LSTM, Input, Embedding, Dropout
from keras.utils import np_utils
from keras.models import Model, load_model
from keras.optimizers import Adam, RMSprop
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras.callbacks import LambdaCallback, ModelCheckpoint

from BoardOperations.brdFile import read_utf8_file_to_string


def read_all_texts(dataset_folder):
   texts = []

   glob_expression = '{}\\*.tokens'.format(dataset_folder)
   files = glob.glob(glob_expression, recursive=False)
   for file_name in files:
      tokenString = read_utf8_file_to_string(file_name)
      texts.append(tokenString)

   return texts

def create_tokenizer(texts):
   tokenizer = Tokenizer(char_level=True, filters='', lower=False, oov_token=1)
   tokenizer.fit_on_texts(texts)

   return tokenizer

def tokenize_inputs(texts):
   tokenizer = create_tokenizer(texts)

   total_words = len(tokenizer.word_index)+1
   print("Total words: ", total_words)
   token_lists = tokenizer.texts_to_sequences(texts)

   print(tokenizer.word_index)
   print("Minimum sequence", min(map(len,token_lists)))
   return total_words, token_lists

def generate_sequences(token_lists, sequence_length, total_words):
   X = []
   Y = []
   print("Reading token files", end='')
   for token_list in token_lists:
      print(".", end="")
      for i in range(0, len(token_list)-sequence_length, 1):
         X.append(token_list[i:i+sequence_length])
         Y.append(token_list[i+sequence_length])
   print("done")

   print("Computing to_categorical")
   Y = np_utils.to_categorical(Y, num_classes=total_words)
   print("Number of sequences:",len(X))

   X = np.array(X)
   Y = np.array(Y)
   return X,Y

def generate_model(total_words):
   n_units = 256
   embedding_size = 100

   text_in = Input(shape=(None,))
   embedding = Embedding(total_words, embedding_size)
   x = embedding(text_in)
   x = LSTM(n_units, return_sequences=True)(x)
   x = LSTM(n_units)(x)
   x = Dropout(0.2)(x)
   text_out = Dense(total_words, activation='softmax')(x)

   model = Model(text_in, text_out)
   optimizer = RMSprop(lr=0.001)
   model.compile(loss='categorical_crossentropy', optimizer=optimizer)
   model.summary()

   return model

def train_model(model, X_train, Y_train):
   epochs = 40
   batch_size = 256
   num_batches = int(len(X_train) / batch_size)

   prefix = 'cb2'

   checkpoint = ModelCheckpoint('data/saved_models/{}_best_model.h5'.format(prefix),
      monitor='loss', verbose=1, save_best_only=True, mode='auto', period=1)

   model.fit(X_train, Y_train, epochs=epochs, batch_size=batch_size, shuffle=True,
      callbacks=[checkpoint])

   model.save('data/saved_models/{}_{}_{}.h5'.format(prefix,epochs,batch_size))

if __name__ == "__main__":
   CWD_FOLDER = os.path.dirname(__file__)
   DATA_FOLDER = os.path.realpath(os.path.join(CWD_FOLDER, "data") )

   DATASET_FOLDER = os.path.join(DATA_FOLDER, 'dataset')

   texts = read_all_texts(DATASET_FOLDER)
   total_words,token_lists = tokenize_inputs(texts)
   X,Y = generate_sequences(token_lists,500,total_words)
   print("X.shape=",X.shape)
   print("Y.shape=",Y.shape)

   model = generate_model(total_words)
   train_model(model, X, Y)