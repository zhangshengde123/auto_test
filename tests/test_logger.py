# -*- coding: utf-8 -*-
"""core.logger 单元测试（单独运行：pytest tests/test_logger.py -v）。"""
from core import logger


def _setup(tmp_path, monkeypatch):
    """重置状态并以 tmp 目录作为日志目录初始化。"""
    logger._reset()
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    logger.setup_logging()
    return logger.get_logger()


def _read(tmp_path):
    for h in logger.get_logger().handlers:
        h.flush()
    return (tmp_path / "test.log").read_text(encoding="utf-8")


def test_setup_creates_log_file(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    logger.get_logger().info("hello 日志")
    assert "hello 日志" in _read(tmp_path)


def test_level_respected(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    logger.get_logger().debug("不该出现")
    assert "不该出现" not in _read(tmp_path)


def test_setup_is_idempotent(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    log = logger.get_logger()
    before = len(log.handlers)
    logger.setup_logging()
    assert len(log.handlers) == before
