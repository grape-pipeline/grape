"""The grape main module"""

import os
import sys
import logging.config

try:
    import yaml
except ImportError:
    yaml = None

__version__ = "2.0-beta.2-SNAPSHOT"

def setup_logging(
    default_path='logging.yaml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if yaml and path and os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

    logging.root.handlers = []
    logging.getLogger().setLevel(default_level)

def set_log_level(log, level):
    """
    Set global loglevel
    """
    log.setLevel(getattr(logging, str(level).upper(), 30))

def get_logger(name, level):
    """\
    Get logger for a given name
    """
    log = logging.getLogger(name)
    log.handlers = []
    log.propagate = False
    set_log_level(log, level)

    handler = logging.StreamHandler(sys.stderr)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s  - %(message)s', '%m/%d/%Y %H:%M:%S')
    handler.setFormatter(log_formatter)
    log.addHandler(handler)

    return log


