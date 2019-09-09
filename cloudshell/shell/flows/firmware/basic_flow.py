#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import abstractmethod

from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.interfaces import FirmwareFlowInterface
from cloudshell.shell.flows.utils.networking_utils import UrlParser


class AbstractFirmwareFlow(FirmwareFlowInterface):
    def __init__(self, logger):
        """Handle firmware upgrade process.

        :param logging.Logger logger: logger
        """
        self._logger = logger
        self._timeout = 3600

    @abstractmethod
    def _load_firmware_flow(self, path, vrf_management_name, timeout):
        """Load Firmware flow property.

        :return: LoadFirmwareFlow object
        """
        pass

    @command_logging
    def load_firmware(self, path, vrf_management_name=None):
        """Update firmware version on device by loading provided image.

        Performs following steps:

            1. Copy bin file from remote tftp server.
            2. Clear in run config boot system section.
            3. Set downloaded bin file as boot file and then reboot device.
            4. Check if firmware was successfully installed.

        :param path: full path to firmware file on ftp/tftp location
        :param vrf_management_name: VRF Name
        :return: status / exception
        """
        url = UrlParser.parse_url(path)
        required_keys = [UrlParser.FILENAME, UrlParser.HOSTNAME, UrlParser.SCHEME]

        if not url or not all(key in url for key in required_keys):
            raise Exception(self.__class__.__name__, "Path is wrong or empty")

        self._load_firmware_flow(path, vrf_management_name, self._timeout)
