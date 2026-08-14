# -*- coding: utf-8 -*-
"""用例执行器：变量替换 -> 发请求 -> 提取 -> 断言。"""
from .context import get_context, set_var
from .http_client import HttpClient
from .validators import get_value, run_validators
from .variables import substitute


def build_ctx(case_file, file_data, env, row_vars):
    """构建变量上下文：环境变量 < 文件级变量 < Excel 行数据 < 会话共享变量(extract)。"""
    ctx = {"BASE_URL": env.get("base_url", "")}
    ctx.update(env.get("variables", {}))
    ctx.update(file_data.get("variables", {}))
    ctx.update(row_vars or {})
    ctx.update(get_context(case_file))

    # 模块级 base_url 覆盖（支持 $ 变量引用，如不同微服务网关）
    if file_data.get("base_url"):
        ctx["BASE_URL"] = substitute(file_data["base_url"], ctx)
    return ctx


def run_case(case_file, file_data, case, row_vars, env):
    ctx = build_ctx(case_file, file_data, env, row_vars)
    case = substitute(case, ctx)

    req = case["request"]
    method = req["method"]
    url = req["url"]
    if not url.startswith(("http://", "https://")):
        url = ctx["BASE_URL"].rstrip("/") + "/" + url.lstrip("/")

    kwargs = {k: v for k, v in req.items() if k not in ("method", "url")}
    resp = HttpClient().request(method, url, **kwargs)

    # 断言前写入报告，失败时也能保留请求/响应信息便于排查
    _attach(method, url, resp)

    # 提取响应字段到会话共享上下文，供后续用例引用（如登录后传 token）
    for key, expr in case.get("extract", {}).items():
        set_var(case_file, key, get_value(resp, expr))

    run_validators(resp, case.get("validate", []))
    return resp


def _attach(method, url, resp):
    try:
        import allure
    except ImportError:
        return
    allure.attach(f"{method.upper()} {url}", "请求", allure.attachment_type.TEXT)
    allure.attach(f"{resp.status_code}\n{resp.text}", "响应", allure.attachment_type.TEXT)
