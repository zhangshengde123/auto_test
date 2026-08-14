# -*- coding: utf-8 -*-
"""HTTP 请求封装：统一超时、Session 复用（后续可扩展重试、日志、Mock）。"""
import requests


class HttpClient:
    def __init__(self, timeout=30):
        self.session = requests.Session()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method.upper(), url, **kwargs)
