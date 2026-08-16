# -*- coding: utf-8 -*-
"""日志初始化：文件 + 控制台双输出，级别/目录用环境变量覆盖。

- 使用独立 logger "autotest"（propagate=False），避免污染 root / 第三方库日志。
- 初始化幂等；目录不可写时降级为仅控制台，不阻断测试。
- 日志文件 `{LOG_DIR}/test.log`，每次运行由主进程清空一次（见 conftest.py）。
"""
import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGGER_NAME = "autotest"
_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_initialized = False


def get_logger():
    return logging.getLogger(LOGGER_NAME)


def setup_logging(level=None, log_dir=None):
    """幂等配置 "autotest" logger：StreamHandler(stderr) + FileHandler(logs/test.log)。"""
    global _initialized
    if _initialized:
        return

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_resolve_level(level))
    logger.propagate = False

    formatter = logging.Formatter(_FORMAT)

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    log_dir = log_dir or os.environ.get("LOG_DIR", os.path.join(BASE_DIR, "logs"))
    try:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "test.log"), encoding="utf-8", mode="a"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logging.getLogger(__name__).warning("日志目录不可写，降级为仅控制台输出")

    _initialized = True


def clear_log_file(log_dir=None):
    """清空日志文件（仅主进程调用一次，保证每次运行覆盖上次日志）。"""
    log_dir = log_dir or os.environ.get("LOG_DIR", os.path.join(BASE_DIR, "logs"))
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "test.log"), "w", encoding="utf-8"):
            pass
    except OSError:
        pass


def _resolve_level(level):
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    return getattr(logging, str(level).upper(), logging.INFO)


def _reset():
    """仅测试用：重置初始化状态并移除 "autotest" logger 上的 handler。"""
    global _initialized
    _initialized = False
    logger = logging.getLogger(LOGGER_NAME)
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
