# -*- coding: utf-8 -*-
"""core.validators 单元测试（单独运行：pytest tests/test_validators.py -v）。"""
import pytest

from core import validators


class _FakeResp:
    """最小响应桩：json() 可抛 ValueError 模拟非 JSON 响应。"""

    def __init__(self, valid=True, content_type="application/json"):
        self.valid = valid
        self.headers = {"Content-Type": content_type}

    def json(self):
        if not self.valid:
            raise ValueError("Expecting value: line 1 column 1")
        return {"code": 0}


def test_is_json_passes():
    validators.run_validators(_FakeResp(valid=True), [{"is_json": []}])


def test_is_json_fails():
    resp = _FakeResp(valid=False, content_type="text/html")
    with pytest.raises(AssertionError, match="不是合法的 JSON"):
        validators.run_validators(resp, [{"is_json": []}])


def test_is_json_registered():
    assert "is_json" in validators.VALIDATORS
