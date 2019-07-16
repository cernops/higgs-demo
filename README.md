# Higgs Demo

Reperforming the Higgs analysis using Kubernetes.

This tool helps with the submission and management of the Higgs Analysis
against any existing Kubernetes cluster. It relies on the Higgs dataset being
accessible either in a S3 or GCS bucket.

## Dataset

The CMS Higgs dataset is available as open data, and has 70TB over 26920 files.

It is expected that it is made available in the same cloud provider you plan to
run the computation - S3 or GCS are supported.

## Configuration Files

If you look into the `config` directory you can find a few examples of demo
configuration files. It offers enough flexibility to scale the demo and to
split the submission across multiple clusters if needed.

Each JSON entry in the list includes the information for a corresponding
cluster named `kubecon-demo-$i`, where `$i` is the list index. The remaining
fields include the node flavor to be used, the number of cluster nodes, and the
path to use for the stage-in data (/dev/shm for shared memory, which is the
recommended setup).

## Command Line

The `higgsdemo` command line offers the following functionality.

### Clusters Create

`clusters-create` will create one cluster per list entry in the config file,
matching the given flavor and number of nodes. Clusters will be named
`kubecon-demo-$i`, where `$i` is the list index in the config.

This is mostly useful where splitting the submission across multiple clusters
is required.

### Prepare

This is useful to speed up the actual demo, and makes sure the docker image is
available in advance on every cluster node.
```bash
higgsdemo prepare --dataset-mapping config/demo-highmem-minimal.json
```

### Submit

Here's an example submission for a scaled down analysis:
```bash
higgsdemo submit --dataset-mapping config/demo-highmem-minimal.json --access-key ... --secret-key ...
```

The dataset-mapping should point to one of the config files. It will spawn
a set of parallel processes (one per cluster) doing the submission. The
remaining params are the access and secret keys to either S3 or GCS.

### Watch and Cleanup

To check the evolution of the computation you can trigger a watch in a specific
cluster:
```bash
higgsdemo watch --cluster kubecon-demo-0
{'pods': {'Running': 48, 'total': 56, 'Succeeded': 8}, 'jobs': {'total': 56, 'succeeded': 8}}
...
```

To reperform the computation in an existing cluster, a cleanup is required:
```bash
higgsdemo cleanup --cluster kubecon-demo-0
```

### Sample Run

```bash
higgsdemo clusters-create --dataset-mapping config/demo-high-mem.json

for i in 0 1 2 3 4 5 6 7 8 9; do gcloud container clusters get-credentials --region europe-west4 kubecon-demo-$i; done

higgsdemo prepare --dataset-mapping config/demo-high-mem.json

# monitor prepull progress in a single cluster
kubectl --context ... -n prepull get po

higgsdemo submit --access-key ... --secret-key ... --dataset-mapping config/demo-high-mem.json
```

## Installation

```bash
virtualenv .venv
. .venv/bin/activate
pip install -r requirements
python setup.py install
```
