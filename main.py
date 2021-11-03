import numpy as np
import time, os, sys
from urllib.parse import urlparse
import skimage.io
import matplotlib.pyplot as plt
import matplotlib as mpl
import sys
import mlflow
import json

from cellpose import models

img = skimage.io.imread(sys.argv[1])

use_GPU = models.use_gpu()
print('>>> GPU activated? %d'%use_GPU)

# DEFINE CELLPOSE MODEL
# model_type='cyto' or model_type='nuclei'
model = models.Cellpose(gpu=use_GPU, model_type='cyto')

channels = [[0,0]]
diameter = 30
flow_threshold = 0.4
cellprob_threshold = 0.2

masks, flows, styles, diams = model.eval([img], diameter=diameter, flow_threshold=flow_threshold, channels=channels, cellprob_threshold=cellprob_threshold, tile=True)

import cv2

int_mask = masks[0]

num_cells = np.max(int_mask)
score_threshold = 0.5

all_contours = []

for index in range(1, num_cells+1):
    bool_mask = int_mask == index

    contours, hierarchy = cv2.findContours(np.where(bool_mask > score_threshold, 1, 0).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        np.squeeze(contour)
        all_contours.append(contour)

segmentation = [dict(
    label = 'Cell',
    contour_coordinates = contour.tolist(),
    type = 'Polygon'
) for contour in all_contours]

result = dict(
    model = 'cellpose',
    format_version = '0.1',
    segmentation = segmentation
)

with open('output.json', 'w') as output:
    json.dump(result, output)

mlflow.log_artifact('output.json')
