# -*- coding: utf-8 -*-
"""Excel 数据驱动加载器：把表格每行转为 {列名: 值} 字典。"""
import openpyxl


def load_excel(file_path, sheet_name=None):
    """读取 Excel，首行为表头（列名），后续每行为一组数据。"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h) for h in rows[0]]
    result = []
    for row in rows[1:]:
        if all(v is None or v == "" for v in row):  # 跳过空行
            continue
        result.append({headers[i]: row[i] for i in range(len(headers))})
    return result
