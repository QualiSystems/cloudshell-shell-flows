import logging

from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.command.basic_flow import RunCommandFlow
from cloudshell.shell.flows.interfaces import StateFlowInterface
from cloudshell.shell.flows.utils.errors import ShellFlowsException
from cloudshell.shell.flows.utils.protocols import CliConfiguratorProtocol

logger = logging.getLogger(__name__)


class StateFlow(StateFlowInterface):
    def __init__(self, resource_config, cli_configurator: CliConfiguratorProtocol, api):
        self._api = api
        self.resource_config = resource_config
        self._cli_configurator = cli_configurator

    @command_logging
    def health_check(self):
        """Verify that device is accessible over CLI by sending ENTER for cli."""
        api_response = "Online"
        r_name = self.resource_config.name
        result = f"Health check on resource {r_name}"

        try:
            RunCommandFlow(self._cli_configurator).run_custom_command("")
            result += " passed."
        except Exception as e:
            logger.exception(e)
            api_response = "Error"
            result += " failed."

        try:
            self._api.SetResourceLiveStatus(r_name, api_response, result)
        except Exception:
            logger.error(f"Cannot update {r_name} resource status on portal")

        return result

    def shutdown(self):
        """Shutdown device."""
        raise ShellFlowsException(
            "Shutdown command isn't available for the current device"
        )
