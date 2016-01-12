Graffiti Monkey
===============

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/Answers4AWS/graffiti-monkey
   :target: https://gitter.im/Answers4AWS/graffiti-monkey?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://travis-ci.org/Answers4AWS/graffiti-monkey.png?branch=master
   :target: https://travis-ci.org/Answers4AWS/graffiti-monkey
   :alt: Build Status

The Graffiti Monkey goes around tagging things. By looking at the tags an EC2
instance has, it copies those tags to the EBS Volumes that are attached to it,
and then copies those tags to the EBS Snapshots.

Usage
-----

::

	usage: graffiti-monkey [-h] [--region REGION] [--profile PROFILE] [--verbose] [--version] [--config CONFIG.YML] [--dryrun]

	Propagates tags from AWS EC2 instances to EBS volumes, and then to EBS
	snapshots. This makes it much easier to find things down the road.

	optional arguments:
	  -h, --help           show this help message and exit
	  --region REGION      the region to tag things in (default is current region of
	                       EC2 instance this is running on). E.g. us-east-1
	  --profile PROFILE    the profile to use to connect to EC2 (default is 'default',
	                       see Boto docs for profile credential options)
	  --verbose, -v        enable verbose output (-vvv for more)
	  --version            display version number and exit
	  --config CONFIG.YML  read a yaml configuration file.  specify tags to propagate without changing code.
	  --dryrun             dryrun only, display tagging actions but do not perform them
	  --append             append propagated tags to existing tags (up to a total of ten tags). When not set,
	                       graffiti-monkey will overwrite existing tags.
	  --volumes            volume(s) to tag
	  --snapshots          snapshot(s) to tag
	  --novolumes          do not perform volume tagging
	  --nosnapshots        do not perform snapshot tagging

Examples
--------

Suppose you have the following in `us-east-1`:

::

	i-abcd1234
	  - Tags:
	    - Name: "Instance 1"

	vol-bcde3456
	  - Attached to i-abcd1234 on /dev/sda1

	snap-cdef4567
	  - Snapshot of vol-bcde3456


When you run:

::

    graffiti-monkey --region us-east-1


First, Graffiti Monkey will set the EBS volume tags

::

	vol-bcde3456
	  - Tags:
	    - Name: "Instance 1"
	    - instance_id: i-abcd1234
	    - device: /dev/sda1

and then it will set the tags on the EBS Snapshot

::

	snap-cdef4567
	  - Tags:
	    - Name: "Instance 1"
	    - instance_id: i-abcd1234
	    - device: /dev/sda1



Installation
------------

You can install Graffiti Monkey using the usual PyPI channels. Example:

::

    sudo pip install graffiti_monkey

You can find the package details here: https://pypi.python.org/pypi/graffiti_monkey

Alternatively, if you prefer to install from source:

::

    git clone git@github.com:Answers4AWS/graffiti-monkey.git
    cd graffiti-monkey
    python setup.py install


Configuration
-------------

This project uses `Boto <http://boto.readthedocs.org/en/latest/index.html>`__ to
call the AWS APIs. You can pass your AWS credentials to Boto can by using a
:code:`.boto` file, IAM Roles or environment variables. Full information can be
found here:

http://boto.readthedocs.org/en/latest/boto_config_tut.html

Graffiti-monkey itself can be configured using a yaml file

::

  ---
  #region: us-west-1
  _instance_tags_to_propagate:
    - 'Name'
    - 'Owner'

  _volume_tags_to_propagate:
    - 'Name'
    - 'instance_id'
    - 'device'
    - 'Owner'

  _volume_tags_to_be_set:
    -  key:   'NU_ROLE'
       value: 'ebs'
  
  _snapshot_tags_to_be_set:
    -  key:   'NU_ROLE'
       value: 'ebs_snapshot'

  _volumes_to_tag:
  # An empty list means tag all volumes
  # Example entries:
  #  - 'vol-1ab2c345'
  #  - 'vol-6de7f890'

  _snapshots_to_tag:
  # An empty list means tag all snapshots
  # Example entries:
  #  - 'snap-12ab3c45'
  #  - 'snap-6de7f890'

:code:`_instance_tags_to_propagate` is used to define the tags that are propagated
from an instance to its volumes. :code:`_volume_tags_to_propagate` defines the tags
that are propagated from a volume to its snapshots.

:code:`_volume_tags_to_be_set` is used to define the tags that are set on volumes
by default. :code:`_snapshot_tags_to_be_set` defines the tags that are on snapshots
by default.

:code:`_volumes_to_tag` is used to define the volumes that are tagged. Leave empty
to tag all volumes. :code:`_snapshots_to_tag` is used to define the snapshots to
be tagged. Leave empty to tag all snapshots.

If the configuration file is used, the _ entry headers must exist (those entries
having no values or commented out values [as shown] is acceptable).

When using yaml configuration files you need to have pyYAML. This can be easily setup
 using pip :code:`pip install PyYAML`.  If you don't use config files you don't have
 this limitation.

If options are specified in both the config file and on the command line, the config
file options are used.


Wiki
----

Can be found here: https://github.com/Answers4AWS/graffiti-monkey/wiki


Source Code
-----------

The Python source code for Graffiti Monkey is available on GitHub:

https://github.com/Answers4AWS/graffiti-monkey


About Answers for AWS
---------------------

This code was written by `Peter
Sankauskas <https://twitter.com/pas256>`__, founder of `Answers for
AWS <http://answersforaws.com/>`__ - a company focused on helping businesses
learn how to use AWS, without doing it the hard way. If you are looking for help
with AWS, please `contact us <http://answersforaws.com/contact/>`__.


License
-------

Copyright 2013 Answers for AWS LLC

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable
law or agreed to in writing, software distributed under the License is
distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
