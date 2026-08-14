# -*- coding: utf-8 -*-
"""会话级共享上下文：extract 提取的变量按文件隔离。

同一 YAML 文件内的用例共享上下文（保证 extract 顺序传值），
不同文件之间相互隔离，避免串行/并发下的变量串扰。
"""
_contexts = {}


def get_context(file_key):
    return _contexts.setdefault(file_key, {})


def set_var(file_key, key, value):
    get_context(file_key)[key] = value
