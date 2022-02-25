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
import cv2
from tqdm.contrib.concurrent import process_map
import glob


from cellpose import models

def extract_rois(int_mask):
    num_cells = np.max(int_mask)
    score_threshold = 0.5

    all_contours = []

    for index in range(1, num_cells+1):
        bool_mask = int_mask == index

        contours, hierarchy = cv2.findContours(np.where(bool_mask > score_threshold, 1, 0).astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            contour = np.squeeze(contour)
            if contour.shape[0] < 3:
                # drop non 2D contours
                continue

            all_contours.append(contour)

    return all_contours

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
        masks, flows, styles, diams = model.eval(images, channels=[0,0],
                                            diameter=0.0, invert=False,
                                            net_avg=False, augment=False, resample=False,
                                            do_3D=False, progress=None, omni=True)
    except:
        print("Error in OmniPose prediction")
        masks = [[],]

    import cv2

    full_result = []

    all_rois = []
    for res in process_map(extract_rois, masks, max_workers=5, chunksize=4):
        all_rois.append(res)

    for roi_list in all_rois:
        segmentation = [dict(
            label = 'Cell',
            contour_coordinates = contour.tolist(),
            type = 'Polygon'
        ) for contour in roi_list]

        full_result.append(segmentation)

    return full_result

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument('images', type=str, nargs='+',
                    help='list of images')
parser.add_argument('--omni', action="store_true", help="Use the omnipose model")

args = parser.parse_args()

if len(args.images) == 1:
    image_path = args.images[0]
    if os.path.isdir(image_path):
        # it's a folder, iterate all images in the folder
        args.images = sorted(glob.glob(os.path.join(image_path, '*.png')))
    else:
        # it may be a list of images
        args.images = image_path.split(' ')

images = [np.asarray(Image.open(image_path)) for image_path in args.images]

omni = args.omni

result = predict(images, omni)

# package everything
result = dict(
    model = f'{git_url}#{short_hash}',
    format_version = '0.2',
    segmentation_data = result
)

with open('output.json', 'w') as output:
    json.dump(result, output)

mlflow.log_artifact('output.json')
