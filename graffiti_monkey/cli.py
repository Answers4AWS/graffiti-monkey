# Copyright 2013 Answers for AWS LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import sys

from graffiti_monkey.core import GraffitiMonkey, Logging
from graffiti_monkey import __version__
from graffiti_monkey.exceptions import GraffitiMonkeyException

from boto.utils import get_instance_metadata


__all__ = ('run', )
log = logging.getLogger(__name__)


class GraffitiMonkeyCli(object):
    def __init__(self):
        self.region = None
        self.profile = None
        self.monkey = None
        self.args = None
        self.config = {"_instance_tags_to_propagate": ['Name'],
                       "_volume_tags_to_propagate": ['Name', 'instance_id', 'device'],
                       "_volume_tags_to_be_set": [],
                       "_snapshot_tags_to_be_set": [],
                       }
        self.dryrun = False
        self.append = False
        self.volumes = None
        self.snapshots = None
        self.novolumes = False
        self.nosnapshots = False

    @staticmethod
    def _fail(message="Unknown failure", code=1):
        log.error(message)
        sys.exit(code)

    def get_argv(self):
        """
        The parse_args method from ArgumentParser expects to not get the script title when arguments are passed to the
        method. So the first element is omitted.
        """
        return sys.argv[1:]

    def set_cli_args(self):
        parser = argparse.ArgumentParser(description='Propagates tags from AWS EC2 instances to EBS volumes, and then to EBS snapshots. This makes it much easier to find things down the road.')
        parser.add_argument('--region', metavar='REGION',
                            help='the region to tag things in (default is current region of EC2 instance this is running on). E.g. us-east-1')
        parser.add_argument('--profile', metavar='PROFILE',
                            help='the profile (credentials) to use to connect to EC2')
        parser.add_argument('--verbose', '-v', action='count',
                            help='enable verbose output (-vvv for more)')
        parser.add_argument('--version', action='version', version='%(prog)s ' + __version__,
                            help='display version number and exit')
        parser.add_argument('--config', '-c', nargs="?", type=argparse.FileType('r'),
                        default=None, help="Give a yaml configuration file")
        parser.add_argument('--dryrun', action='store_true',
                            help='dryrun only, display tagging actions but do not perform them')
        parser.add_argument('--append', action='store_true',
                            help='append propagated tags to existing tags (up to a total of ten tags)')
        parser.add_argument('--volumes', action='append',
                            help='volume-ids to tag')
        parser.add_argument('--snapshots', action='append',
                            help='snapshot-ids to tag'),
        parser.add_argument('--novolumes', action='store_true',
                            help='do not perform volume tagging')
        parser.add_argument('--nosnapshots', action='store_true',
                            help='do not perform snapshot tagging')
        self.args = parser.parse_args(self.get_argv())

    @staticmethod
    def fail_due_to_bad_config_file(self):
        self._fail("Something went wrong reading the passed yaml config file. "
                          "Make sure to use valid yaml syntax. "
                          "Also the start of the file should not be marked with '---'.", 6)

    def set_config(self):
        if self.args.config:
            try:
                import yaml
            except:
                log.error("When the config parameter is used, you need to have the python PyYAML library.")
                log.error("It can be installed with pip `pip install PyYAML`.")
                sys.exit(5)

            try:
                #TODO: take default values and these can be overwritten by config
                self.config = yaml.load(self.args.config)
                if self.config is None:
                    self.fail_due_to_bad_config_file()
            except:
                self.fail_due_to_bad_config_file()



    def set_region(self):
        if "region" in self.config.keys():
            self.region = self.config["region"]
        elif self.args.region:
            self.region = self.args.region
        else:
            # If no region was specified, assume this is running on an EC2 instance
            # and work out what region it is in
            log.debug("Figure out which region I am running in...")
            instance_metadata = get_instance_metadata(timeout=5)
            log.debug('Instance meta-data: %s', instance_metadata)
            if not instance_metadata:
                GraffitiMonkeyCli._fail('Could not determine region. This script is either not running on an EC2 instance (in which case you should use the --region option), or the meta-data service is down')

            self.region = instance_metadata['placement']['availability-zone'][:-1]
        log.debug("Running in region: %s", self.region)

    def set_profile(self):
        if "profile" in self.config.keys():
            self.profile = self.config["profile"]
        elif self.args.profile:
            self.profile = self.args.profile
        else:
            self.profile = 'default'
        log.debug("Using profile: %s", self.profile)

    def set_dryrun(self):
        self.dryrun = self.args.dryrun

    def set_append(self):
        self.append = self.args.append

    def set_volumes(self):
        if "_volumes_to_tag" in self.config.keys():
            self.volumes = self.config["_volumes_to_tag"]
        elif self.args.volumes:
            self.volumes = self.args.volumes

    def set_snapshots(self):
        if "_snapshots_to_tag" in self.config.keys():
            self.snapshots = self.config["_snapshots_to_tag"]
        elif self.args.snapshots:
            self.snapshots = self.args.snapshots

    def set_novolumes(self):
        self.novolumes = self.args.novolumes

    def set_nosnapshots(self):
        self.nosnapshots = self.args.nosnapshots

    def initialize_monkey(self):
        self.monkey = GraffitiMonkey(self.region,
                                     self.profile,
                                     self.config["_instance_tags_to_propagate"],
                                     self.config["_volume_tags_to_propagate"],
                                     self.config["_volume_tags_to_be_set"],
                                     self.config["_snapshot_tags_to_be_set"],
                                     self.dryrun,
                                     self.append,
                                     self.volumes,
                                     self.snapshots,
                                     self.novolumes,
                                     self.nosnapshots
                                     )

    def start_tags_propagation(self):
        self.monkey.propagate_tags()

    def exit_succesfully(self):
        log.info('Graffiti Monkey completed successfully!')
        sys.exit(0)

    def run(self):
        self.set_cli_args()

        Logging().configure(self.args.verbose)
        log.debug("CLI parse args: %s", self.args)

        self.set_config()
        self.set_region()
        self.set_profile()
        self.set_dryrun()
        self.set_append()
        self.set_volumes()
        self.set_snapshots()
        self.set_novolumes()
        self.set_nosnapshots()

        try:
            self.initialize_monkey()
            self.start_tags_propagation()

        except GraffitiMonkeyException as e:
            GraffitiMonkeyCli._fail(e.message)

        self.exit_succesfully()


def run():
    cli = GraffitiMonkeyCli()
    cli.run()
