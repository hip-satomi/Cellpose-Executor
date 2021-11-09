import numpy as np
import time, os, sys
from urllib.parse import urlparse
import skimage.io
import matplotlib.pyplot as plt
import matplotlib as mpl
import sys
import mlflow
import json
import subprocess
from urllib.parse import urlparse

from cellpose import models

def get_git_revision_short_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

def get_git_url() -> str:
    basic_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('ascii').strip()
    parsed = urlparse(basic_url)
    if parsed.username and parsed.password:
        # erase username and password
        return parsed._replace(netloc="{}".format(parsed.hostname)).geturl()
    else:
        return parsed.geturl()

img = skimage.io.imread(sys.argv[1])

if len(sys.argv) > 2 and sys.argv[2] == 'omni':
    omni = True
else:
    omni = False

#use_GPU = models.use_gpu()
use_GPU = False
print('>>> GPU activated? %d'%use_GPU)
print('Hard coded deactivation')

# DEFINE CELLPOSE MODEL
# model_type='cyto' or model_type='nuclei'
if omni:
    print('Loading omni model...')
    model = models.Cellpose(gpu=use_GPU, model_type='bact_omni', omni=True)
else:
    model = models.Cellpose(gpu=use_GPU, model_type='cyto')


channels = [[0,0]]
diameter = 30
flow_threshold = 0.4
cellprob_threshold = 0.2

#flow_threshold=flow_threshold, cellprob_threshold=cellprob_threshold

masks, flows, styles, diams = model.eval([img], channels=channels, rescale=None, diameter=None, flow_threshold=.5, mask_threshold=.25, resample=True)

import cv2

int_mask = masks[0]

num_cells = np.max(int_mask)
score_threshold = 0.5

all_contours = []

for index in range(1, num_cells+1):
    bool_mask = int_mask == index

    contours, hierarchy = cv2.findContours(np.where(bool_mask > score_threshold, 1, 0).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        contour = np.squeeze(contour)
        all_contours.append(contour)

segmentation = [dict(
    label = 'Cell',
    contour_coordinates = contour.tolist(),
    type = 'Polygon'
) for contour in all_contours]

# get the git hash of the current commit
short_hash = get_git_revision_short_hash()
git_url = get_git_url()

result = dict(
    model_version = f'{git_url}#{short_hash}',
    format_version = '0.1',
    segmentation = segmentation
)

with open('output.json', 'w') as output:
    json.dump(result, output)

mlflow.log_artifact('output.json')
