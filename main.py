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
import torch
from PIL import Image

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

# get the git hash of the current commit
short_hash = get_git_revision_short_hash()
git_url = get_git_url()

import argparse

def predict(images, omni):

    #use_GPU = models.use_gpu()
    use_GPU = torch.cuda.is_available()
    print('>>> GPU activated? %d'%use_GPU)

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

    try:
        masks, flows, styles, diams = model.eval(images, channels=channels, rescale=None, diameter=None, flow_threshold=.9, mask_threshold=.25, resample=True, diam_threshold=100)
    except:
        print("Error in OmniPose prediction")
        masks = [[],]

    import cv2

    full_result = []

    for i,_ in enumerate(images):
        int_mask = masks[i]

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


        result = dict(
            model_version = f'{git_url}#{short_hash}',
            format_version = '0.1',
            segmentation = segmentation
        )

        full_result.append(result)

    return full_result

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument('images', type=str, nargs='+',
                    help='list of images')
parser.add_argument('--omni', action="store_true", help="Use the omnipose model")

args = parser.parse_args()

if len(args.images) == 1:
    args.images = args.images[0].split(' ')

images = [np.asarray(Image.open(image_path)) for image_path in args.images]

omni = args.omni

result = predict(images, omni)

if len(images) == 1:
    result = result[0]

with open('output.json', 'w') as output:
    json.dump(result, output)

mlflow.log_artifact('output.json')
