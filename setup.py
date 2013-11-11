#!/usr/bin/env python
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

"""
setuptools install script for Graffiti Monkey
"""

import sys
major, minor = sys.version_info[0:2]
if major != 2 or minor < 7:
    print 'Graffiti Monkey requires Python 2.7.x'
    sys.exit(1)

from setuptools import setup, find_packages
    
import graffiti_monkey

with open('requirements.txt') as fh:
    requires = [requirement.strip() for requirement in fh]

entry_points = {
    'console_scripts': [
        'graffiti-monkey = graffiti_monkey.cli:run',
    ]
}

exclude_packages = [
    'tests',
    'tests.*',
]

setup(
    name='graffiti_monkey',
    version=graffiti_monkey.__version__,
    description='A service that propagates tags from EC2 instances to EBS Volumes, and then to EBS Snapshots',
    long_description=open('README.rst').read(),
    author=graffiti_monkey.__author__,
    author_email='info@answersforaws.com',
    url='https://github.com/Answers4AWS/graffiti-monkey',
    packages=find_packages(exclude=exclude_packages),
    package_dir={'graffiti_monkey': 'graffiti_monkey'},
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points=entry_points,
    license=open("LICENSE.txt").read(),
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: Utilities',
    )
)
