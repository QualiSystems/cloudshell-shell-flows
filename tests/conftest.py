import logging
from logging.handlers import BufferingHandler

import pytest


@pytest.fixture()
def logger_handler():
    return BufferingHandler(capacity=1000)


@pytest.fixture()
def logger(logger_handler):
    logger = logging.getLogger()
    logger.addHandler(logger_handler)
    logger.setLevel(logging.DEBUG)
    return logger
