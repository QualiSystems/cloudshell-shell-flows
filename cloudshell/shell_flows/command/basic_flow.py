#!/usr/bin/python
# -*- coding: utf-8 -*-
import collections

from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell_flows.interfaces import RunCommandInterface


class RunCommandFlow(RunCommandInterface):
    def __init__(self, logger, cli_configurator):
        """Create RunCommandOperations

        :param logger: QsLogger object
        :param cloudshell.cli.configurator.EnableConfigModeConfigurator cli_configurator:
        """
        self._logger = logger
        self._cli_configurator = cli_configurator

    def _run_command_flow(self, custom_command, is_config=False):
        """ Execute flow which run custom command on device

           :param custom_command: the command to execute on device
           :param is_config: if True then run command in configuration mode
           :return: command execution output
           """
        if not isinstance(custom_command, collections.Iterable):
            commands = [custom_command]
        else:
            commands = custom_command

        if is_config:
            service_manager = self._cli_configurator.enable_mode_service()
        else:
            service_manager = self._cli_configurator.config_mode_service()

        responses = []
        with service_manager as session:
            for cmd in commands:
                responses.append(session.send_command(command=cmd))
        return '\n'.join(responses)

    @command_logging
    def run_custom_command(self, custom_command):
        """ Execute custom command on device

        :param custom_command: command
        :return: result of command execution
        """

        return self._run_command_flow(custom_command=custom_command)

    @command_logging
    def run_custom_config_command(self, custom_command):
        """ Execute custom command in configuration mode on device

        :param custom_command: command
        :return: result of command execution
        """

        return self._run_command_flow(custom_command=custom_command, is_config=True)
