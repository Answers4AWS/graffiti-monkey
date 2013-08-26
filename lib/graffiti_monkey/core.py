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

import logging
import pprint

from boto import ec2

pp = pprint.PrettyPrinter(depth=2)

__all__ = ('GraffitiMonkey', 'Logging')
log = logging.getLogger(__name__)


class GraffitiMonkey(object):
    def __init__(self, region):
        self._region = region
        
        log.info("Connecting to region %s", self._region)
        self._conn = ec2.connect_to_region(self._region)            

    
    def tag(self):
        ''' Loops through all EBS volumes and creates snapshots of them '''
        
        log.info('Tagging')
#        volumes = self._conn.get_all_volumes()
#        log.info('Found %d volumes', len(volumes))
#        for volume in volumes:            
#            description_parts = [self._prefix]
#            description_parts.append(volume.id)
#            if volume.attach_data.instance_id:
#                description_parts.append(volume.attach_data.instance_id)
#            if volume.attach_data.device:
#                description_parts.append(volume.attach_data.device)
#            description = ' '.join(description_parts)
#            log.info('Creating snapshot of %s: %s', volume.id, description)
#            volume.create_snapshot(description)
#        return True






class Logging(object):
    # Logging formats
    _log_simple_format = '%(asctime)s [%(levelname)s] %(message)s'
    _log_detailed_format = '%(asctime)s [%(levelname)s] [%(name)s(%(lineno)s):%(funcName)s] %(message)s'
    
    def configure(self, verbosity = None):
        ''' Configure the logging format and verbosity '''
        
        # Configure our logging output
        if verbosity >= 2:
            logging.basicConfig(level=logging.DEBUG, format=self._log_detailed_format, datefmt='%F %T')
        elif verbosity >= 1:
            logging.basicConfig(level=logging.INFO, format=self._log_detailed_format, datefmt='%F %T')
        else:
            logging.basicConfig(level=logging.INFO, format=self._log_simple_format, datefmt='%F %T')
    
        # Configure Boto's logging output
        if verbosity >= 4:
            logging.getLogger('boto').setLevel(logging.DEBUG)
        elif verbosity >= 3:
            logging.getLogger('boto').setLevel(logging.INFO)
        else:
            logging.getLogger('boto').setLevel(logging.CRITICAL)    
    
