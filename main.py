from numpy.random import seed
seed(1)
from tensorflow import set_random_seed
set_random_seed(1)
import random as rn
rn.seed(1)

import os
import time
import json
import numpy as np
from itertools import chain
import collections
import matplotlib.pyplot as plt
import seaborn

# from keras.applications.xception import Xception
# from sklearn.preprocessing import MultiLabelBinarizer
from keras_preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import BatchNormalization
from keras import optimizers
from keras.optimizers import SGD
from PIL import Image
import tensorflow as tf
from keras.backend import tensorflow_backend

config = tf.ConfigProto(gpu_options=tf.GPUOptions(allow_growth=True))
session = tf.Session(config=config)
tensorflow_backend.set_session(session)

import read_data_df as rd

print('Imports done')

root_path = os.getcwd()

Server = False
# Server = True

if Server:
    path_to_images = root_path + '/DATA/bigearth/dump/sample/'

    with open('/home/strathclyde/DATA/corine_labels.json') as jf:
        names = json.load(jf)

else:
    path_to_images = root_path + '/data/sample/'

    with open('data/corine_labels.json') as jf:
        names = json.load(jf)

st = time.time()

patches = [patches for patches in os.listdir(path_to_images)]

patches, split_point = rd.get_patches(patches)

print('patch count: {}'.format(len(patches)))
# print('split point: {}'.format(split_point))

split_point=3751
df, class_count = rd.read_patch(split_point)

class_rep = list(chain.from_iterable(df['labels']))
counter=collections.Counter(class_rep)
print('class dist: {}'.format(counter))
plt.bar(range(len(counter)), list(counter.values()), align='center')
# plt.xticks(range(len(counter)), list(counter.keys()))
plt.title('Training classes')
plt.ion()
plt.show()
# print('class list: {}'.format(classes))
# print('class count: {}'.format(class_present))

print('df : {}'.format(df.head()))

print(set(df['path'].apply(lambda x: os.path.exists(x))))

en = time.time()
t = en - st
print('Images ready in: {} minutes'.format(int(t/60)))

model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(120, 120, 3)))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(class_count, activation='sigmoid'))

print('Normalizing images...')
data_gen = ImageDataGenerator(rescale=1.0/255.0, validation_split=0.3)
# data_gen = ImageDataGenerator(validation_split=0.3)

print('Flowing training set...')

# directory = path_to_merge,

training_data = data_gen.flow_from_dataframe(
                dataframe = df,
                x_col = 'path',
                y_col = 'labels',
                subset = "training",
                seed = 1,
                target_size = (120,120),
                class_mode = 'categorical',
                batch_size = 64,
                shuffle = True)

train_cls = training_data.class_indices
train_rep = training_data.classes
train_rep = list(chain.from_iterable(train_rep))
counter=collections.Counter(train_rep)

print('Training indices: {}'.format(train_cls))
print('training class count: {}'.format(counter))

plt.bar(range(len(counter)), list(counter.values()), align='center')
plt.xticks(range(len(counter)), list(counter.keys()))
plt.title('Training classes')
plt.ion()
plt.show()

print('Flowing validation set...')

validation_data = data_gen.flow_from_dataframe(
                dataframe = df,
                x_col = 'path',
                y_col = 'labels',
                subset = "validation",
                seed = 1,
                target_size = (120,120),
                class_mode = 'categorical',
                batch_size = 64,
                shuffle = True)

valid_cls = validation_data.class_indices
valid_rep = validation_data.classes
valid_rep = list(chain.from_iterable(valid_rep))
counter=collections.Counter(valid_rep)

print('Validation indices: {}'.format(validation_data.class_indices))
print('valid class count: {}'.format(counter))

plt.bar(range(len(counter)), list(counter.values()), align='center')
plt.xticks(range(len(counter)), list(counter.keys()))
plt.title('Validation classes')
plt.ion()
plt.show()

print('Training network...')

sgd = optimizers.SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)

model.compile(optimizer=sgd, loss='binary_crossentropy',
              metrics=['categorical_accuracy'])

history = model.fit_generator(training_data,
                    steps_per_epoch=1200,
                    epochs=10,
                    validation_data=validation_data,
                    validation_steps=800)

# keys = history.history.keys

plt.plot(history.history['categorical_accuracy'])
plt.plot(history.history['val_categorical_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='lower right')
plt.show(block=True)

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper right')
plt.show(block=True)

# if __name__ == '__main__':
#     rd