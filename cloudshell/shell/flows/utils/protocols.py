from __future__ import annotations

from typing_extensions import Protocol


class SessionProtocol(Protocol):
    def send_command(self, command: str) -> str:
        ...


class ServiceManagerProtocol(Protocol):
    def __enter__(self) -> SessionProtocol:
        ...


class CliConfiguratorProtocol(Protocol):
    def config_mode_service(self) -> ServiceManagerProtocol:
        ...

    def enable_mode_service(self) -> ServiceManagerProtocol:
        ...
