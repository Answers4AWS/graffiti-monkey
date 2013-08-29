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

import unittest
import random

from graffiti_monkey.cache import Memorize 

class CacheTests(unittest.TestCase):
    def test_new_obj(self):
        o = Memorize('a')
        self.assertIsInstance(o, Memorize)

    @Memorize
    def get_random_number(self, some_arg):
        return random.randint(1, 100000000)

    def test_get_is_memorized(self):
        a_val = self.get_random_number('a')
        a_val_2 = self.get_random_number('a')
        a_val_3 = self.get_random_number('a')
        b_val = self.get_random_number('b')
        c_val = self.get_random_number('c')
        self.assertEquals(a_val, a_val_2)
        self.assertEquals(a_val, a_val_3)
        self.assertNotEqual(a_val, b_val)
        self.assertNotEqual(a_val, c_val)
        self.assertNotEqual(b_val, c_val)
        
        
        