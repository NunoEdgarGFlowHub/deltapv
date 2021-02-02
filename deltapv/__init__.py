import os
from jax.config import config
config.update("jax_enable_x64", True)
if os.environ.get("ALLOWNANS") != "TRUE":
    config.update("jax_debug_nans", True)
if os.environ.get("NOJIT") == "TRUE":
    config.update('jax_disable_jit', True)

import logging
logger = logging.getLogger("deltapv")
logger.setLevel("INFO")

from deltapv import simulator, materials, plotting