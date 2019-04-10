#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import abstractmethod

from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell_flows.interfaces import AutoloadInterface


class AbstractAutoload(AutoloadInterface):

    def __init__(self, resource_config, logger):
        """
        Facilitate SNMP autoload
        :param cloudshell.shell_standards.core.resource_config_entities.GenericResourceConfig resource_config:
        :param logging.Logger logger:
        """

        self.resource_config = resource_config
        self._logger = logger

    @abstractmethod
    def _autoload_flow(self, supported_os, shell_name, family_name, resource_name):
        """
        Build autoload details, has to be implemented.
        :param list supported_os: list of regexp.
        :param str shell_name: shell_name.
        :param str family_name: resource family name.
        :param str resource_name: resource name
        :return: autolod details
        :rtype: cloudshell.shell.core.driver_context.AutoLoadDetails
        """
        pass

    def _log_device_details(self, details):
        needed_attrs = {'Vendor', 'Model', 'OS Version'}
        attrs = {}

        for attr in details.attributes:
            attr_name = attr.attribute_name.rsplit('.', 1)[-1]

            if attr.relative_address == '' and attr_name in needed_attrs:
                attrs[attr_name] = attr.attribute_value

                needed_attrs.remove(attr_name)
                if not needed_attrs:
                    break

        self._logger.info('Device Vendor: "{}", Model: "{}", OS Version: "{}"'.format(
            attrs.get('Vendor', ''), attrs.get('Model', ''), attrs.get('OS Version', ''),
        ))

    @command_logging
    def discover(self):
        """Enable and Disable SNMP communityon the device, Read it's structure and attributes: chassis, modules,
        submodules, ports, port-channels and power supplies.

        :return: AutoLoadDetails object
        :rtype: cloudshell.shell.core.driver_context.AutoLoadDetails
        """

        details = self._autoload_flow(self.resource_config.supported_os,
                                      self.resource_config.shell_name,
                                      self.resource_config.family_name,
                                      self.resource_config.name)

        self._log_device_details(details)
        return details
