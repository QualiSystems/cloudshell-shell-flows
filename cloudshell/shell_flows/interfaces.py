from abc import ABC, abstractmethod


class ConnectivityInterface(ABC):
    @abstractmethod
    def apply_connectivity_changes(self, request):
        pass


class AutoloadInterface(ABC):
    @abstractmethod
    def discover(self):
        pass


class ConfigurationOperationsInterface(ABC):

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
