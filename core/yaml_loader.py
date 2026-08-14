# -*- coding: utf-8 -*-
"""YAML 用例加载器。"""
import glob
import os

import yaml

from .excel_loader import load_excel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_cases(cases_dir):
    """扫描 cases_dir 下所有 YAML，返回用例实例列表。

    返回 5 元组：(文件路径, 文件数据, 单条用例, Excel行数据, 行号)
    - 无 data 配置时：行数据为 {}，行号为 None
    - 有 data 配置时：每个 case 按 Excel 每行展开成一个实例
    """
    result = []
    pattern = os.path.join(cases_dir, "**", "*.yaml")
    for path in sorted(glob.glob(pattern, recursive=True)):
        data = load_yaml(path)
        rows = _load_data_rows(data)
        for case in data.get("cases", []):
            if rows:
                for idx, row in enumerate(rows):
                    result.append((path, data, case, row, idx + 1))
            else:
                result.append((path, data, case, {}, None))
    return result


def _load_data_rows(data):
    cfg = data.get("data")
    if not cfg:
        return []
    file_path = cfg["file"]
    if not os.path.isabs(file_path):
        file_path = os.path.join(BASE_DIR, file_path)
    return load_excel(file_path, cfg.get("sheet"))
