#!/bin/bash

echo "Project Url: ${CI_PROJECT_URL}"
echo "Version: ${CI_COMMIT_SHA}"

curl -f -X 'POST' \
  'http://segServe:8000/image-prediction/' \
  -F "repo=${CI_PROJECT_URL}" \
  -F "entry_point=main" \
  -F "version=${CI_COMMIT_SHA}" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@test.jpg;type=image/jpeg'
