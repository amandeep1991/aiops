import logging
import os
from pathlib import Path

logger = logging.getLogger("aiops")
logger.setLevel(logging.DEBUG)


class LoggerMock:

    def print_code(self, s):
        print(str(self.__class__.__name__) + " : " + s)
        # pass

    def info(self, s):
        self.print_code(s)

    def debug(self, s):
        self.print_code(s)

    def warning(self, s):
        self.print_code(s)

    def error(self, s):
        self.print_code(s)

    def critical(self, s):
        self.print_code(s)


logger = LoggerMock()

_cache = Path.home() / ".cache"
cache_dir = str(_cache)
cache_dir_for_torch_text = str(_cache / "torch_text")
os.environ["TORCH_HOME"] = cache_dir
logger.info("configuration in done!!")
