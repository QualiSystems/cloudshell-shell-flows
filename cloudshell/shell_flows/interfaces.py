from abc import ABC, abstractmethod


class ConnectivityInterface(ABC):
    @abstractmethod
    def apply_connectivity_changes(self, request):
        pass
