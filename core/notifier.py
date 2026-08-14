# -*- coding: utf-8 -*-
"""测试结果通知：汇总通过/失败用例，通过企业微信/钉钉机器人 webhook 发送。"""
import os

import requests
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config():
    path = os.path.join(BASE_DIR, "config", "notify.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def notify(results):
    """session 结束时汇总结果并推送（未启用或无 webhook 时静默跳过）。"""
    cfg = _load_config()
    if not cfg.get("enabled"):
        return
    webhook = cfg.get("webhook")
    if not webhook:
        return

    total = len(results)
    failed = [nodeid for nodeid, r in results.items() if r.outcome != "passed"]
    passed = total - len(failed)

    lines = [
        "### 接口自动化测试结果",
        f"- 总计：**{total}**　通过：**{passed}**　失败：**{len(failed)}**",
    ]
    if failed:
        lines.append("- 失败用例：")
        for nodeid in failed:
            lines.append(f"  - {nodeid}")
    content = "\n".join(lines)

    if cfg.get("type") == "dingtalk":
        _send_dingtalk(webhook, content)
    else:
        _send_wecom(webhook, content)


def _send_wecom(webhook, content):
    requests.post(
        webhook,
        json={"msgtype": "markdown", "markdown": {"content": content}},
        timeout=10,
    )


def _send_dingtalk(webhook, content):
    requests.post(
        webhook,
        json={"msgtype": "markdown", "markdown": {"title": "测试报告", "text": content}},
        timeout=10,
    )
