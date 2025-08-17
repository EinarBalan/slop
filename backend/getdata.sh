#!/bin/bash
# curl -L -o archive.zip\
#   https://www.kaggle.com/api/v1/datasets/download/noahpersaud/reddit-submissions-dec-2022-to-feb-2023

curl -L -o archive.zip\
  https://www.kaggle.com/api/v1/datasets/download/einarbalan/slop-reddit

unzip archive.zip -d archive

# rm ~/development/research/slop/backend/archive.zip

# https://www.kaggle.com/datasets/noahpersaud/reddit-submissions-july-2021-to-oct-2022
# https://www.kaggle.com/datasets/noahpersaud/reddit-submissions-dec-2022-to-feb-2023