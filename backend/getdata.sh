#!/bin/bash
curl -L -o ~/Downloads/reddit-submissions-dec-2022-to-feb-2023.zip\
  https://www.kaggle.com/api/v1/datasets/download/noahpersaud/reddit-submissions-dec-2022-to-feb-2023

unzip ~/Downloads/reddit-submissions-dec-2022-to-feb-2023.zip -d ~/Downloads/reddit-submissions-dec-2022-to-feb-2023

rm ~/Downloads/reddit-submissions-dec-2022-to-feb-2023.zip

