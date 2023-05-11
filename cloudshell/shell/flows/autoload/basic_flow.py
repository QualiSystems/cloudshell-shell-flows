from __future__ import annotations

import logging
import re
from abc import abstractmethod

from cloudshell.logging.utils.decorators import command_logging
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.standards.autoload_generic_models import GenericResourceModel

from cloudshell.shell.flows.interfaces import AutoloadFlowInterface

logger = logging.getLogger(__name__)


class AbstractAutoloadFlow(AutoloadFlowInterface):
    @abstractmethod
    def _autoload_flow(
        self,
        supported_os: re.Pattern | str | list[str],
        resource_model: GenericResourceModel,
    ) -> AutoLoadDetails:
        pass

    @staticmethod
    def _log_device_details(details: AutoLoadDetails) -> None:
        needed_attrs = {"Vendor", "Model", "OS Version"}
        attrs = {}

        for attr in details.attributes:
            attr_name = attr.attribute_name.rsplit(".", 1)[-1]

            if attr.relative_address == "" and attr_name in needed_attrs:
                attrs[attr_name] = attr.attribute_value

                needed_attrs.remove(attr_name)
                if not needed_attrs:
                    break

        logger.info(
            f'Device Vendor: "{attrs.get("Vendor", "")}", '
            f'Model: "{attrs.get("Model", "")}", '
            f'OS Version: "{attrs.get("OS Version", "")}"'
        )

    @command_logging
    def discover(
        self,
        supported_os: re.Pattern | str | list[str],
        resource_model: GenericResourceModel,
    ) -> AutoLoadDetails:
        details = self._autoload_flow(supported_os, resource_model)

        self._log_device_details(details)
        return details
