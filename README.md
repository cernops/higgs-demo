# Higgs Demo

Reperforming the Higgs analysis using Kubernetes.

This tool helps with the submission and management of the Higgs Analysis
against any existing Kubernetes clusters. It relies on the Higgs dataset being
accessing either in a S3 or GCS bucket.

## Dataset

The CMS Higgs dataset is available as open data, and has 70TB over 26920 files.

At CERN it's available under s3.cern.ch://higgs-demo.

## Pre-requisites

It is expected you already have a kubernetes cluster configured in your
environment, ready to be used - meaning `kubectl` commands work. That will be
the cluster used for the analysis.

## Command Line

### Submit

You can trigger the analysis via the command line with:
```bash
higgsdemo submit --dataset-pattern datasets_s3/*SMHiggs* --s3-access-key ... --s3-secret-key ...
```

The dataset-pattern param specifies which subset of the full dataset should be
processed - the whole dataset is ~70TB, so this is a useful option. The other
two params are the S3 credentials.


An example reading from CERN's S3 service:
```bash
higgsdemo submit --dataset-pattern datasets_s3/*SMHiggs* --storage-host https://s3.cern.ch --s3-access-key ... --s3-secret-key ...
```

Check `--help` for further options to customize the submission.
```bash
  --config CONFIG       the demo analyzer config file
  --dataset-pattern DATASET_PATTERN
                        the pattern of datasets to process
  --run RUN             the name of the demo run
  --namespace NAMESPACE
                        the kube namespace to use
  --image IMAGE         the docker image to use for jobs
  --access-key ACCESS_KEY
                        the storage access key
  --secret-key SECRET_KEY
                        the storage secret key
  --storage-type STORAGE_TYPE
                        the type of storage (s3 or gcs)
  --storage-host STORAGE_HOST
                        the storage host(for s3 or gcs)
  --bucket BUCKET       the name of the bucket holding the data
  --output-bucket OUTPUT_BUCKET
                        the name of the bucket to write the output
  --cpu-limit CPU_LIMIT
                        the kube cpu request / limit
  --backoff-limit BACKOFF_LIMIT
                        the kube job backoff limit
  --mc-threads MULTIPART_THREADS
                        the number of minio threads
  --output-file OUTPUT_FILE
                        the local path for the output file
  --output-json-file OUTPUT_JSON_FILE
                        the local path for the output json file
```

### Watch and Cleanup

Similar commands to the above.
```bash
higgsdemo watch
{'pods': {'Running': 48, 'total': 56, 'Succeeded': 8}, 'jobs': {'total': 56, 'succeeded': 8}}
...
```

```bash
higgsdemo cleanup
```

## Python API

You can also trigger the submission using the Python API, useful if you want to
integrate this with a Jupyter notebook for example.
```python
higgs = HiggsDemo(dataset_pattern='*SMHiggs*')
higgs.submit()
```

## Installation

```bash
virtualenv .venv
. .venv/bin/activate
pip install -r requirements
python setup.py install
```
