import sys
import unittest

from cloudshell.shell.flows.state.basic_flow import StateFlow

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestStateFlow(unittest.TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.api = mock.MagicMock()
        self.resource_config = mock.MagicMock()
        self.session = mock.MagicMock(
            send_command=mock.MagicMock(
                side_effect=lambda command: "Output of {!r}".format(command)
            )
        )
        self.cli_configurator = mock.MagicMock(
            enable_mode_service=mock.MagicMock(
                return_value=mock.MagicMock(
                    __enter__=mock.MagicMock(return_value=self.session)
                )
            )
        )
        self.state_flow = StateFlow(
            logger=self.logger,
            api=self.api,
            resource_config=self.resource_config,
            cli_configurator=self.cli_configurator,
        )

    def test_shutdown(self):
        """Check that method will raise exception."""
        with self.assertRaisesRegexp(
            Exception, "Shutdown command isn't available for the current device"
        ):
            self.state_flow.shutdown()

    @mock.patch("cloudshell.shell.flows.state.basic_flow.RunCommandFlow")
    def test_health_check_passed(self, run_command_flow_class):
        """Check that method will execute RunCommandFlow and return success message."""
        run_command_flow = mock.MagicMock()
        run_command_flow_class.return_value = run_command_flow
        # act
        result = self.state_flow.health_check()
        # verify
        self.assertEqual(
            result,
            "Health check on resource {} passed.".format(self.resource_config.name),
        )

        run_command_flow_class.assert_called_once_with(
            self.logger, self.cli_configurator
        )
        run_command_flow.run_custom_command.assert_called_once_with("")
        self.api.SetResourceLiveStatus.assert_called_once_with(
            self.resource_config.name, "Online", result
        )

    @mock.patch("cloudshell.shell.flows.state.basic_flow.RunCommandFlow")
    def test_health_check_failed(self, run_command_flow_class):
        """Check that method will execute RunCommandFlow and return failed message."""
        run_command_flow = mock.MagicMock(
            run_custom_command=mock.MagicMock(side_effect=Exception)
        )
        run_command_flow_class.return_value = run_command_flow
        # act
        result = self.state_flow.health_check()
        # verify
        self.assertEqual(
            result,
            "Health check on resource {} failed.".format(self.resource_config.name),
        )
        self.api.SetResourceLiveStatus.assert_called_once_with(
            self.resource_config.name, "Error", result
        )

    @mock.patch("cloudshell.shell.flows.state.basic_flow.RunCommandFlow")
    def test_health_check_failed_to_update_live_status(self, run_command_flow_class):
        """Check that method will not update live status. if health check fails."""
        self.api.SetResourceLiveStatus.side_effect = Exception()
        # act
        result = self.state_flow.health_check()
        # verify
        self.assertEqual(
            result,
            "Health check on resource {} passed.".format(self.resource_config.name),
        )
