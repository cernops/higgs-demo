# Higgs Demo

Reperforming the Higgs analysis using Kubernetes.

This tool helps with the submission and management of the Higgs Analysis
against any existing Kubernetes clusters. It relies on the Higgs dataset being
accessing either in a S3 or GCS bucket.

## Pre-requisites

It is expected you already have a kubernetes cluster configured in your
environment, ready to be used - meaning `kubectl` commands work. That will be
the cluster used for the analysis.

## Command Line

You can trigger the analysis via the command line with:
```bash
higgs-demo submit --dataset-pattern datasets_s3/*SMHiggs*
```

The dataset-pattern param specifies which subset of the full dataset should be
processed - the whole dataset is ~70TB, so this is a useful option.

Check `--help` for further options to customize the submission.

## Python API

You can also trigger the submission using the Python API, useful if you want to
integrate this with a Jupyter notebook for example.
```python
higgs = HiggsDemo(dataset_pattern='*SMHiggs*')
higgs.submit()
```

