#!/usr/bin/python
# -*- coding: utf-8 -*-
from abc import abstractmethod

from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell_flows.interfaces import RunCommandInterface


class RunCommandFlow(RunCommandInterface):
    def __init__(self, logger, cli_handler):
        """Create RunCommandOperations

        :param logger: QsLogger object
        """
        self._logger = logger
        self._cli_handler = cli_handler

    @abstractmethod
    def _run_command_flow(self, custom_command, is_config=False):
        """ Execute flow which run custom command on device

           :param custom_command: the command to execute on device
           :param is_config: if True then run command in configuration mode
           :return: command execution output
           """
        responses = []
        if isinstance(custom_command, str):
            commands = [custom_command]
        elif isinstance(custom_command, tuple):
            commands = list(custom_command)
        else:
            commands = custom_command

        if is_config:
            mode = self._cli_handler.config_mode
            if not mode:
                raise Exception(self.__class__.__name__,
                                "CliHandler configuration is missing. Config Mode has to be defined")
        else:
            mode = self._cli_handler.enable_mode
            if not mode:
                raise Exception(self.__class__.__name__,
                                "CliHandler configuration is missing. Enable Mode has to be defined")

        with self._cli_handler.get_cli_service(mode) as session:
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
