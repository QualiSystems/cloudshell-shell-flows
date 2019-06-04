#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import jsonpickle
import re
import time

from abc import abstractmethod
from posixpath import join

from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell.standards.core import OrchestrationSaveResult, OrchestrationSavedArtifactInfo, \
    OrchestrationSavedArtifact, OrchestrationRestoreRules
from cloudshell.shell.flows.interfaces import ConfigurationOperationsFlowInterface
from cloudshell.shell.flows.utils import JsonRequestDeserializer
from cloudshell.shell.flows.utils.networking_utils import UrlParser

AUTHORIZATION_REQUIRED_STORAGE = ['ftp', 'sftp', 'scp']


def _validate_custom_params(custom_params):
    if not hasattr(custom_params, 'custom_params'):
        raise Exception('ConfigurationOperations', 'custom_params attribute is empty')


class AbstractConfigurationOperationsFlow(ConfigurationOperationsFlowInterface):
    REQUIRED_SAVE_ATTRIBUTES_LIST = ['resource_name', ('saved_artifact', 'identifier'),
                                     ('saved_artifact', 'artifact_type'), ('restore_rules', 'requires_same_resource')]
    DEFAULT_FILE_SYSTEM = "File System"

    def __init__(self, resource_config, logger, api):
        """

        :param cloudshell.shell_standards.resource_config_generic_models.GenericBackupConfig resource_config:
        :param logging.Logger logger:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession api:
        """
        self._logger = logger
        self._api = api
        self.resource_config = resource_config

    @abstractmethod
    def _save_flow(self, folder_path, configuration_type, vrf_management_name):
        """ Save flow, has to be implemented.
        :return: SaveFlow object
        """

        pass

    @abstractmethod
    def _restore_flow(self, path, configuration_type, restore_method, vrf_management_name):
        """ Restore flow, has to be implemented.
        :return: RestoreFlow object
        """

        pass

    @property
    @abstractmethod
    def _file_system(self):
        """ File system attribute, has to be implemented.
        :return: str: file system name
        """
        pass

    @command_logging
    def save(self, folder_path='', configuration_type='running', vrf_management_name=None, return_artifact=False):
        """Backup 'startup-config' or 'running-config' from device to provided file_system [ftp|tftp]
        Also possible to backup config to localhost
        :param folder_path:  tftp/ftp server where file be saved
        :param configuration_type: type of configuration that will be saved (StartUp or Running)
        :param vrf_management_name: Virtual Routing and Forwarding management name
        :param return_artifact:
        :return: status message / exception
        :rtype: OrchestrationSavedArtifact or str
        """

        self._validate_configuration_type(configuration_type)
        folder_path = self._get_path(folder_path)
        system_name = re.sub(r'\s+', '_', self.resource_config.name)[:23]
        time_stamp = time.strftime("%d%m%y-%H%M%S", time.localtime())
        destination_filename = '{0}-{1}-{2}'.format(system_name, configuration_type.lower(), time_stamp)
        full_path = join(folder_path, destination_filename)
        folder_path = self._get_path(full_path)
        self._save_flow(folder_path=folder_path,
                        configuration_type=configuration_type.lower(),
                        vrf_management_name=vrf_management_name or getattr(self.resource_config,
                                                                           "vrf_management_name", None))

        if return_artifact:
            artifact_type = full_path.split(':')[0]
            identifier = full_path.replace("{0}:".format(artifact_type), "")
            return OrchestrationSavedArtifact(identifier=identifier, artifact_type=artifact_type)

        return destination_filename

    @command_logging
    def restore(self, path, configuration_type="running", restore_method="override", vrf_management_name=None):
        """Restore configuration on device from provided configuration file
        Restore configuration from local file system or ftp/tftp server into 'running-config' or 'startup-config'.
        :param path: relative path to the file on the remote host tftp://server/sourcefile
        :param configuration_type: the configuration type to restore (StartUp or Running)
        :param restore_method: override current config or not
        :param vrf_management_name: Virtual Routing and Forwarding management name
        :return: exception on crash
        """

        self._validate_configuration_type(configuration_type)
        path = self._get_path(path)
        self._restore_flow(path=path, configuration_type=configuration_type.lower(),
                           restore_method=restore_method.lower(),
                           vrf_management_name=vrf_management_name or getattr(self.resource_config,
                                                                              "vrf_management_name", None))

    @command_logging
    def orchestration_save(self, mode="shallow", custom_params=None):
        """Orchestration Save command

        :param mode:
        :param custom_params: json with all required action to configure or remove vlans from certain port
        :return Serialized OrchestrationSavedArtifact to json
        :rtype json
        """

        save_params = {'folder_path': '', 'configuration_type': 'running', 'return_artifact': True}
        params = dict()
        if custom_params:
            params = jsonpickle.decode(custom_params)

        save_params.update(params.get('custom_params', {}))
        save_params['folder_path'] = self._get_path(save_params['folder_path'])

        saved_artifact = self.save(**save_params)

        saved_artifact_info = OrchestrationSavedArtifactInfo(resource_name=self.resource_config.name,
                                                             created_date=datetime.datetime.now(),
                                                             restore_rules=self._get_restore_rules(),
                                                             saved_artifact=saved_artifact)
        save_response = OrchestrationSaveResult(saved_artifacts_info=saved_artifact_info)
        self._validate_artifact_info(saved_artifact_info)

        return str(jsonpickle.encode(save_response, unpicklable=False))

    @command_logging
    def orchestration_restore(self, saved_artifact_info, custom_params=None):
        """Orchestration restore

        :param saved_artifact_info: json with all required data to restore configuration on the device
        :param custom_params: custom parameters
        """

        if saved_artifact_info is None or saved_artifact_info == '':
            raise Exception('ConfigurationOperations', 'saved_artifact_info is None or empty')

        saved_artifact_info = JsonRequestDeserializer(jsonpickle.decode(saved_artifact_info))
        if not hasattr(saved_artifact_info, 'saved_artifacts_info'):
            raise Exception('ConfigurationOperations', 'Saved_artifacts_info is missing')
        saved_config = saved_artifact_info.saved_artifacts_info
        params = None
        if custom_params:
            params = JsonRequestDeserializer(jsonpickle.decode(custom_params))
            _validate_custom_params(params)

        self._validate_artifact_info(saved_config)

        if saved_config.restore_rules.requires_same_resource \
                and saved_config.resource_name.lower() != self.resource_config.name.lower():
            raise Exception('ConfigurationOperations',
                            'Incompatible resource, expected {}'.format(self.resource_config.name))

        restore_params = {'configuration_type': 'running',
                          'restore_method': 'override',
                          'vrf_management_name': None,
                          'path': '{}:{}'.format(saved_config.saved_artifact.artifact_type,
                                                 saved_config.saved_artifact.identifier)}

        if hasattr(params, 'custom_params'):
            if hasattr(params.custom_params, 'restore_method'):
                restore_params['restore_method'] = params.custom_params.restore_method

            if hasattr(params.custom_params, 'configuration_type'):
                restore_params['configuration_type'] = params.custom_params.configuration_type

            if hasattr(params.custom_params, 'vrf_management_name'):
                restore_params['vrf_management_name'] = params.custom_params.vrf_management_name

        if 'startup' in saved_config.saved_artifact.identifier.split('/')[-1]:
            restore_params['configuration_type'] = 'startup'

        self.restore(**restore_params)

    def _get_path(self, path=''):
        """
        Validate incoming path, if path is empty, build it from resource attributes,
        If path is invalid - raise exception

        :param path: path to remote file storage
        :return: valid path or :raise Exception:
        """

        if not path:
            host = self.resource_config.backup_location
            if ':' not in host:
                scheme = self.resource_config.backup_type
                if not scheme or scheme.lower() == self.DEFAULT_FILE_SYSTEM.lower():
                    scheme = self._file_system
                scheme = re.sub('(:|/+).*$', '', scheme, re.DOTALL)
                host = re.sub('^/+', '', host)
                host = '{}://{}'.format(scheme, host)
            path = host

        url = UrlParser.parse_url(path)

        if url[UrlParser.SCHEME].lower() in AUTHORIZATION_REQUIRED_STORAGE:
            if UrlParser.USERNAME not in url or not url[UrlParser.USERNAME]:
                url[UrlParser.USERNAME] = self.resource_config.backup_user
            if UrlParser.PASSWORD not in url or not url[UrlParser.PASSWORD]:
                url[UrlParser.PASSWORD] = self._api.DecryptPassword(self.resource_config.backup_password).Value
        try:
            result = UrlParser.build_url(url)
        except Exception as e:
            self._logger.error('Failed to build url: {}'.format(e))
            raise Exception('ConfigurationOperations', 'Failed to build path url to remote host')
        return result

    def _validate_configuration_type(self, configuration_type):
        """Validate configuration type

        :param configuration_type: configuration_type, should be Startup or Running
        :raise Exception:
        """

        if configuration_type.lower() != 'running' and configuration_type.lower() != 'startup':
            raise Exception(self.__class__.__name__, 'Configuration Type is invalid. Should be startup or running')

    def _validate_artifact_info(self, saved_config):
        """Validate OrchestrationSavedArtifactInfo object for key components

        :param OrchestrationSavedArtifactInfo saved_config: object to validate
        """
        is_fail = False
        fail_attribute = ''
        for class_attribute in self.REQUIRED_SAVE_ATTRIBUTES_LIST:
            if type(class_attribute) is tuple:
                if not hasattr(saved_config, class_attribute[0]):
                    is_fail = True
                    fail_attribute = class_attribute[0]
                elif not hasattr(getattr(saved_config, class_attribute[0]), class_attribute[1]):
                    is_fail = True
                    fail_attribute = class_attribute[1]
            else:
                if not hasattr(saved_config, class_attribute):
                    is_fail = True
                    fail_attribute = class_attribute

        if is_fail:
            raise Exception('ConfigurationOperations',
                            'Mandatory field {0} is missing in Saved Artifact Info request json'.format(
                                fail_attribute))

    def _get_restore_rules(self):
        """
        Populate required restore rules.

        :return OrchestrationRestoreRules: response
        """

        self._logger.info('Creating Restore Rules')
        return OrchestrationRestoreRules(True)
