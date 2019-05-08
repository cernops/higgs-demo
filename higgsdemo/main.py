import glob
import joblib
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


class HiggsDemo(object):

    def __init__(self, dataset_pattern='*Higgs*', config='', namespace='default',
            image='lukasheinrich/cms-higgs-4l-full', access_key='',
            secret_key='', storage_type='s3', storage_host='',
            cpu_limit='1000m', bucket='higgs-demo', output_bucket='higgs-demo',
            backoff_limit=5,  multipart_threads=10, output_file='/tmp/output.root',
            output_json_file='/tmp/output.json', run='run6', limit='1000'):
        super(HiggsDemo, self).__init__()
        self.dataset_pattern = dataset_pattern
        self.config = config
        self.namespace = namespace
        self.image = image
        self.access_key = access_key
        self.secret_key = secret_key
        self.storage_type = storage_type
        self.storage_host = storage_host
        if self.storage_host == '':
            self.storage_host = self.storage_type
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

        kube_config.load_kube_config()
        self.kube_client = client.ApiClient()

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


    def _kube_submit(self, manifests):
        utils.create_from_yaml(self.kube_client, 'cm-runjob.yaml')
        for m in manifests:
            f = open('/tmp/yaml', 'w')
            f.write(m)
            f.close()
            utils.create_from_yaml(self.kube_client, '/tmp/yaml')

    def _cleanup_jobs(self):
        result = client.BatchV1Api().delete_collection_namespaced_job(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = client.BatchV1Api().delete_collection_namespaced_job(
                    namespace, limit = limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')

    def _cleanup_pods(self):
        result = client.CoreV1Api().delete_collection_namespaced_pod(
                self.namespace, limit = self.limit).to_dict()
        c = result['metadata'].get('_continue')
        while c:
            result = client.CoreV1Api().delete_collection_namespaced_pod(
                    namespace, limit = limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
      
    def _get_jobs(self):
        result = client.BatchV1Api().list_namespaced_job(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        jobs = result['items']
        while c:
            result = client.BatchV1Api().list_namespaced_job(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            jobs.extend(result['items'])
        return jobs

    def _get_pods(self):
        result = client.CoreV1Api().list_namespaced_pod(
                self.namespace, limit=self.limit).to_dict()
        c = result['metadata'].get('_continue')
        pods = result['items']
        while c:
            result = client.CoreV1Api().list_namespaced_pod(
                self.namespace, limit=self.limit, _continue = c).to_dict()
            c = result['metadata'].get('_continue')
            pods.extend(result['items'])
        return pods

    def cleanup(self):
        try:
            client.CoreV1Api().delete_namespaced_config_map('runjob', self.namespace)
        except:
            pass
        self._cleanup_jobs()
        self._cleanup_pods()

    def status(self):
        result = {'jobs': {'succeeded': 0}, 'pods': {}}
        jobs = self._get_jobs()
        for job in jobs:
            if 'succeeded' in job['status'] and job['status']['succeeded'] == 1:
               result['jobs']['succeeded'] += 1
        result['jobs']['total'] = len(jobs)

        pods = self._get_pods()
        for pod in pods:
            phase = pod['status']['phase']
            result['pods'].setdefault(phase, 0)
            result['pods'][phase] += 1
        result['pods']['total'] = len(pods)

        return result

    def submit(self):
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
                    'fullsetname': fullsetname, 'eventfile': eventfile.strip(),
                    'jobname': jobname, 's3_outputpath': s3_outputpath,
                    'config': self.config, 'jsonfile': self._jsonfile(self.config),
                    'image': self.image, 's3_basedir': s3_basedir,
                    'cpu_limit': self.cpu_limit, 'backoff_limit': self.backoff_limit,
                    'multipart_threads': self.multipart_threads,
                    'output_file': self.output_file, 'output_json_file': self.output_json_file
                }
                for st in ('s3', 'gcs'):
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


