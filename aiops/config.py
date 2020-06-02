from pathlib import Path
import os
import logging

logging.info("configuration in progress.......")
_cache = Path.home() / ".cache"
cache_dir = str(_cache)
cache_dir_for_torch_text = str(_cache / "torch_text")
os.environ["TORCH_HOME"] = cache_dir
logging.info("configuration in done!!")
