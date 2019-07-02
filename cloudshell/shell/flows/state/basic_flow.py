#!/usr/bin/python
# -*- coding: utf-8 -*-
from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell.flows.command.basic_flow import RunCommandFlow
from cloudshell.shell.flows.interfaces import StateFlowInterface


class StateFlow(StateFlowInterface):
    def __init__(self, logger, api, resource_config, cli_handler):
        self._logger = logger
        self._api = api
        self.resource_config = resource_config
        self._cli_handler = cli_handler

    @command_logging
    def health_check(self):
        """ Verify that device is accessible over CLI by sending ENTER for cli session """

        api_response = 'Online'

        result = 'Health check on resource {}'.format(self.resource_config.name)
        try:
            RunCommandFlow(self._cli_handler, self._logger).run_custom_command()
            result += ' passed.'
        except Exception as e:
            self._logger.exception(e)
            api_response = 'Error'
            result += ' failed.'

        try:
            self._api.SetResourceLiveStatus(self.resource_config.name, api_response, result)
        except:
            self._logger.error('Cannot update {} resource status on portal'.format(self.resource_config.name))

        return result

    def shutdown(self):
        """ Shutdown device """

        raise Exception(self.__class__.__name__, "Shutdown command isn't available for the current device")
