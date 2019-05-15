import logging
import higgsdemo.main as demo
import time

from cliff.command import Command
from datetime import datetime
from jupyterlab.labapp import main as jupyterlab_main


class Cleanup(Command):
    "clean up a higgs demo deployment in the currently configured cluster"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Cleanup, self).get_parser(prog_name)
        parser.add_argument('--namespace', dest='namespace',
                            default='default',
                            help='the kube namespace to use')
        parser.add_argument('--limit', dest='limit', type=int,
                            default=1000,
                            help='the limit of objects per kube api query')
        parser.add_argument('--cluster', dest='cluster',
                            default=None,
                            help='the cluster context to be used')
        return parser

    def take_action(self, parsed_args):
        hd = demo._higgs_demo(parsed_args)
        hd.cleanup()


class Submit(Command):
    "submit the higgs demo to the currently configured cluster"

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
        parser.add_argument('--access-key', dest='access_key',
                            default='',
                            help='the storage access key')
        parser.add_argument('--secret-key', dest='secret_key',
                            default='',
                            help='the storage secret key')
        parser.add_argument('--storage-type', dest='storage_type',
                            default='s3',
                            help='the type of storage (s3 or gcs)')
        parser.add_argument('--storage-host', dest='storage_host',
                            default='',
                            help='the storage host(for s3 or gcs)')
        parser.add_argument('--bucket', dest='bucket',
                            default='higgs-demo-nl',
                            help='the name of the bucket holding the data')
        parser.add_argument('--output-bucket', dest='output_bucket',
                            default='higgs-demo-nl',
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
        parser.add_argument('--download-max-kb', dest='download_max_kb',
                            default=10000,
                            help='the max download speed per file in kb')
        parser.add_argument('--upload-max-kb', dest='upload_max_kb',
                            default=5000,
                            help='the max upload speed per file in kb')
        parser.add_argument('--redis-host', dest='redis_host',
                            default='10.0.0.4',
                            help='the redis host to publish output data')
        parser.add_argument('--gcs-project-id', dest='gcs_project_id',
                            default='nimble-valve-236407',
                            help='the gcs project id being used')
        parser.add_argument('--limit', dest='limit', type=int,
                            default=1000,
                            help='the limit of objects per kube api query')
        parser.add_argument('--cluster', dest='cluster',
                            default=None,
                            help='the cluster context to be used')
        return parser

    def take_action(self, parsed_args):
        hd = demo._higgs_demo(parsed_args)
        hd.submit()
        

class Watch(Command):
    "watch status of the higgs demo deployment in the currently configured cluster"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Watch, self).get_parser(prog_name)
        parser.add_argument('--namespace', dest='namespace',
                            default='default',
                            help='the kube namespace to use')
        parser.add_argument('--cluster', dest='cluster',
                            default=None,
                            help='the cluster context to be used')
        return parser

    def take_action(self, parsed_args):
        hd = demo._higgs_demo(parsed_args)
        start = datetime.now()
        def fn(r):
            now = datetime.now()
            print("%s %s %s" % ((now-start).total_seconds(), now, r))
        hd.status(fn=fn)
        

class Prepare(Command):
    "prepare the cluster for a higgs demo deployment (image pull, ...)"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Prepare, self).get_parser(prog_name)
        parser.add_argument('--namespace', dest='namespace',
                            default='default',
                            help='the kube namespace to use')
        parser.add_argument('--limit', dest='limit', type=int,
                            default=1000,
                            help='the limit of objects per kube api query')
        parser.add_argument('--cluster', dest='cluster',
                            default=None,
                            help='the cluster context to be used')
        return parser

    def take_action(self, parsed_args):
        hd = demo._higgs_demo(parsed_args)
        hd.prepare()


class Notebook(Command):
    "launch the demo jupyter notebook"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Notebook, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        jupyterlab_main()


class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')
