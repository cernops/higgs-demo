import glob
import os
import re
import sys

from string import Template

from cliff.app import App
from cliff.commandmanager import CommandManager


class HiggsDemo(object):

    def __init__(self, dataset_pattern='*Higgs*', config='',
            image='lukasheinrich/cms-higgs-4l-full', s3_access_key='',
            s3_secret_key='', s3_host='s3', gcs_access_key='', gcs_secret_key='',
            gcs_host='gs', cpu_limit='1000m', backoff_limit=5,
            multipart_threads=10):
        super(HiggsDemo, self).__init__()
        self.dataset_pattern = dataset_pattern
        self.config = config
        self.image = image
        self.s3_access_key = s3_access_key
        self.s3_secret_key = s3_secret_key
        self.s3_host = s3_host
        self.gcs_access_key = gcs_access_key
        self.gcs_secret_key = gcs_secret_key
        self.gcs_host = gcs_host
        self.cpu_limit = cpu_limit
        self.backoff_limit = backoff_limit
        self.multipart_threads = multipart_threads

    def _job_template(self):
        content = ''
        with open('job.yaml', 'r') as job_file:
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

    def submit(self):
        for datasetfile in glob.glob("datasets_s3/%s" % self.dataset_pattern):
            datasetname = self._datasetname(datasetfile)
            fullsetname = self._fullsetname(datasetname)

            for eventfile in open(datasetfile).readlines():
                manifest = self._job_manifest(datasetname=datasetname,
                        fullsetname=fullsetname, eventfile=eventfile.strip(),
                        config=self.config,
                        jsonfile=self._jsonfile(self.config),
                        image=self.image,
                        s3_access_key=self.s3_access_key,
                        s3_secret_key=self.s3_secret_key,
                        s3_host=self.s3_host,
                        gcs_access_key=self.gcs_access_key,
                        gcs_secret_key=self.gcs_secret_key,
                        gcs_host=self.gcs_host,
                        cpu_limit=self.cpu_limit,
                        backoff_limit=self.backoff_limit,
                        multipart_threads=self.multipart_threads)
                print manifest


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
    return HiggsDemo(dataset_pattern=parsed_args.dataset_pattern,
            config=parsed_args.config, image=parsed_args.image,
            s3_access_key=parsed_args.s3_access_key,
            s3_secret_key=parsed_args.s3_secret_key,
            s3_host=parsed_args.s3_host,
            gcs_access_key=parsed_args.gcs_access_key,
            gcs_secret_key=parsed_args.gcs_secret_key,
            gcs_host=parsed_args.gcs_host,
            multipart_threads=parsed_args.multipart_threads
            )


def main(argv=sys.argv[1:]):
    myapp = HiggsDemoCli()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))


