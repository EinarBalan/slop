#!/bin/bash
#!/bin/bash
curl -L -o ~/development/research/slop/backend/archive.zip\
  https://www.kaggle.com/api/v1/datasets/download/noahpersaud/reddit-submissions-dec-2022-to-feb-2023

unzip ~/development/research/slop/backend/archive.zip -d ~/development/research/slop/backend/archive

# rm ~/development/research/slop/backend/archive.zip

# https://www.kaggle.com/datasets/noahpersaud/reddit-submissions-july-2021-to-oct-2022
# https://www.kaggle.com/datasets/noahpersaud/reddit-submissions-dec-2022-to-feb-2023