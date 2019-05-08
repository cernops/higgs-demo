import logging
import main

from cliff.command import Command

class Submit(Command):
    "Submits the higgs demo to the currently configured cluster."

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Submit, self).get_parser(prog_name)
        parser.add_argument('--config', dest='config',
                            default='/configs/demoanalyzer_cfg_level4MC.py',
                            help='the demo analyzer config file')
        parser.add_argument('--dataset-pattern', dest='dataset_pattern',
                            default='*Higgs*',
                            help='the pattern of datasets to process')
        parser.add_argument('--run', dest='run',
                            default='run6',
                            help='the name of the demo run')
        parser.add_argument('--namespace', dest='namespace',
                            default='default',
                            help='the kube namespace to use')
        parser.add_argument('--image', dest='image',
                            default='lukasheinrich/cms-higgs-4l-full',
                            help='the docker image to use for jobs')
        parser.add_argument('--s3-access-key', dest='s3_access_key',
                            default='',
                            help='the s3 access key')
        parser.add_argument('--s3-secret-key', dest='s3_secret_key',
                            default='',
                            help='the s3 secret key')
        parser.add_argument('--s3-host', dest='s3_host',
                            default='s3',
                            help='the s3 host')
        parser.add_argument('--gcs-access-key', dest='gcs_access_key',
                            default='',
                            help='the gcs access key')
        parser.add_argument('--gcs-secret-key', dest='gcs_secret_key',
                            default='',
                            help='the gcs secret key')
        parser.add_argument('--gcs-host', dest='gcs_host',
                            default='gcs',
                            help='the gcs host')
        parser.add_argument('--bucket', dest='bucket',
                            default='higgs-demo',
                            help='the name of the bucket holding the data')
        parser.add_argument('--output-bucket', dest='output_bucket',
                            default='higgs-demo',
                            help='the name of the bucket to write the output')
        parser.add_argument('--cpu-limit', dest='cpu_limit',
                            default="1000m",
                            help='the kube cpu request / limit')
        parser.add_argument('--backoff-limit', dest='backoff_limit',
                            default=5,
                            help='the kube job backoff limit')
        parser.add_argument('--mc-threads', dest='multipart_threads',
                            default=10,
                            help='the number of minio threads')
        parser.add_argument('--output-file', dest='output_file',
                            default='/tmp/output.root',
                            help='the local path for the output file')
        parser.add_argument('--output-json-file', dest='output_json_file',
                            default='/tmp/output.json',
                            help='the local path for the output json file')
        return parser

    def take_action(self, parsed_args):
        hd = main._higgs_demo(parsed_args)
        hd.submit()
        

class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')
