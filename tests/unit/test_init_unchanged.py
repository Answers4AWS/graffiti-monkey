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
import mock
"""
These tests are put in place as to assure that behavior is not changed due to changes in the constructor of
GraffitiMonkey and .
"""
from graffiti_monkey.cli import GraffitiMonkeyCli


class InitUnchangedTests(unittest.TestCase):

    @staticmethod
    def do_not_propagate_tags_nor_exit(graffiti_monkey_cli):
        mock_do_nothing = mock.Mock()
        graffiti_monkey_cli.start_tags_propagation = mock_do_nothing
        graffiti_monkey_cli.exit_succesfully = mock_do_nothing

    @staticmethod
    def set_cli_arguments(graffiti_monkey_cli):
        mock_get_cli_arguments = mock.Mock()
        mock_get_cli_arguments.return_value = ['-v', '--region', 'us-west-1']
        graffiti_monkey_cli.get_argv = mock_get_cli_arguments

    def test_graffiti_monkey_instance_tags_to_propagate_should_be_the_same(self):
        cli = GraffitiMonkeyCli()
        self.set_cli_arguments(cli)
        self.do_not_propagate_tags_nor_exit(cli)
        cli.run()
        self.assertEquals(cli.monkey._instance_tags_to_propagate, ['Name'])

    def test_graffiti_monkey_volume_tags_to_propagate_should_be_the_same(self):
        cli = GraffitiMonkeyCli()
        self.set_cli_arguments(cli)
        self.do_not_propagate_tags_nor_exit(cli)
        cli.run()
        self.assertEquals(cli.monkey._volume_tags_to_propagate, ['Name', 'instance_id', 'device'])

    def test_region_unchanged(self):
        cli = GraffitiMonkeyCli()
        self.set_cli_arguments(cli)
        self.do_not_propagate_tags_nor_exit(cli)
        cli.run()
        self.assertEquals(cli.monkey._region, "us-west-1")
