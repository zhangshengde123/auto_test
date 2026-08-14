# -*- coding: utf-8 -*-
"""公共函数注册表：自动收集 common/functions.py 中的函数，供 YAML 调用（白名单收口）。"""
import inspect

from common import functions as _mod


def _registry():
    return {
        name: obj
        for name, obj in inspect.getmembers(_mod, inspect.isfunction)
        if not name.startswith("_")
    }


def call_function(name, args_str=""):
    reg = _registry()
    if name not in reg:
        raise KeyError(f"未注册的公共函数: {name}")
    return reg[name](*_parse_args(args_str))


def _parse_args(args_str):
    if not args_str.strip():
        return []
    return [_coerce(p.strip()) for p in args_str.split(",") if p.strip()]


def _coerce(s):
    """简单类型转换：整数 / 浮点 / 布尔 / 字符串（去引号）。"""
    if s.isdigit():
        return int(s)
    try:
        return float(s)
    except ValueError:
        pass
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s
