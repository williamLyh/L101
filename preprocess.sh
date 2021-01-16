#!/bin/bash

if [ "$#" -lt 1 ]; then
  echo "./preprocess_WEBNLG.sh <dataset_folder>"
  exit 2
fi

python preprocessing_webnlg.py ${1}