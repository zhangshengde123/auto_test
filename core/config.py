# -*- coding: utf-8 -*-
"""环境配置加载：支持 dev/prod 多环境，通过环境变量 TEST_ENV 切换。"""
import os

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_cache = {}


def load_env(name=None):
    """返回指定环境的配置 dict（含 base_url、variables）。"""
    name = name or os.environ.get("TEST_ENV", "dev")
    if name not in _cache:
        path = os.path.join(BASE_DIR, "config", "env.yaml")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _cache[name] = data[name]
    return _cache[name]
