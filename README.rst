Graffiti Monkey
===============

The Graffiti Monkey goes around tagging things. By looking at the tags an EC2
instance has, it copies those tags to the EBS Volumes that are attached to it,
and then copies those tags to the EBS Snapshots.

Usage
-----

::

    usage: graffiti-monkey [-h] [--region REGION]

Examples
--------

Propagate tags from EC2 instances to EBS volumes and snapshots in us-east-1:

::

    graffiti-monkey --region us-east-1



Installation
------------

You can install Graffiti Monkey using the usual PyPI channels. Example:

::

    sudo pip install graffiti_monkey
    
You can find the package details here: https://pypi.python.org/pypi/graffiti_monkey


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
