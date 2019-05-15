from sklearn.neural_network import MLPClassifier
import rasterio as rio
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
import pylab as pl
import seaborn as sns
import os

from .preprocessing import create_raster_df, create_zero_samples, onehot_targets
from .raster import calc_indices
from .io import write_raster

def classify(df, 
             pred_path='data/masked.tif', 
             cv=True,
             onehot=True,
             name='mlp', 
             bands=['B02', 'B03', 'B04', 'B08'],
             algorithm=MLPClassifier()):
    """
    Wrapper for data loading, training, prediction, and some cross-validation metrics.
    
    It saves the raster to disk for review in Qgis (or otherwise).
    args:
        df <- dataframe with band information and labels
        pred_path <- either a dataset or path to multiband raster
        cv <- flag whether or not to run cross validation and produce metrics
        onehot <- whether or not to onehot the targets
        bands <- a list of bands to use. if it is None, then it chooses all 
                bands, including any indices generated on input.
        algorithm <- you may specify your choice of algorithm from sklearn, 
        XGBoost, Keras, etc.
                returns:
        pred <- an array with the classification map
        proba <- probability map from any classification. Will need changing 
                if you want to run regression
        cm <- the confusion matrix from cross validation
        cls <- the classifier model if you need to review it further
    """
    assert isinstance(pred_path, str) or isinstance(pred_path, rio.DatasetReader)
    
    if isinstance(pred_path, str):
        mask_src = rio.open(pred_path)
    else:
        mask_src = pred_path
    if onehot:
        class_cols = list(df['labels'].unique())
    else:
        class_cols = 'labels'
    if bands is None:
        X = df.drop(class_cols + ['labels'], axis=1)
    else:
        X = df[bands]
    y = df[class_cols]
    
    ## Load and prepare the dataset to predict on
    profile = mask_src.profile
    data = mask_src.read(list(pl.arange(mask_src.count) + 1))
    gdf = create_raster_df(data)
    gdf = calc_indices(gdf)
    if cv:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5)
    else:
        X_train, y_train = X, y
        
    ## Train and predict. algorithm is fed in as an argument
    cls = algorithm
    cls.fit(X_train, y_train)
    out = cls.predict(gdf[bands])
    pred = pl.argmax(out, axis=1).reshape((1, data.shape[1], data.shape[2])).astype(pl.int16)
    proba = cls.predict_proba(gdf).max(axis=1).reshape(1, data.shape[1], data.shape[2])
    
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        
    write_raster("outputs/lc_10m_{}_pred.tif".format(name), pred, profile, nodata=0)
    write_raster("outputs/lc_10m_{}_proba.tif".format(name), proba, profile)
    
    if cv:
        cls_cv = cls.predict(X_test)
        score = cls.score(X_test, y_test)
        print(score)
        cm = confusion_matrix(cls_cv, y_test)
        f, ax = pl.subplots(1, figsize = (20, 20))
        sns.heatmap(ax = ax, 
                    data=cm, 
                    annot=True, 
                    fmt='g', 
                    linewidths=0.5, 
                    cbar=False)
        ax.set_ylabel('Predicted')
        ax.set_xlabel('True')
        f.savefig('outputs/cv_{}.png'.format(name))
    else:
        cv = None
    return pred, proba, cm, cls