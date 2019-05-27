import glob
import joblib
import json
import os
import re
import sys
import yaml

from string import Template

from cliff.app import App
from cliff.commandmanager import CommandManager
from kubernetes import client
from kubernetes import config as kube_config
from kubernetes import utils
from kubernetes import watch


class HiggsDemo(object):

    def __init__(self, dataset_pattern='*Higgs*', namespace='default',
            image='lukasheinrich/cms-higgs-4l-full', access_key='',
            secret_key='', storage_type='gs', storage_host='https://storage.googleapis.com',
            cpu_limit='900m', bucket='higgs-demo-nl', output_bucket='higgs-demo-nl',
            backoff_limit=5,  multipart_threads=10, output_file='/tmp/output.root',
            output_json_file='/tmp/output.json', redis_host='10.0.0.4',
            gcs_project_id='nimble-valve-236407',
            download_max_kb=50000, upload_max_kb=10000,
            run='run6', limit=200, cluster=None, dataset_mapping=None,
            dataset_index=None, gcs_region='europe-west4', prefix='kubecon-demo-',
            dpath='/mnt/disks/ssd0'):
        super(HiggsDemo, self).__init__()
        self.dataset_pattern = dataset_pattern
        self.dataset_index = dataset_index
        self.ftype = "Directory"
        self.dpath = dpath
        if dataset_mapping:
            self.dataset_mapping = dataset_mapping
            with open(dataset_mapping, "r") as f:
                self.dataset_mapping = json.load(f)
                if self.dataset_index is not None and 'dpath' in self.dataset_mapping[self.dataset_index]:
                    dpath = self.dataset_mapping[self.dataset_index]['dpath']
                    if dpath == '/dev/null':
                        self.ftype = "File"
                    self.dpath = dpath

        self.namespace = namespace
        self.image = image
        self.access_key = access_key
        self.secret_key = secret_key
        self.storage_type = storage_type
        self.storage_host = storage_host
        if self.storage_host == '':
            if self.storage_type == 'gcs':
                self.storage_host = 'https://storage.googleapis.com'
            elif self.storage_type == 's3':
                self.storage_host = 'https://s3.amazonaws.com'
        self.bucket = bucket
        self.output_bucket = output_bucket
        self.cpu_limit = cpu_limit
        self.backoff_limit = backoff_limit
        self.multipart_threads = multipart_threads
        self.output_file = output_file
        self.output_json_file = output_json_file
        self.redis_host = redis_host
        self.gcs_project_id = gcs_project_id
        self.download_max_kb = download_max_kb
        self.upload_max_kb = upload_max_kb
        self.run = run
        self.limit = limit
        self.prefix = prefix
        self.gcs_region = gcs_region
        self.cluster = cluster

        self._dataset_job_counter = {}

        kube_config.load_kube_config(
                context="gke_%s_%s_%s" % (gcs_project_id, gcs_region, cluster))
        self.api_client = client.ApiClient()
        self.core_client = client.CoreV1Api()
        self.batch_client = client.BatchV1Api()

    def _job_template(self):
        content = ''
        with open('job-template.yaml', 'r') as job_file:
            content = job_file.read()
            return content

    def _job_manifest(self, **kwargs):
        job_template = self._job_template()

        template = Template(self._job_template())
        manifest = template.safe_substitute(kwargs)
        return manifest

    def _jsonfile(self, year):
        jsonfiles = {
            2011: '/json_files/Cert_160404-180252_7TeV_ReRecoNov08_Collisions11_JSON.txt',
            2012: '/json_files/Cert_190456-208686_8TeV_22Jan2013ReReco_Collisions12_JSON.txt'
        }
        return jsonfiles[year]

    def _datasetname(self, filename):
        replace = [
            re.search('_AODSIM.*v[0-9]+',filename),
            re.search('CMS_MonteCarlo20[0-9]*_',filename),
            re.search('_file_index.txt',filename),
        ]

        datasetname = os.path.basename(filename)
        for r in replace:
            datasetname = datasetname if not r else datasetname.replace(r.group(0),'')
        datasetname = datasetname.lower().replace(
            # '_','').replace(
            # '-','').lower().replace(
            'summer','sm').replace(
            'powheg','pw').replace(
            'jhugenv3','j3').replace(
            'pythia','py').replace(
            'madgraph-tarball-tauola','mgtt').replace(
            'madgraph-tauola','mgt').replace(
            'tunez2star','tz2'
        )
        return datasetname

    def _fullsetname(self, datasetname):
        return datasetname.rsplit('_', 1)[0]

    def _jobname(self, datasetname, fullsetname):
        return '{}-{}'.format(datasetname,
                str(self._dataset_job_counter[fullsetname]).zfill(4)).replace('_', '')

    def _s3_outputpath(self, datasetname, fullsetname):
        return '{}-{}.json'.format(fullsetname,
            str(self._dataset_job_counter[fullsetname]).zfill(4))

    def _s3_basedir(self):
        return "%s/%s/testoutputs/higgs4lbucket/%s/eventselection" % (
                self.storage_type, self.bucket, self.run)

    def _kube_submit(self, manifests):
        try:
            utils.create_from_yaml(self.api_client, 'cm-runjob.yaml')
        except Exception as e:
            pass
        for i in range(0, len(manifests), self.limit):
            yaml = ''
            for m in manifests[i:i + self.limit]:
                yaml += "\n---\n%s" % m
            f = open('/tmp/{0}'.format(self.cluster), 'w')
            f.write(yaml)
            f.close()
            utils.create_from_yaml(self.api_client, '/tmp/{0}'.format(self.cluster))

    def _cleanup_jobs(self):
        result = self.batch_client.delete_collection_namespaced_job(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = self.batch_client.delete_collection_namespaced_job(
                    self.namespace, limit = self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')

    def _cleanup_pods(self):
        result = self.core_client.delete_collection_namespaced_pod(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = self.core_client.delete_collection_namespaced_pod(
                    self.namespace, limit = self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
      
    def _get_jobs(self):
        result = self.batch_client.list_namespaced_job(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        jobs = result['items']
        while c:
            result = self.batch_client.list_namespaced_job(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            jobs.extend(result['items'])
        return jobs

    def _get_pods(self):
        result = self.core_client.list_namespaced_pod(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        pods = result['items']
        while c:
            result = self.core_client.list_namespaced_pod(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            pods.extend(result['items'])

        rv = result['metadata']['resource_version']
        return pods, rv

    def _dataset_files(self):
        if self.dataset_pattern:
            return glob.glob("datasets_s3/%s" % self.dataset_pattern)
        elif self.dataset_mapping:
            return self.dataset_mapping[self.dataset_index]['datasets']
        return []

    def cleanup(self):
        try:
            self.core_client.delete_namespaced_config_map('runjob', self.namespace)
            self.core_client.delete_namespaced_config_map('getfile', self.namespace)
        except:
            pass
        self._cleanup_jobs()
        self._cleanup_pods()

    def prepare(self):
        try:
            utils.create_from_yaml(self.api_client, 'ds-prepull.yaml')
        except Exception as exc:
            pass

    def status(self, fn=None):
        self._pods = {'Pulling': [], 'Running': [], 'Pending': [], 'Succeeded': [], 'Failed': [], 'Unknown': []}
        pods, rv = self._get_pods()
        for pod in pods:
            pod_name = pod['metadata']['name']
            phase = pod['status']['phase']
            prepull = None
            if pod['status']['init_container_statuses']:
                prepull = pod['status']['init_container_statuses'][0]['state']['running']
            for p in self._pods.keys():
                try:
                    self._pods[p].remove(pod_name)
                except:
                    pass
            if prepull:
                self._pods['Pulling'].append(pod_name)
            else:
                self._pods[phase].append(pod_name)

        result = {}
        for p in self._pods.keys():
            result[p] = len(self._pods[p])

        if not fn:
            return result

        fn(result)
        w = watch.Watch()
        api = self.core_client
        for item in w.stream(
            api.list_namespaced_pod, namespace=self.namespace,
                timeout_seconds=0, resource_version=rv):
            pod_name = item['object'].metadata.name
            phase = item['object'].status.phase
            prepull = None
            if item['object'].status.init_container_statuses:
                prepull = item['object'].status.init_container_statuses[0].state.running
            t = item['type']
            for p in self._pods.keys():
                try:
                    self._pods[p].remove(pod_name)
                except:
                    pass
            if t != 'DELETED':
                if prepull:
                    self._pods['Pulling'].append(pod_name)
                else:
                    self._pods[phase].append(pod_name)
            result = {}
            for p in self._pods.keys():
                result[p] = len(self._pods[p])

            fn(result)

    def submit(self):
        s3_basedir = self._s3_basedir()
        manifests = []

        dataset_files = self._dataset_files()
        for datasetfile in dataset_files:
            datasetname = self._datasetname(datasetfile)
            fullsetname = self._fullsetname(datasetname)
            is_data = False
            if 'cms_run' in fullsetname: #is data and not simulation
                lumi_data = json.load(open('lumi/{}.json'.format(fullsetname)))
                is_data = True
            else:
                lumi_data = {}
            if not os.path.isfile(datasetfile):
                continue
            for eventfile in open(datasetfile).readlines():
                eventfile = eventfile.strip()
                eospath = eventfile.replace('s3/higgs-demo','root://eospublic.cern.ch/')
                lumi_value_for_file = lumi_data.get(eospath)
                year_for_file = None
                stream_for_file = None
                lumi_data_for_file = None
                if is_data:
                    config = "/configs/demoanalyzer_cfg_level4data.py"
                    if '2012' in eventfile:
                        year_for_file = 2012
                    if '2011' in eventfile:
                        year_for_file = 2011
                    if 'DoubleEl' in eventfile:
                        stream_for_file = 'el_stream'
                    if 'DoubleMu' in eventfile:
                        stream_for_file = 'mu_stream'
                    if all(x is not None for x in [year_for_file, stream_for_file, lumi_value_for_file]):
                        lumi_data_for_file = {
                            'stream': '{}_{}'.format(stream_for_file, year_for_file),
                            'value': lumi_value_for_file
                        }
                    config_json_file = self._jsonfile(year_for_file)
                else:
                    config = "/configs/demoanalyzer_cfg_level4MC.py"
                    config_json_file = ''

                self._dataset_job_counter.setdefault(fullsetname, 0)
                cur = self._dataset_job_counter[fullsetname]
                self._dataset_job_counter[fullsetname] += 1
                jobname = self._jobname(datasetname, fullsetname)
                s3_outputpath = self._s3_outputpath(datasetname, fullsetname)

                params = {
                    'datasetname': datasetname, 'namespace': self.namespace,
                    'fullsetname': fullsetname, 'eventfile': eventfile.strip().replace('s3', self.storage_type).replace('higgs-demo', self.bucket),
                    'jobname': jobname, 's3_outputpath': s3_outputpath,
                    'config': config, 'jsonfile': config_json_file,
                    'image': self.image, 's3_basedir': s3_basedir,
                    'cpu_limit': self.cpu_limit, 'backoff_limit': self.backoff_limit,
                    'multipart_threads': self.multipart_threads,
                    'output_file': self.output_file,
                    'output_json_file': self.output_json_file,
                    'redis_host': self.redis_host,
                    'download_max_kb': self.download_max_kb,
                    'upload_max_kb': self.upload_max_kb,
                    'gs_project_id': self.gcs_project_id,
                    'lumi_data': json.dumps(lumi_data_for_file),
                    'dpath': self.dpath, 'ftype': self.ftype
                }
                for st in ('s3', 'gs'):
                    params["%s_access_key" % st] = ''
                    params["%s_secret_key" % st] = ''
                    params["%s_host" % st] = ''
                params["%s_access_key" % self.storage_type] = self.access_key
                params["%s_secret_key" % self.storage_type] = self.secret_key
                params["%s_host" % self.storage_type] = self.storage_host

                manifests.append(self._job_manifest(**params))

        self._kube_submit(manifests)


class HiggsDemoCli(App):

    def __init__(self):
        super(HiggsDemoCli, self).__init__(
            description='higgs demo app',
            version='0.1.0',
            command_manager=CommandManager('higgs.demo'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def _higgs_demo(parsed_args):
    return HiggsDemo(**parsed_args.__dict__)


def main(argv=sys.argv[1:]):
    myapp = HiggsDemoCli()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


