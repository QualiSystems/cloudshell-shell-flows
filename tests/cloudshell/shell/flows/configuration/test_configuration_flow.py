from __future__ import annotations

import json
import time
from unittest.mock import Mock

import attr
import pytest

from cloudshell.shell.flows.configuration.basic_flow import (
    AbstractConfigurationFlow,
    ConfigurationType,
    RestoreMethod,
)
from cloudshell.shell.flows.utils.url import ErrorParsingUrl, LocalFileURL


@attr.s(auto_attribs=True, slots=True, frozen=True)
class ResourceConfig:
    name: str
    backup_location: str = ""
    backup_type: str = ""
    backup_user: str = ""
    backup_password: str = ""


@pytest.fixture()
def logger():
    return Mock()


@pytest.fixture()
def local_time_str(monkeypatch):
    l_time = time.localtime()

    def get_local_time():
        return l_time

    monkeypatch.setattr(time, "localtime", get_local_time)
    return time.strftime("%d%m%y-%H%M%S", l_time)


def test_file_system_property_not_implemented(logger):
    class TestedFlow(AbstractConfigurationFlow):
        def _save_flow(
            self,
            file_dst_url,
            configuration_type: ConfigurationType,
            vrf_management_name: str | None,
        ) -> str | None:
            return super()._save_flow(
                file_dst_url, configuration_type, vrf_management_name
            )

        def _restore_flow(
            self,
            config_path,
            configuration_type: ConfigurationType,
            restore_method,
            vrf_management_name: str | None,
        ) -> None:
            return super()._restore_flow(
                config_path, configuration_type, restore_method, vrf_management_name
            )

        @property
        def file_system(self) -> str:
            return super().file_system

    conf = ResourceConfig("res-name")
    flow = TestedFlow(logger, conf)

    with pytest.raises(NotImplementedError):
        _ = flow.file_system
    with pytest.raises(NotImplementedError):
        flow._save_flow(None, None, None)
    with pytest.raises(NotImplementedError):
        flow._restore_flow(None, None, None, None)


@pytest.mark.parametrize(
    ("folder_path", "resource_config", "file_system", "expected_file_prefix"),
    (
        (
            "ftp://user:password@192.168.2.3",
            ResourceConfig("res name"),
            None,
            "ftp://user:password@192.168.2.3/res_name",
        ),
        (
            "ftp://192.168.2.3",
            ResourceConfig("res name"),
            None,
            "ftp://192.168.2.3/res_name",
        ),
        (
            "ftp://192.168.2.3",
            ResourceConfig("res name", backup_user="ftp_user"),
            None,
            "ftp://ftp_user@192.168.2.3/res_name",
        ),
        (
            "ftp://192.168.2.3",
            ResourceConfig("res name", backup_user="ftp_user", backup_password="pw"),
            None,
            "ftp://ftp_user:pw@192.168.2.3/res_name",
        ),
        (
            "",
            ResourceConfig(
                "res name",
                backup_location="ftp://192.168.4.5",
                backup_user="ftp_user",
                backup_password="pw",
            ),
            None,
            "ftp://ftp_user:pw@192.168.4.5/res_name",
        ),
        (
            "",
            ResourceConfig(
                "res name",
                backup_location="192.168.4.5",
                backup_type="ftp",
                backup_user="ftp_user",
                backup_password="pw",
            ),
            None,
            "ftp://ftp_user:pw@192.168.4.5/res_name",
        ),
        (
            "",
            ResourceConfig(
                "res name",
                backup_type=AbstractConfigurationFlow.FILE_SYSTEM_SCHEME,
            ),
            "flash:/",
            "flash://res_name",
        ),
        (
            "",
            ResourceConfig(
                "res name",
                backup_type=AbstractConfigurationFlow.FILE_SYSTEM_SCHEME,
            ),
            "disc0:",
            "disc0:/res_name",
        ),
        (
            "flash:/folder_path",
            ResourceConfig("res name"),
            "",
            "flash:/folder_path/res_name",
        ),
    ),
)
def test_save_method_get_correct_file_path(
    folder_path,
    resource_config,
    file_system,
    expected_file_prefix,
    logger,
    local_time_str,
):
    config_type = "running"
    expected_file_path = f"{expected_file_prefix}-{config_type}-{local_time_str}"

    class TestedConfigurationFlow(AbstractConfigurationFlow):
        _restore_flow = None

        @property
        def file_system(self) -> str:
            return file_system

        def _save_flow(self, file_dst_url, configuration_type, vrf_management_name):
            assert str(file_dst_url) == expected_file_path
            assert configuration_type == ConfigurationType.from_str(config_type)

    flow = TestedConfigurationFlow(logger, resource_config)

    file_name = flow.save(folder_path, config_type)
    assert file_name == expected_file_path.rsplit("/")[-1]


def test_save_return_another_filename(logger):
    class TestedConfigurationFlow(AbstractConfigurationFlow):
        _restore_flow = None
        file_system = None

        def _save_flow(
            self,
            file_dst_url,
            configuration_type: ConfigurationType,
            vrf_management_name: str | None,
        ) -> str | None:
            return "another-file-name"

    resource_config = ResourceConfig("res-name")
    flow = TestedConfigurationFlow(logger, resource_config)
    file_name = flow.save("ftp://folder-path", "running")

    assert file_name == "another-file-name"


def test_save_incorrect_folder_path(logger):
    class TestedConfigurationFlow(AbstractConfigurationFlow):
        _restore_flow = None
        _save_flow = None
        file_system = None

    resource_config = ResourceConfig("res-name")
    flow = TestedConfigurationFlow(logger, resource_config)

    with pytest.raises(ErrorParsingUrl):
        flow.save("flash", "startup")


def test_orchestration_save(logger, local_time_str):
    class TestedFlow(AbstractConfigurationFlow):
        file_system = "flash:/"
        _restore_flow = None

        def _save_flow(
            self,
            file_dst_url,
            configuration_type: ConfigurationType,
            vrf_management_name: str | None,
        ) -> str | None:
            return None

    conf = ResourceConfig("res-name")
    flow = TestedFlow(logger, conf)
    custom_params = json.dumps({"custom_params": {"configuration_type": "startup"}})
    file_path = flow.orchestration_save(custom_params=custom_params)
    file_suffix = f"-startup-{local_time_str}"

    assert file_path == f"{TestedFlow.file_system}/{conf.name}{file_suffix}"


@pytest.mark.parametrize(
    ("passed_config_path", "resource_config", "expected_config_path"),
    (
        (
            "ftp://user:pass@host/file-name",
            ResourceConfig(""),
            "ftp://user:pass@host/file-name",
        ),
        ("tftp://host/file-name", ResourceConfig(""), "tftp://host/file-name"),
        (
            "sftp://host/folder/file",
            ResourceConfig("", backup_user="user", backup_password="pass"),
            "sftp://user:pass@host/folder/file",
        ),
        (
            "file_name",
            ResourceConfig("", backup_user="user", backup_password="pass"),
            "disk0:/file_name",
        ),
    ),
)
def test_restore(logger, passed_config_path, resource_config, expected_config_path):
    class TestedFlow(AbstractConfigurationFlow):
        file_system = "disk0:"
        _save_flow = None

        def _restore_flow(
            self,
            config_path,
            configuration_type: ConfigurationType,
            restore_method: RestoreMethod,
            vrf_management_name: str | None,
        ) -> None:
            assert str(config_path) == expected_config_path
            assert configuration_type == ConfigurationType.STARTUP
            assert restore_method == RestoreMethod.OVERRIDE
            assert vrf_management_name == "mgmt-vrf"

    flow = TestedFlow(logger, resource_config)
    flow.restore(passed_config_path, "startup", "override", "mgmt-vrf")


def test_restore_invalid_path(logger):
    class TestedFlow(AbstractConfigurationFlow):
        file_system = None
        _save_flow = None
        _restore_flow = None

    conf = ResourceConfig("")
    flow = TestedFlow(logger, conf)

    with pytest.raises(ErrorParsingUrl):
        flow.restore("file", "running", "append")


def test_another_local_url(logger, local_time_str):
    file_suffix = f"-running-{local_time_str}"
    conf = ResourceConfig("res-name")

    class TestedFlow(AbstractConfigurationFlow):
        LOCAL_URL_CLASS = LocalFileURL
        file_system = "file:/"

        def _save_flow(
            self,
            file_dst_url: LOCAL_URL_CLASS,
            configuration_type: ConfigurationType,
            vrf_management_name: str | None,
        ) -> str | None:
            assert file_dst_url == LocalFileURL(path=f"/folder/res-name{file_suffix}")
            return None

        def _restore_flow(
            self,
            config_path: LOCAL_URL_CLASS,
            configuration_type: ConfigurationType,
            restore_method: RestoreMethod,
            vrf_management_name: str | None,
        ) -> None:
            assert config_path == LocalFileURL(path="/folder/res-name")

    flow = TestedFlow(logger, conf)
    flow.save("file://folder", "running", "mgmt")
    flow.restore("file://folder/res-name", "running", "append", "mgmt")
