from unittest.mock import MagicMock

import pytest

from cloudshell.shell.flows.autoload.basic_flow import AbstractAutoloadFlow

VENDOR_ATTR_NAME = "Test Vendor"
MODEL_ATTR_NAME = "Test Model"
AUTOLOAD_DETAILS = MagicMock(
    attributes=[
        MagicMock(
            attribute_name="Shell Name.Vendor",
            attribute_value=VENDOR_ATTR_NAME,
            relative_address="",
        ),
        MagicMock(
            attribute_name="Shell Name.Model",
            attribute_value=MODEL_ATTR_NAME,
            relative_address="",
        ),
        MagicMock(
            attribute_name="Shell Name.Some Attribute",
            attribute_value="Some Attribute",
            relative_address="",
        ),
    ]
)


@pytest.fixture()
def autoload_flow():
    class ImplementedTestAbstractAutoloadFlow(AbstractAutoloadFlow):
        def _autoload_flow(self, supported_os, resource_model):
            return AUTOLOAD_DETAILS

    return ImplementedTestAbstractAutoloadFlow()


def test_discover(autoload_flow):
    supported_os = MagicMock()
    resource_model = MagicMock()
    autoload_flow._log_device_details = MagicMock()
    # act
    result = autoload_flow.discover(
        supported_os=supported_os, resource_model=resource_model
    )
    # verify
    assert AUTOLOAD_DETAILS == result
    autoload_flow._log_device_details.assert_called_once_with(AUTOLOAD_DETAILS)


def test_log_device_details(logger, logger_handler, autoload_flow):
    # act
    autoload_flow._log_device_details(details=AUTOLOAD_DETAILS)
    # verify

    assert len(logger_handler.buffer) == 1
    msg = logger_handler.buffer[0]
    assert msg.msg == (
        f'Device Vendor: "{VENDOR_ATTR_NAME}", '
        f'Model: "{MODEL_ATTR_NAME}", '
        'OS Version: ""'
    )
