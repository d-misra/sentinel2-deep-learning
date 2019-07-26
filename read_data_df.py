from numpy.random import seed
seed(1)
from tensorflow import set_random_seed
set_random_seed(1)
import random as rn
rn.seed(1)

from glob import glob
import pandas as pd
import rasterio as rio
import pylab as pl
import os
import numpy as np
import time
import random
import json
import scipy.misc

st = time.time()

bands = ['B02', 'B03', 'B04']
root_path = os.getcwd()

print('root path: {}'.format(root_path))
print('Using bands: {}'.format(bands))

print('Reading BigEarthNet imagery...')

path_to_images = root_path + '/data/sample/'
path_to_split = root_path + '/data/split/'
path_to_train = root_path  + '/data/split/train/'
path_to_validation = root_path + '/data/split/validation/'

path_to_merge = root_path + '/data/merge/'

with open('data/corine_labels.json') as jf:
    names = json.load(jf)

patches = [patches for patches in os.listdir(path_to_images)]

# path_to_images = root_path + '/DATA/bigearth/sample/'
# path_to_split = root_path + '/DATA/bigearth/split/'
# path_to_train = root_path  + '/DATA/bigearth/split/train/'
# path_to_validation = root_path + '/DATA/bigearth/split/validation/'

# with open('/home/strathclyde/DATA/corine_labels.json') as jf:
#     names = json.load(jf)

print('Forming into train and validation subsets...')

def build_dirs():

    for value in names.values():
        if not os.path.isdir(path_to_train + value):
            os.makedirs(path_to_train + value)
        if not os.path.isdir(path_to_validation + value):
            os.makedirs(path_to_validation + value)

    for split in os.listdir(path_to_split):
        split = split + '/'
        for sub_dir in os.listdir(os.path.join(path_to_split, split)):
            sub_dir = sub_dir + '/'
            split_path = path_to_split + split
            if not os.listdir(os.path.join(split_path, sub_dir)):
                continue
            else:
                for file in os.listdir(os.path.join(split_path, sub_dir)):
                    filepath = split_path + sub_dir + file
                    os.remove(filepath)

    print('Empty class directories ready...')

# build_dirs()

def get_patches(patches):

    valid_split = 0.3
    print('Raw patch count: {}'.format(len(patches)))

    cloud_patches = pd.read_csv(root_path + '/data/patches_with_cloud_and_shadow.csv', 'r', header=None)
    snow_patches = pd.read_csv(root_path + '/data/patches_with_seasonal_snow.csv', 'r', header=None)

    # cloud_patches = pd.read_csv(root_path + '/DATA/patches_with_cloud_and_shadow.csv','r', header=None)
    # snow_patches = pd.read_csv(root_path + '/DATA/patches_with_seasonal_snow.csv', 'r', header=None)

    bad_patches = pd.concat([cloud_patches, snow_patches], axis=1)

    print('Purging cloud, shadow and snow patches...')

    patches = [patch for patch in patches if not patch in bad_patches.values]
    
    print('Processing {} clean patches...'.format(len(patches)))
    
    split_point = int(len(patches) * valid_split)

    return patches, split_point

patches, split_point = get_patches(patches)

def read_patch(split_point, bands = ['B02', 'B03', 'B04'], nodata=-9999):

    ''' Returns a NumPy array for each patch,
    consisting of the four bands'''

    print('Shuffling patches...')
    random.shuffle(patches)

    cols = ['path', 'labels']
    index = range(0, len(patches) - 1)
    df = pd.DataFrame(index=index, columns=cols)

    print('Merging RGB bands...')
    class_rep = []

    for i in range(0, len(patches) - 1):

        tifs = glob(path_to_images + '{}/*.tif'.format(patches[i]), recursive=True)
        band_tifs = [tif for tif in tifs for band in bands if band in tif]

        # with open('/home/strathclyde/DATA/bigearth/sample/{}/{}_labels_metadata.json'\
        #           .format(patches[i], patches[i])) as js:
        #     meta = json.load(js)

        with open('data/sample/{}/{}_labels_metadata.json' \
                  .format(patches[i], patches[i])) as js:
            meta = json.load(js)

        labels = meta.get('labels')
        label = labels[0] + '/'          # taking just the first label for now
        if label == 'Transitional woodland/shrub/':
            label = 'Transitional woodland or shrub/'
        class_rep.append(label)

        band_tifs.sort()

        files2rio = list(map(rio.open, band_tifs))
        data = pl.stack(list(map(lambda x: x.read(1).astype(pl.int16), files2rio)))
        data = np.moveaxis(data, 0, 2)

        # vec = np.asarray(data.shape[0]*dxxxxata.shape[1]*data.shape[2])
        # np.savez((path + label + patches[i]), vec)

        # if i < split_point:
        #     path = path_to_validation
        # else:
        #     path = path_to_train

        # if i==6:
        #     print(path + patches[i])
        # scipy.misc.toimage(data[...]).save(path + label + patches[i] + '.jpeg')

        scipy.misc.toimage(data[...]).save(path_to_merge + patches[i] + '.JPG')

        if i==6:
            print(path_to_merge + patches[i])

        df.iloc[i] = [path_to_merge + patches[i] + '.JPG', ', '.join(labels)]

    print('Patches sorted into classes...')

    class_count = len(set(class_rep))

    # valid_df = df.iloc[0:split_point, :]
    # train_df = df.iloc[split_point:,]

    return class_count, df

class_count, df = read_patch(split_point)

print(df)
# print(len(set(train_df.iloc[:,1])))
# print('Ready to train on {} RGB patches belonging to {}/{} classes.' \
#       .format(len(patches), class_count, len(names)))

en = time.time()
t = en - st

print('Time taken: {} minutes'.format(int(t/60)))
