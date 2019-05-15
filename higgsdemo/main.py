import glob
import joblib
import os
import re
import sys
import yaml
import traceback
from string import Template

from cliff.app import App
from cliff.commandmanager import CommandManager
from kubernetes import client
from kubernetes import config as kube_config
from kubernetes import utils
from kubernetes import watch


class HiggsDemo(object):

    def __init__(self, dataset_pattern='*Higgs*', config='', namespace='default',
            image='lukasheinrich/cms-higgs-4l-full', access_key='',
            secret_key='', storage_type='s3', storage_host='',
            cpu_limit='1000m', bucket='higgs-demo-nl', output_bucket='higgs-demo-nl',
            backoff_limit=5,  multipart_threads=10, output_file='/tmp/output.root',
            output_json_file='/tmp/output.json', run='run6', limit=1000, dry = False, cluster = None):
        super(HiggsDemo, self).__init__()
        self.dataset_pattern = dataset_pattern
        self.config = config
        self.dry = dry
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
        self.run = run
        self.limit = limit
        self._dataset_job_counter = {}
        self.default_cluster_name = cluster or None

    def _connect_cluster(self, cluster_name):
        kube_config.load_kube_config(context = cluster_name)
        api_client = client.ApiClient()
        batch_client = client.BatchV1Api()
        batch_client.api_client = api_client

        core_client = client.CoreV1Api()
        core_client.api_client = api_client

        clients = {
            'api': api_client,
            'batch': batch_client,
            'core': core_client
        }
        return clients

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

    def _jsonfile(self, config):
        jsonfile = ''
        if 'data' in config:
            parts = config.split(':')
            config = parts[0]
            jsonfile = {
                '2011': '/json_files/Cert_160404-180252_7TeV_ReRecoNov08_Collisions11_JSON.txt',
                '2012': '/json_files/Cert_190456-208686_8TeV_22Jan2013ReReco_Collisions12_JSON.txt'
            }[parts[1]]
        return jsonfile

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

    def _create_from_yaml(self,filename, cluster_name):
        cl = self._connect_cluster(cluster_name)['api']
        if self.dry:
            print('dry-run {}'.format(filename))
            return
        self._connect_cluster(cluster_name)
        utils.create_from_yaml(cl, filename)

    def _kube_submit(self, manifests, cluster_name):
        self._create_from_yaml('cm-runjob.yaml', cluster_name)
        for i in range(0, len(manifests), self.limit):
            yaml = ''
            for m in manifests[i:i + self.limit]:
                yaml += "\n---\n%s" % m
            f = open('/tmp/yaml', 'w')
            f.write(yaml)
            f.close()
            self._create_from_yaml('/tmp/yaml', cluster_name)

    def _cleanup_cm(self, cluster_name):
        cl = self._connect_cluster(cluster_name)['core']
        cl.delete_namespaced_config_map('runjob', self.namespace)

    def _cleanup_jobs(self, cluster_name):
        cl = self._connect_cluster(cluster_name)['batch']
        result = cl.delete_collection_namespaced_job(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = cl.BatchV1Api().delete_collection_namespaced_job(
                    namespace, limit = limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')

    def _cleanup_pods(self, cluster_name):
        cl = self._connect_cluster(cluster_name)['core']
        result = cl.delete_collection_namespaced_pod(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = cl.delete_collection_namespaced_pod(
                    namespace, limit = limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
      
    def _get_jobs(self, cluster_name):
        cl = self._connect_cluster(cluster_name)['batch']
        result = cl.list_namespaced_job(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        jobs = result['items']
        while c:
            result = cl.list_namespaced_job(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            jobs.extend(result['items'])
        return jobs

    def _get_pods(self, cluster_name):
        cl = self._connect_cluster(cluster_name)['core']
        assert cl.api_client
        result = cl.list_namespaced_pod(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        pods = result['items']
        while c:
            result = cl.list_namespaced_pod(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            pods.extend(result['items'])

        rv = result['metadata']['resource_version']
        return pods, rv

    def cleanup(self, cluster_name = None):
        cluster_name = cluster_name or self.default_cluster_name
        self._cleanup_cm(cluster_name)
        self._cleanup_jobs(cluster_name)
        self._cleanup_pods(cluster_name)

    def prepare(self, cluster_name = None):
        cluster_name = cluster_name or self.default_cluster_name
        self._create_from_yaml('ds-prepull.yaml', cluster_name)

    def status(self, cluster_name = None):
        cluster_name = cluster_name or self.default_cluster_name
        result = {'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'jobs': {'succeeded': 0}, 'pods': {}}
        jobs = self._get_jobs(cluster_name)
        for job in jobs:
            if 'succeeded' in job['status'] and job['status']['succeeded'] == 1:
               result['jobs']['succeeded'] += 1
        result['jobs']['total'] = len(jobs)

        pods = self._get_pods(cluster_name)
        for pod in pods:
            pod_name = pod['metadata']['name']
            for p in self._pods.keys():
                try:
                    self._pods[p].remove(pod_name)
                except:
                    pass
            phase = pod['status']['phase']
            self._pods[phase].append(pod_name)

        result = {}
        for p in self._pods.keys():
            result[p] = len(self._pods[p])

        if not fn:
            return result

        fn(result)
        w = watch.Watch()
        api = client.CoreV1Api()
        for item in w.stream(
            api.list_namespaced_pod, namespace=self.namespace,
                timeout_seconds=0, resource_version=rv):
            pod_name = item['object'].metadata.name
            phase = item['object'].status.phase
            t = item['type']
            for p in self._pods.keys():
                try:
                    self._pods[p].remove(pod_name)
                except:
                    pass
            if t != 'DELETED':
                self._pods[phase].append(pod_name)
            result = {}
            for p in self._pods.keys():
                result[p] = len(self._pods[p])

            fn(result)

    def submit(self, cluster_name = None):
        cluster_name = cluster_name or self.default_cluster_name
        s3_basedir = self._s3_basedir()
        manifests = []

        for datasetfile in glob.glob("datasets_s3/%s" % self.dataset_pattern):
            datasetname = self._datasetname(datasetfile)
            fullsetname = self._fullsetname(datasetname)

            for eventfile in open(datasetfile).readlines():
                self._dataset_job_counter.setdefault(fullsetname, 0)
                cur = self._dataset_job_counter[fullsetname]
                self._dataset_job_counter[fullsetname] += 1
                jobname = self._jobname(datasetname, fullsetname)
                s3_outputpath = self._s3_outputpath(datasetname, fullsetname)

                params = {
                    'datasetname': datasetname, 'namespace': self.namespace,
                    'fullsetname': fullsetname, 'eventfile': eventfile.strip().replace('s3', self.storage_type).replace('higgs-demo', self.bucket),
                    'jobname': jobname, 's3_outputpath': s3_outputpath,
                    'config': self.config, 'jsonfile': self._jsonfile(self.config),
                    'image': self.image, 's3_basedir': s3_basedir,
                    'cpu_limit': self.cpu_limit, 'backoff_limit': self.backoff_limit,
                    'multipart_threads': self.multipart_threads,
                    'output_file': self.output_file, 'output_json_file': self.output_json_file
                }
                for st in ('s3', 'gs'):
                    params["%s_access_key" % st] = ''
                    params["%s_secret_key" % st] = ''
                    params["%s_host" % st] = ''
                params["%s_access_key" % self.storage_type] = self.access_key
                params["%s_secret_key" % self.storage_type] = self.secret_key
                params["%s_host" % self.storage_type] = self.storage_host

                manifests.append(self._job_manifest(**params))
        if not manifests:
            raise RuntimeError('no manifests to submit')
        self._kube_submit(manifests, cluster_name)


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


