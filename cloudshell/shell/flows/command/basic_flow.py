from __future__ import annotations

from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.interfaces import RunCommandFlowInterface
from cloudshell.shell.flows.utils.protocols import CliConfiguratorProtocol


class RunCommandFlow(RunCommandFlowInterface):
    def __init__(self, cli_configurator: CliConfiguratorProtocol):
        self._cli_configurator = cli_configurator

    def _run_command_flow(self, custom_command: str, is_config: bool = False) -> str:
        """Execute flow which run custom command on device.

        :param custom_command: the command to execute on device
        :param is_config: if True then run command in configuration mode
        """
        commands = self.parse_custom_commands(custom_command)

        if is_config:
            service_manager = self._cli_configurator.config_mode_service()
        else:
            service_manager = self._cli_configurator.enable_mode_service()

        responses = []
        with service_manager as session:
            for cmd in commands:
                responses.append(session.send_command(command=cmd))
        return "\n".join(responses)

    @command_logging
    def run_custom_command(self, custom_command: str) -> str:
        """Execute custom command on device."""
        return self._run_command_flow(custom_command=custom_command)

    @command_logging
    def run_custom_config_command(self, custom_command: str) -> str:
        """Execute custom command in configuration mode on device."""
        return self._run_command_flow(custom_command=custom_command, is_config=True)

    @staticmethod
    def parse_custom_commands(command: str, separator: str = ";") -> list[str]:
        """Parse run custom command string into the commands list.

        :param str command: run custom [config] command(s)
        :param str separator: commands separator in the string
        """
        return command.strip(separator).split(separator)
