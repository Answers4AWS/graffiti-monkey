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


def _fail(message="Unknown failure", code=1):
    log.error(message)
    sys.exit(code)


def run():
    parser = argparse.ArgumentParser(description='Propagates tags from AWS EC2 instances to EBS volumes, and then to EBS snapshots. This makes it much easier to find things down the road.')
    parser.add_argument('--region', metavar='REGION', 
                        help='the region to tag things in (default is current region of EC2 instance this is running on). E.g. us-east-1')
    parser.add_argument('--verbose', '-v', action='count', 
                        help='enable verbose output (-vvv for more)')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__,
                        help='display version number and exit')
    args = parser.parse_args()
    
    Logging().configure(args.verbose)

    log.debug("CLI parse args: %s", args)

    if args.region:
        region = args.region
    else:
        # If no region was specified, assume this is running on an EC2 instance
        # and work out what region it is in
        log.debug("Figure out which region I am running in...")
        instance_metadata = get_instance_metadata(timeout=5)
        log.debug('Instance meta-data: %s', instance_metadata)
        if not instance_metadata:
            _fail('Could not determine region. This script is either not running on an EC2 instance (in which case you should use the --region option), or the meta-data service is down')
        
        region = instance_metadata['placement']['availability-zone'][:-1]
        log.debug("Running in region: %s", region)

    try:
        monkey = GraffitiMonkey(region)
        
        monkey.propagate_tags()
        
    except GraffitiMonkeyException as e:
        _fail(e.message)
    
    log.info('Graffiti Monkey completed successfully!')
    sys.exit(0)
    
