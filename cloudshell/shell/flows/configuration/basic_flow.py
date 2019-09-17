#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import time
from abc import abstractmethod, abstractproperty
from posixpath import join

import jsonpickle
from cloudshell.logging.utils.decorators import command_logging

from cloudshell.shell.flows.interfaces import ConfigurationFlowInterface
from cloudshell.shell.flows.utils.networking_utils import UrlParser

AUTHORIZATION_REQUIRED_STORAGE = ["ftp", "sftp", "scp"]


class AbstractConfigurationFlow(ConfigurationFlowInterface):
    DEFAULT_BACKUP_SCHEME = "File System"

    def __init__(self, logger, resource_config):
        """Abstract configuration flow.

        :param cloudshell.shell_standards.resource_config_generic_models.GenericBackupConfig resource_config:  # noqa: E501
        :param logging.Logger logger:
        """
        self._logger = logger
        self.resource_config = resource_config

    @abstractmethod
    def _save_flow(self, folder_path, configuration_type, vrf_management_name):
        """Save flow, has to be implemented.

        :return: SaveFlow object
        """
        pass

    @abstractmethod
    def _restore_flow(
        self, path, configuration_type, restore_method, vrf_management_name
    ):
        """Restore flow, has to be implemented.

        :return: RestoreFlow object
        """
        pass

    @abstractproperty
    def _file_system(self):
        """File system attribute, has to be implemented.

        :return: file system name
        :rtype: str
        """
        pass

    @command_logging
    def save(
        self,
        folder_path="",
        configuration_type="running",
        vrf_management_name=None,
        return_artifact=False,
    ):
        """Backup config from the device to provided file system.

        Config can be 'startup-config' or 'running-config'
        Also possible to backup config to localhost

        :param folder_path:  tftp/ftp server where file be saved
        :param configuration_type: type of configuration that will be saved
            (StartUp or Running)
        :param vrf_management_name: Virtual Routing and Forwarding management name
        :param return_artifact:
        :return: status message / exception
        :rtype: OrchestrationSavedArtifact or str
        """
        self._validate_configuration_type(configuration_type)
        folder_path = self._get_path(folder_path)
        system_name = re.sub(r"\s+", "_", self.resource_config.name)[:23]
        time_stamp = time.strftime("%d%m%y-%H%M%S", time.localtime())
        destination_filename = "{0}-{1}-{2}".format(
            system_name, configuration_type.lower(), time_stamp
        )
        full_path = join(folder_path, destination_filename)
        folder_path = self._get_path(full_path)
        self._save_flow(
            folder_path=folder_path,
            configuration_type=configuration_type.lower(),
            vrf_management_name=vrf_management_name
            or getattr(self.resource_config, "vrf_management_name", None),
        )
        return folder_path

    @command_logging
    def restore(
        self,
        path,
        configuration_type="running",
        restore_method="override",
        vrf_management_name=None,
    ):
        """Restore configuration on device from provided configuration file.

        Restore configuration from local file system or ftp/tftp server into
        'running-config' or 'startup-config'.

        :param path: relative path to the file on the remote host
            tftp://server/sourcefile
        :param configuration_type: the configuration type to restore
            (StartUp or Running)
        :param restore_method: override current config or not
        :param vrf_management_name: Virtual Routing and Forwarding management name
        :return: exception on crash
        """
        self._validate_configuration_type(configuration_type)
        path = self._get_path(path)
        self._restore_flow(
            path=path,
            configuration_type=configuration_type.lower(),
            restore_method=restore_method.lower(),
            vrf_management_name=vrf_management_name
            or getattr(self.resource_config, "vrf_management_name", None),
        )

    @command_logging
    def orchestration_save(self, mode="shallow", custom_params=None):
        """Orchestration Save command.

        :param mode:
        :param custom_params: json with all required action to configure or remove
            vlans from certain port
        :return Serialized OrchestrationSavedArtifact to json
        :rtype json
        """
        save_params = {
            "folder_path": "",
            "configuration_type": "running",
            "return_artifact": True,
        }
        params = {}
        if custom_params:
            params = jsonpickle.decode(custom_params)

        save_params.update(params.get("custom_params", {}))
        save_params["folder_path"] = self._get_path(save_params["folder_path"])

        path = self.save(**save_params)

        return path

    @command_logging
    def orchestration_restore(self, saved_artifact_info, custom_params=None):
        """Orchestration restore.

        :param saved_artifact_info: json with all required data to restore
            configuration on the device
        :param custom_params: custom parameters
        """
        pass

    def _get_path(self, path=""):
        """Validate incoming path.

        If path is empty, build it from resource attributes,
        If path is invalid - raise exception

        :param path: path to remote file storage
        :return: valid path or :raise Exception:
        """
        if not path:
            host = self.resource_config.backup_location
            if ":" not in host:
                scheme = self.resource_config.backup_type
                if not scheme or scheme.lower() == self.DEFAULT_BACKUP_SCHEME.lower():
                    scheme = self._file_system
                scheme = re.sub("(:|/+).*$", "", scheme, re.DOTALL)
                host = re.sub("^/+", "", host)
                host = "{}://{}".format(scheme, host)
            path = host

        url = UrlParser.parse_url(path)

        if url[UrlParser.SCHEME].lower() in AUTHORIZATION_REQUIRED_STORAGE:
            if UrlParser.USERNAME not in url or not url[UrlParser.USERNAME]:
                url[UrlParser.USERNAME] = self.resource_config.backup_user
            if UrlParser.PASSWORD not in url or not url[UrlParser.PASSWORD]:
                url[UrlParser.PASSWORD] = self.resource_config.backup_password
        try:
            result = UrlParser.build_url(url)
        except Exception as e:
            self._logger.error("Failed to build url: {}".format(e))
            raise Exception(
                "ConfigurationOperations", "Failed to build path url to remote host"
            )
        return result

    def _validate_configuration_type(self, configuration_type):
        """Validate configuration type.

        :param configuration_type: configuration_type, should be Startup or Running
        :raise Exception:
        """
        if (
            configuration_type.lower() != "running"
            and configuration_type.lower() != "startup"
        ):
            raise Exception(
                "Configuration Type is invalid. Should be startup or running"
            )
