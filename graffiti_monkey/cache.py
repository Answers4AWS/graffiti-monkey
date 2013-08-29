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

__all__ = ('Memorize', )
log = logging.getLogger(__name__)

import collections
import functools


class Memorize(object):
    ''' Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}


    def __call__(self, *args):
        ''' Retrieve from cache, or call and save to cache '''
        
        if not isinstance(args, collections.Hashable):
            # Function arguments are not a good key (e.g. a list), so
            # better to not cache than blow up
            return self.func(*args)
        
        if args in self.cache:
            log.debug('Found key [%s] in cache', args)
            return self.cache[args]
        else:
            log.debug('Key [%s] not in cache, evaluation function and saving value', args)
            value = self.func(*args)
            self.cache[args] = value
            return value
    
    
    def __repr__(self):
        ''' Return the function's docstring '''
        
        return self.func.__doc__
    
    
    def __get__(self, obj, objtype):
        ''' Support instance methods '''
        
        return functools.partial(self.__call__, obj)
        