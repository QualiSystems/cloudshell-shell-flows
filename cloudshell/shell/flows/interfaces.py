from abc import ABCMeta, abstractmethod

ABC = ABCMeta("ABC", (object,), {"__slots__": ()})


class AutoloadFlowInterface(ABC):
    @abstractmethod
    def discover(self, supported_os, resource_model):
        pass


class ConfigurationFlowInterface(ABC):
    @abstractmethod
    def save(self, folder_path, configuration_type, vrf_management_name=None):
        pass

    @abstractmethod
    def restore(
        self, path, configuration_type, restore_method, vrf_management_name=None
    ):
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


class StateFlowInterface(ABC):
    @abstractmethod
    def health_check(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass
