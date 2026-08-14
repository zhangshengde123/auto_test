# -*- coding: utf-8 -*-
"""所有 YAML 用例都汇聚到这个测试函数执行（参数由 conftest 动态注入）。"""
from core.config import load_env
from core.runner import run_case


def test_api(case_file, file_data, case, row_vars):
    _set_allure(file_data, case)
    run_case(case_file, file_data, case, row_vars, load_env())


def _set_allure(file_data, case):
    """把 YAML 元信息映射到 Allure 报告（feature/title/tag）。"""
    try:
        import allure
    except ImportError:
        return
    allure.dynamic.feature(file_data.get("name", "未命名模块"))
    allure.dynamic.title(case.get("name", "未命名用例"))
    for t in case.get("tags", []):
        allure.dynamic.tag(t)
