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

from exceptions import *

import boto3
import botocore

import time

__all__ = ('GraffitiMonkey', 'Logging')
log = logging.getLogger(__name__)


class GraffitiMonkey(object):
    def __init__(self, region, profile, instance_tags_to_propagate, volume_tags_to_propagate, volume_tags_to_be_set, snapshot_tags_to_be_set, dryrun, append, volumes_to_tag, snapshots_to_tag, instance_filter, novolumes, nosnapshots):
        # This list of tags associated with an EC2 instance to propagate to
        # attached EBS volumes
        self._instance_tags_to_propagate = instance_tags_to_propagate

        # This is a list of tags associated with a volume to propagate to
        # a snapshot created from the volume
        self._volume_tags_to_propagate = volume_tags_to_propagate

        # This is a dict of tags (keys and values) which will be set on the volumes (ebs)
        self._volume_tags_to_be_set = volume_tags_to_be_set

        # This is a dict of tags (keys and values) which will be set on the snapshots
        self._snapshot_tags_to_be_set = snapshot_tags_to_be_set

        # The region to operate in
        self._region = region

        # The profile to use
        self._profile = profile

        # Whether this is a dryrun
        self._dryrun = dryrun

        # If we are appending tags
        self._append = append

        # Volumes we will tag
        self._volumes_to_tag = volumes_to_tag

        # Snapshots we will tag
        self._snapshots_to_tag = snapshots_to_tag

        # Filter instances by a given param and propagate their tags to their attached volumes
        self._instance_filter = instance_filter

        # If we process volumes
        self._novolumes = novolumes

        # If we process snapshots
        self._nosnapshots = nosnapshots

        log.info("Starting Graffiti Monkey")
        log.info("Options: dryrun %s, append %s, novolumes %s, nosnapshots %s", self._dryrun, self._append, self._novolumes, self._nosnapshots)
        log.info("Connecting to region %s using profile %s", self._region, self._profile)
        try:
            session = boto3.Session(profile_name=profile)
            self._conn = session.client('ec2', region_name=self._region)
        except botocore.exceptions.ProfileNotFound:
            raise GraffitiMonkeyException('No AWS credentials found - check your credentials')
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.PartialCredentialsError, botocore.exceptions.CredentialRetrievalError):
            log.info("Connecting to region %s using default credentials", self._region)
            try:
                session = boto3.Session()
                self._conn = session.client('ec2', region_name=self._region)
            except botocore.exceptions.ProfileNotFound:
                raise GraffitiMonkeyException('No AWS credentials found - check your credentials')


    def propagate_tags(self):
        ''' Propagates tags by copying them from EC2 instance to EBS volume, and
        then to snapshot '''

        volumes = []
        if not self._novolumes:
            volumes = self.tag_volumes()

        volumes = { v["VolumeId"]: v for v in volumes }

        if not self._nosnapshots:
            self.tag_snapshots(volumes)

    def tag_volumes(self):
        ''' Gets a list of volumes, and then loops through them tagging
        them '''

        storage_counter = 0
        volumes = []
        instances = {}

        if self._volumes_to_tag:
            log.info('Using volume list from cli/config file')

            # Max of 200 filters in a request
            for chunk in (self._volumes_to_tag[n:n+200] for n in xrange(0, len(self._volumes_to_tag), 200)):
                chunk_volumes = self._conn.get_all_volumes(
                        filters = { 'volume-id': chunk }
                        )
                volumes += chunk_volumes

                chunk_instance_ids = set(v.attach_data.instance_id for v in chunk_volumes)
                reservations = self._conn.get_all_instances(
                        filters = {'instance-id': [id for id in chunk_instance_ids]}
                        )
                for reservation in reservations:
                    for instance in reservation.instances:
                        instances[instance.id] = instance

            volume_ids = [v.id for v in volumes]

            ''' We can't trust the volume list from the config file so we
            test the status of each volume and remove any that raise an exception '''
            for volume_id in self._volumes_to_tag:
                if volume_id not in volume_ids:
                    log.info('Volume %s does not exist and will not be tagged', volume_id)
                    self._volumes_to_tag.remove(volume_id)

        elif self._instance_filter:
            log.info('Filter instances and retrieve volume ids')
            instances = dict((instance.id, instance) for instance in self._conn.get_only_instances(filters=self._instance_filter))
            volumes = self._conn.get_all_volumes(filters={'attachment.instance-id': list(instances.keys())})

        else:
            log.info('Getting list of all volumes')
            results = ""
            kwargs = { }
            while True:
                if "NextToken" in results:
                    kwargs["NextToken"] = results["NextToken"]
                results = self._conn.describe_volumes(**kwargs)
                for volume in results["Volumes"]:
                    volumes.append(volume)
                if "NextToken" not in results:
                    break

            results = ""
            kwargs = { }
            while True:
                if "NextToken" in results:
                    kwargs["NextToken"] = results["NextToken"]
                results = self._conn.describe_instances(**kwargs)
                for reservation in results["Reservations"]:
                    for instance in reservation["Instances"]:
                        instances[instance["InstanceId"]] = instance
                if "NextToken" not in results:
                    break

        if not volumes:
            log.info('No volumes found')
            return True

        log.debug('Volume list >%s<', volumes)
        total_vols = len(volumes)
        log.info('Found %d volume(s)', total_vols)
        this_vol = 0
        for volume in volumes:
            this_vol += 1
            storage_counter += volume["Size"]
            log.info ('Processing volume %d of %d total volumes', this_vol, total_vols)

            if volume["State"] != 'in-use':
                log.debug('Skipping %s as it is not attached to an EC2 instance, so there is nothing to propagate', volume["VolumeId"])
                continue

            for attempt in range(5):
                try:
                    self.tag_volume(volume, instances)
                except botocore.exceptions.ClientError as e:
                    log.error("Encountered Error %s on volume %s", e.error_code, volume.id)
                    break
                except (botocore.exceptions.EndpointConnectionError, botocore.exceptions.ConnectionClosedError) as e:
                    log.error("Encountered Error %s on volume %s, waiting %d seconds then retrying", e.error_code, volume.id, attempt)
                    time.sleep(attempt)
                else:
                    break
            else:
                log.error("Encountered Error %s on volume %s, %d retries failed, continuing", e.error_code, volume.id, attempt)
                continue

        log.info('Processed a total of {0} GB of AWS Volumes'.format(storage_counter))
        log.info('Completed processing all volumes')

        return volumes


    def tag_volume(self, volume, instances):
        ''' Tags a specific volume '''

        instance_id = None
        if volume["Attachments"][0]["InstanceId"]:
            instance_id = volume["Attachments"][0]["InstanceId"]
        device = None
        if volume["Attachments"][0]["Device"]:
            device = volume["Attachments"][0]["Device"]

        if "Tags" in instances[instance_id]:
            instance_tags = instances[instance_id]["Tags"]
        else:
            instance_tags = []

        tags_to_set = {}
        if self._append:
            tags_to_set = volume.tags
        for tag_name in self._instance_tags_to_propagate:
            log.debug('Trying to propagate instance tag: %s', tag_name)

            for tag_set in instance_tags:
                if tag_name in tag_set["Key"]:
                    value = tag_set["Value"]
                    tags_to_set[tag_name] = value

        # Additional tags
        tags_to_set['instance_id'] = instance_id
        tags_to_set['device'] = device

        # Set default tags for volume
        for tag in self._volume_tags_to_be_set:
            log.debug('Trying to set default tag: %s=%s', tag['key'], tag['value'])
            tags_to_set[tag['key']] = tag['value']

        if self._dryrun:
            log.info('DRYRUN: Volume %s would have been tagged %s', volume["VolumeId"], tags_to_set)
        else:
            self._set_resource_tags(volume, "VolumeId", tags_to_set)
        return True


    def tag_snapshots(self, volumes):
        ''' Gets a list of snapshots, and then loops through them tagging
        them '''

        snapshots = []
        if self._snapshots_to_tag:
            log.info('Using snapshot list from cli/config file')

            # Max of 200 filters in a request
            for chunk in (self._snapshots_to_tag[n:n+200] for n in xrange(0, len(self._snapshots_to_tag), 200)):
                chunk_snapshots = self._conn.get_all_snapshots(
                        filters = { 'snapshot-id': chunk }
                        )
                snapshots += chunk_snapshots
            snapshot_ids = [s.id for s in snapshots]

            ''' We can't trust the snapshot list from the config file so we
            test the status of each and remove any that raise an exception '''
            for snapshot_id in self._snapshots_to_tag:
                if snapshot_id not in snapshot_ids:
                    log.info('Snapshot %s does not exist and will not be tagged', snapshot_id)
                    self._snapshots_to_tag.remove(snapshot)
        else:
            log.info('Getting list of all snapshots')
            results = ""
            kwargs = {"OwnerIds": ["self"]}
            while True:
                if "NextToken" in results:
                    kwargs["NextToken"] = results["NextToken"]
                results = self._conn.describe_snapshots(**kwargs)
                for snapshot in results["Snapshots"]:
                    snapshots.append(snapshot)
                if "NextToken" not in results:
                    break

        if not snapshots:
            log.info('No snapshots found')
            return True

        all_volume_ids = set(s["VolumeId"] for s in snapshots)
        extra_volume_ids = [id for id in all_volume_ids if id not in volumes]

        ''' Fetch any extra volumes that weren't carried over from tag_volumes() (if any) '''
        for chunk in (extra_volume_ids[n:n+200] for n in xrange(0, len(extra_volume_ids), 200)):
            extra_volumes = self._conn.describe_volumes(
                    Filters=[{"Name": "volume-id", "Values": chunk}]
                    )
            for vol in extra_volumes["Volumes"]:
                volumes[vol["VolumeId"]] = vol

        log.debug('Snapshot list >%s<', snapshots)
        total_snaps = len(snapshots)
        log.info('Found %d snapshot(s)', total_snaps)
        this_snap = 0

        for snapshot in snapshots:
            this_snap += 1
            log.info ('Processing snapshot %d of %d total snapshots', this_snap, total_snaps)
            for attempt in range(5):
                try:
                    self.tag_snapshot(snapshot, volumes)
                except botocore.exceptions.ClientError as e:
                    log.error("Encountered Error %s on snapshot %s", e.error_code, snapshot.id)
                    break
                except (botocore.exceptions.EndpointConnectionError, botocore.exceptions.ConnectionClosedError) as e:
                    log.error("Encountered Error %s on snapshot %s, waiting %d seconds then retrying", e.error_code, snapshot.id, attempt)
                    time.sleep(attempt)
                else:
                    break
            else:
                log.error("Encountered Error %s on snapshot %s, %d retries failed, continuing", e.error_code, snapshot.id, attempt)
                continue
        log.info('Completed processing all snapshots')

    def tag_snapshot(self, snapshot, volumes):
        ''' Tags a specific snapshot '''

        volume_id = snapshot["VolumeId"]
        volume_tags = []

        if volume_id not in volumes:
            log.info("Snapshot %s volume %s not found. Snapshot will not be tagged", snapshot["SnapshotId"], volume_id)
            return

        if "Tags" in volumes[volume_id]:
            for volume_tag_set in volumes[volume_id]["Tags"]:
                volume_tag_key = volume_tag_set["Key"]
                volume_tag_value = volume_tag_set["Value"]
                volume_tags.append({"Key": volume_tag_key, "Value": volume_tag_value})

        tags_to_set = {}
        if self._append:
            tags_to_set = snapshot.tags
        for tag_name in self._volume_tags_to_propagate:
            log.debug('Trying to propagate volume tag: %s', tag_name)

            for tag_set in volume_tags:
                if tag_name == tag_set["Key"]:
                    value = tag_set["Value"]
                    tags_to_set[tag_name] = value

        # Set default tags for snapshot
        for tag in self._snapshot_tags_to_be_set:
            log.debug('Trying to set default tag: %s=%s', tag['key'], tag['value'])
            tags_to_set[tag['key']] = tag['value']

        if self._dryrun:
            log.info('DRYRUN: Snapshot %s would have been tagged %s', snapshot["SnapshotId"], tags_to_set)
        else:
            self._set_resource_tags(snapshot, "SnapshotId", tags_to_set)
        return True


    def _set_resource_tags(self, resource, resource_id, tags):
        ''' Sets the tags on the given AWS resource '''

        resource_tags = {}
        delta_tags = {}

        if "Tags" in resource:
            for tag_set in resource["Tags"]:
                resource_tags[tag_set["Key"]] = tag_set["Value"]
            for tag_key, tag_value in tags.iteritems():
                if not tag_key in resource_tags or resource_tags[tag_key] != tag_value:
                    delta_tags[tag_key] = tag_value
        else:
            delta_tags = tags

        if len(delta_tags) == 0:
            return

        log.info('Tagging %s with [%s]', resource[resource_id], delta_tags)

        boto3_formatted_tags = []
        for key in delta_tags.keys():
            boto3_formatted_tags.append({ 'Key': key, 'Value' : delta_tags[key]})
        self._conn.create_tags(Resources=[resource[resource_id]], Tags=boto3_formatted_tags)
        # Need to replace tags in the resource variable
        if "Tags" not in resource:
            resource["Tags"] = boto3_formatted_tags
        else:
            resource_keys = []
            for tag_set in resource["Tags"]:
                resource_keys.append(tag_set["Key"])

            for key in delta_tags.keys():
                tag_key = key
                tag_value = delta_tags[key]
                if tag_key in resource_keys:
                    tag_index = resource_keys.index(tag_key)
                    resource["Tags"][tag_index] = {"Key": tag_key, "Value": tag_value}
                else:
                    resource["Tags"].append({"Key": tag_key, "Value": tag_value})


class Logging(object):
    # Logging formats
    _log_simple_format = '%(asctime)s [%(levelname)s] %(message)s'
    _log_detailed_format = '%(asctime)s [%(levelname)s] [%(name)s(%(lineno)s):%(funcName)s] %(message)s'

    def configure(self, verbosity = None):
        ''' Configure the logging format and verbosity '''

        # Configure our logging output
        if verbosity >= 2:
            logging.basicConfig(level=logging.DEBUG, format=self._log_detailed_format, datefmt='%Y-%m-%d %H:%M:%S')
        elif verbosity >= 1:
            logging.basicConfig(level=logging.INFO, format=self._log_detailed_format, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            logging.basicConfig(level=logging.INFO, format=self._log_simple_format, datefmt='%Y-%m-%d %H:%M:%S')

        # Configure Boto's logging output
        if verbosity >= 4:
            logging.getLogger('boto3').setLevel(logging.DEBUG)
        elif verbosity >= 3:
            logging.getLogger('boto3').setLevel(logging.INFO)
        else:
            logging.getLogger('boto3').setLevel(logging.CRITICAL)
