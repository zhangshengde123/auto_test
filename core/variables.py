# -*- coding: utf-8 -*-
"""变量替换：把请求/断言里的 $name、${name}、${fn(args)} 替换成对应值。"""
import re

from .functions import call_function

# 分组：1=花括号内名字 2=函数参数（仅 ${fn(args)} 存在） 3=裸 $name 的名字
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


def _resolve(name, args, ctx):
    """求值单个引用：带参数走函数调用，无参数取变量（返回原值，保留类型）。"""
    if args is not None:
        return call_function(name, args)
    if name not in ctx:
        raise KeyError(f"变量未定义: {name}")
    return ctx[name]


def _sub_str(s, ctx):
    # 整个字符串是单个引用 → 返回原值（保留 int/list/dict 等类型）
    m = _PATTERN.fullmatch(s)
    if m:
        return _resolve(m.group(1) or m.group(3), m.group(2), ctx)

    # 混合字符串 → 逐处替换并转成字符串
    def repl(m):
        return str(_resolve(m.group(1) or m.group(3), m.group(2), ctx))

    return _PATTERN.sub(repl, s)
