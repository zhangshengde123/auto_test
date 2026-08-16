# -*- coding: utf-8 -*-
"""HTTP 请求封装：统一超时、Session 复用、请求/响应日志。"""
import time

import requests

from .logger import get_logger

logger = get_logger()


class HttpClient:
    def __init__(self, timeout=30):
        self.session = requests.Session()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        method = method.upper()
        logger.info("请求 %s %s", method, url)
        logger.debug("请求头 %s", kwargs.get("headers"))
        logger.debug("请求体 %s", _body_of(kwargs))

        start = time.perf_counter()
        resp = self.session.request(method, url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info("响应 %s %s（耗时 %.0fms）", resp.status_code, url, elapsed_ms)
        logger.debug("响应头 %s", resp.headers)
        logger.debug("响应体 %s", resp.text)
        return resp


def _body_of(kwargs):
    """取请求体（json 优先，其次 data/params），便于 DEBUG 排查。"""
    for key in ("json", "data", "params"):
        if kwargs.get(key) is not None:
            return kwargs[key]
    return None
