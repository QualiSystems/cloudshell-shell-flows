from abc import ABC, abstractmethod


class ConnectivityFlowInterface(ABC):
    @abstractmethod
    def apply_connectivity_changes(self, request):
        pass


class AutoloadFlowInterface(ABC):
    @abstractmethod
    def discover(self, supported_os, resource_model):
        pass


class ConfigurationOperationsFlowInterface(ABC):

    @abstractmethod
    def save(self, folder_path, configuration_type, vrf_management_name=None):
        pass

    @abstractmethod
    def restore(self, path, configuration_type, restore_method, vrf_management_name=None):
        pass

    @abstractmethod
    def orchestration_save(self, mode="shallow", custom_params=None):
        pass

    @abstractmethod
    def orchestration_restore(self, saved_artifact_info, custom_params=None):
        pass


class FirmwareFlowInterface(ABC):

    @abstractmethod
    def load_firmware(self, path, vrf_management_name):
        pass


class RunCommandFlowInterface(ABC):

    @abstractmethod
    def run_custom_command(self, command):
        pass

    @abstractmethod
    def run_custom_config_command(self, command):
        pass


class StateOperationsFlowInterface(ABC):

    @abstractmethod
    def health_check(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass
