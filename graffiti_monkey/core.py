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

from cache import Memorize
from exceptions import *

import boto
from boto import ec2 

__all__ = ('GraffitiMonkey', 'Logging')
log = logging.getLogger(__name__)


class GraffitiMonkey(object):
    def __init__(self, region):
        # This list of tags associated with an EC2 instance to propagate to 
        # attached EBS volumes
        self._instance_tags_to_propagate = ['Name']
        
        # This is a list of tags associated with a volume to propagate to
        # a snapshot created from the volume 
        self._volume_tags_to_propagate = ['Name', 'instance_id', 'device']
        
        # The region to operate in
        self._region = region
        
        log.info("Connecting to region %s", self._region)
        try:
            self._conn = ec2.connect_to_region(self._region)
        except boto.exception.NoAuthHandlerFound:
            raise GraffitiMonkeyException('No AWS credentials found - check your credentials')

    
    def propagate_tags(self):
        ''' Propagates tags by copying them from EC2 instance to EBS volume, and
        then to snapshot '''
        
        self.tag_volumes()
        self.tag_snapshots()
            

    def tag_volumes(self):
        ''' Gets a list of all volumes, and then loops through them tagging
        them '''
        
        log.info('Getting list of all volumes')
        volumes = self._conn.get_all_volumes()
        log.info('Found %d volumes', len(volumes))
        for volume in volumes:
            if volume.status != 'in-use':
                log.debug('Skipping %s as it is not attached to an EC2 instance, so there is nothing to propagate', volume.id)
                continue
            self.tag_volume(volume)


    def tag_volume(self, volume):
        ''' Tags a specific volume '''
                
        instance_id = None
        if volume.attach_data.instance_id:
            instance_id = volume.attach_data.instance_id
        device = None
        if volume.attach_data.device:
            device = volume.attach_data.device
        
        instance_tags = self._get_resource_tags(instance_id)
        
        tags_to_set = {}
        for tag_name in self._instance_tags_to_propagate:
            log.debug('Trying to propagate instance tag: %s', tag_name)
            if tag_name in instance_tags:
                value = instance_tags[tag_name]
                tags_to_set[tag_name] = value

        # Additional tags
        tags_to_set['instance_id'] = instance_id
        tags_to_set['device'] = device

        self._set_resource_tags(volume, tags_to_set)        
        return True
    
    
    def tag_snapshots(self):
        ''' Gets a list of all snapshots, and then loops through them tagging
        them '''
        
        log.info('Getting list of all snapshots')
        snapshots = self._conn.get_all_snapshots(owner='self')
        log.info('Found %d snapshots', len(snapshots))
        for snapshot in snapshots:
            self.tag_snapshot(snapshot)    


    def tag_snapshot(self, snapshot):
        ''' Tags a specific snapshot '''
                
        volume_id = snapshot.volume_id
#        if volume_id == '':
#            log.debug('Skipping %s as it does not have volume information', snapshot.id)
#            continue
        
        volume_tags = self._get_resource_tags(volume_id)
        
        tags_to_set = {}
        for tag_name in self._volume_tags_to_propagate:
            log.debug('Trying to propagate volume tag: %s', tag_name)
            if tag_name in volume_tags:
                value = volume_tags[tag_name]
                tags_to_set[tag_name] = value


        self._set_resource_tags(snapshot, tags_to_set)        
        return True
        

    @Memorize
    def _get_resource_tags(self, resource_id):
        ''' Gets all of the tags associated with an AWS resource (such as an
        instance-id, volume-id, etc) as a dictionary '''
        
        resource_tags = {}
        if resource_id:
            # Get the set of tags for a volume
            log.debug('Fetching tags for %s', resource_id)
            tags = self._conn.get_all_tags({'resource-id': resource_id})
            for tag in tags:
                resource_tags[tag.name] = tag.value

        return resource_tags    


    def _set_resource_tags(self, resource, tags):
        ''' Sets the tags on the given AWS resource '''
        
        if not isinstance(resource, ec2.ec2object.TaggedEC2Object):
            msg = 'Resource %s is not an instance of TaggedEC2Object' % resource
            raise GraffitiMonkeyException(msg)
        
        for tag_key, tag_value in tags.iteritems():
            if not tag_key in resource.tags or resource.tags[tag_key] != tag_value:
                log.info('Tagging %s with [%s: %s]', resource.id, tag_key, tag_value)
                resource.add_tag(tag_key, tag_value)



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
    
