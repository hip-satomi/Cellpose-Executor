import unittest
import os
from git_utils import get_git_url
import mlflow
import json

from git_utils import get_git_revision_short_hash


class TestSegmentation(unittest.TestCase):

    def setUp(self):
        # download the image
        import requests

        url = 'https://fz-juelich.sciebo.de/s/wAXbC0MoN1G3ST7/download'
        r = requests.get(url, allow_redirects=True)

        print(len(r.content))

        with open('test.png', 'wb') as file:
            file.write(r.content)

    def test_cellpose(self):
        # test entrypoints: main (Cellpose)
        self.predict('main')
    
    def test_omnipose(self):
        self.predict('omnipose')

    def predict(self, entrypoint):
        import requests
        from io import BytesIO
        from PIL import Image
        import json

        contours = []

        image = Image.open('test.png')

        # convert image into a binary png stream
        byte_io = BytesIO()
        image.save(byte_io, "png")
        byte_io.seek(0)

        # pack this into form data
        multipart_form_data = [
            ("files", ("data.png", byte_io, "image/png"))
        ]

        # get job specific environment variables
        CI_COMMIT_SHA = os.environ['CI_COMMIT_SHA']
        CI_REPOSITORY_URL = os.environ['CI_REPOSITORY_URL']

        additional_parameters = {}

        # exactly request segmentation with the current repo version
        params = dict(
            repo=CI_REPOSITORY_URL,
            entry_point=entrypoint,
            version=CI_COMMIT_SHA,
            parameters=json.dumps(additional_parameters),
        )

        # send a request to the server
        response = requests.post(
            'http://segserve/batch-image-prediction/', params=params, files=multipart_form_data, timeout=20 * 60
        )

        # output response
        print(response.content)

        # the request should be successful
        self.assertTrue(response.status_code == 200)

    def test_info_endpoint(self):
        run = mlflow.projects.run(
            './',
            entry_point="info",
            backend='local',
        )

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', './')

        with open('output.json', 'r') as input_file:
            info_result = json.load(input_file)
            self.assertTrue(info_result['name'] == 'cellpose/omnipose')
            self.assertTrue(info_result['git_hash'] == get_git_revision_short_hash())
            self.assertTrue(info_result["git_url"] == get_git_url())
            self.assertTrue(info_result["type"] == "info")


if __name__ == '__main__':
    unittest.main()