import unittest
from unittest.mock import MagicMock

from cloudshell.shell.flows.state.basic_flow import StateFlow


class TestStateFlow(unittest.TestCase):
    def setUp(self):
        super(TestStateFlow, self).setUp()
        self.logger = MagicMock()
        self.api = MagicMock()
        self.resource_config = MagicMock()
        self.session = MagicMock(
            send_command=MagicMock(
                side_effect=lambda command: "Output of {!r}".format(command)
            )
        )
        self.cli_configurator = MagicMock(
            enable_mode_service=MagicMock(
                return_value=MagicMock(__enter__=MagicMock(return_value=self.session))
            )
        )
        self.state_flow = StateFlow(
            self.logger, self.resource_config, self.cli_configurator, self.api
        )

    def test_shutdown(self):
        with self.assertRaisesRegex(
                Exception, "Shutdown command isn't available for the current device"
        ):
            self.state_flow.shutdown()

    def test_health_check(self):
        result = self.state_flow.health_check()

        self.assertIn('passed', result)
        self.api.SetResourceLiveStatus.assert_called_once_with(
            self.resource_config.name, "Online", result
        )
        self.session.send_command.assert_called_once_with(command="")
