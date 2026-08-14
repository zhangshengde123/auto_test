# -*- coding: utf-8 -*-
"""变量替换：把请求/断言里的 $name、${name}、${fn(args)} 替换成对应值。"""
import re

from .functions import call_function

_PATTERN = re.compile(r"\$\{(\w+)(?:\(([^)]*)\))?\}|\$(\w+)")


def substitute(obj, ctx):
    """递归替换 obj 中的变量/函数引用（支持 str / list / dict）。"""
    if isinstance(obj, str):
        return _sub_str(obj, ctx)
    if isinstance(obj, dict):
        return {k: substitute(v, ctx) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(v, ctx) for v in obj]
    return obj


def _sub_str(s, ctx):
    # 1) 整个字符串是函数调用 ${fn(args)} → 直接调用返回
    m = re.fullmatch(r"\$\{(\w+)\(([^)]*)\)\}", s)
    if m:
        return call_function(m.group(1), m.group(2))

    # 2) 整个字符串是变量 $name / ${name} → 返回原值（保留 int/list/dict 等类型）
    m = re.fullmatch(r"\$\{(\w+)\}|\$(\w+)", s)
    if m:
        name = m.group(1) or m.group(2)
        if name not in ctx:
            raise KeyError(f"变量未定义: {name}")
        return ctx[name]

    # 3) 混合字符串 → 逐处替换并转成字符串
    def repl(m):
        if m.group(1) is not None and m.group(2) is not None:
            return str(call_function(m.group(1), m.group(2)))
        name = m.group(1) or m.group(3)
        if name not in ctx:
            raise KeyError(f"变量未定义: {name}")
        return str(ctx[name])

    return _PATTERN.sub(repl, s)
