# -*- coding: utf-8 -*-
"""pytest 入口钩子：把 cases/ 下的 YAML 用例动态注册成 pytest 测试项。

测试人员只需在 cases/ 目录下编写/维护 YAML 文件（零代码），
本文件负责把它们转换成可执行、可标记、可单独运行的 pytest 用例。
"""
import os
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.logger import setup_logging  # noqa: E402
from core.notifier import notify  # noqa: E402
from core.yaml_loader import load_cases  # noqa: E402

# 记录每个用例的执行结果，供 session 结束时的结果通知使用
_results = {}


def pytest_configure(config):
    setup_logging()


def pytest_generate_tests(metafunc):
    """为 test_api 测试函数按 YAML 用例动态生成参数。"""
    if metafunc.function.__name__ != "test_api":
        return

    cases = load_cases(os.path.join(BASE_DIR, "cases"))
    params, ids = [], []
    for file_path, file_data, case, row_vars, data_index in cases:
        # 把 YAML 里的 tags 转成 pytest 标记，支持 pytest -m smoke 按需执行
        marks = [getattr(pytest.mark, t) for t in case.get("tags", [])]
        # 按 YAML 文件分组：同文件内用例串行（保证 extract 顺序），不同文件可并发
        marks.append(pytest.mark.xdist_group(file_path))
        params.append(pytest.param(file_path, file_data, case, row_vars, marks=marks))

        rel = os.path.relpath(file_path, BASE_DIR).replace("\\", "/")
        name = case["name"]
        if data_index is not None:
            name = f"{name}[数据第{data_index}行]"
        ids.append(f"{rel}::{name}")

    metafunc.parametrize("case_file, file_data, case, row_vars", params, ids=ids)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if call.when == "call":
        _results[item.nodeid] = outcome.get_result()


def pytest_sessionfinish(session, exitstatus):
    notify(_results)
