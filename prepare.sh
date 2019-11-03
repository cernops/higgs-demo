#!/bin/bash
set +x

ln -s /eos/user/r/rbritoda ~/eos
kinit rbritoda@CERN.CH
cp -r ~/eos/.config/gcloud ~/.config
