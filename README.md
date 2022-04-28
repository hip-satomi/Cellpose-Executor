# CellPose-Executor

This is a [SegServe](https://github.com/hip-satomi/SegServe) executor for the [Cellpose](https://doi.org/10.1038/s41592-020-01018-x) and [Omnipose](https://doi.org/10.1101/2021.11.03.467199 ) cell segmentation methdod [implementation](https://github.com/MouseLand/cellpose).

## Local testing

Make sure you have [anaconda](https://www.anaconda.com/products/distribution) installed and an active environment with [`mlflow`](https://pypi.org/project/mlflow/). Then execute
```bash
pip install mlflow
mlproject run ./ -e omnipose -P input_images=<path to your local image or image folder (*.png)>
```
The resulting segmentation should be written to `output.json` and logged as an artifact in the mlflow run.

## Intended Usage

The wrapper is used to deploy the Cellpose/Omnipose methods in the [SegServe](https://github.com/hip-satomi/SegServe) runtime environment. SegServe can be used to host 3rd party segmentation algorithms and execute them on a central computer while providing a REST interface for clients. Therefore, end-users do not need any powerful hardware/GPU.
