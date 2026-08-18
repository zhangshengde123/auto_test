# -*- coding: utf-8 -*-
"""core.variables 单元测试（单独运行：pytest tests/test_variables.py -v）。"""
import re

import pytest

from core import variables

CTX = {"name": "张三", "user_id": 1, "data": {"a": 1}, "lst": [1, 2]}


# ---- 整串引用：返回原值并保留类型 ----

def test_whole_string_var_keeps_type():
    assert variables.substitute("$user_id", CTX) == 1          # int 保持 int
    assert variables.substitute("${user_id}", CTX) == 1        # 两种写法等价
    assert variables.substitute("$data", CTX) == {"a": 1}      # dict 保持 dict
    assert variables.substitute("$lst", CTX) == [1, 2]         # list 保持 list
    assert variables.substitute("$name", CTX) == "张三"


def test_whole_string_function_returns_raw_value(monkeypatch):
    monkeypatch.setattr(variables, "call_function", lambda name, args="": 42)
    assert variables.substitute("${fn()}", CTX) == 42          # 函数结果不转 str


def test_real_function_call():
    v = variables.substitute("${random_digits(4)}", {})
    assert re.fullmatch(r"\d{4}", v)


# ---- 混合字符串：逐处替换并转 str ----

def test_mixed_string_stringifies():
    assert variables.substitute("hello $name", CTX) == "hello 张三"
    assert variables.substitute("$user_id-${name}", CTX) == "1-张三"


def test_mixed_function_stringifies(monkeypatch):
    monkeypatch.setattr(variables, "call_function", lambda name, args="": 42)
    assert variables.substitute("id=${fn()}", CTX) == "id=42"


# ---- 递归结构 ----

def test_recursive_dict_list():
    obj = {"a": "$name", "b": ["$user_id", {"c": "${data}"}]}
    assert variables.substitute(obj, CTX) == {"a": "张三", "b": [1, {"c": {"a": 1}}]}


def test_passthrough_scalars():
    assert variables.substitute(None, CTX) is None
    assert variables.substitute(123, CTX) == 123
    assert variables.substitute(True, CTX) is True


# ---- 错误处理 ----

def test_undefined_variable_raises():
    with pytest.raises(KeyError, match="missing"):
        variables.substitute("$missing", CTX)


def test_undefined_variable_in_mixed_raises():
    with pytest.raises(KeyError, match="missing"):
        variables.substitute("x $missing", CTX)


def test_unregistered_function_raises():
    with pytest.raises(KeyError, match="not_a_fn"):
        variables.substitute("${not_a_fn()}", CTX)
