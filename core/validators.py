# -*- coding: utf-8 -*-
"""断言器：YAML 里 validate 列表的每一条对应一个操作符。"""


def get_value(resp, expr):
    """根据取值表达式从响应里取值。

    - status_code -> 状态码
    - text        -> 响应文本
    - headers.X   -> 响应头字段
    - body.x.y    -> JSON 响应体字段路径（支持 list 下标，如 body.data.0.name）
    """
    if expr == "status_code":
        return resp.status_code
    if expr == "text":
        return resp.text
    parts = expr.split(".")
    if parts[0] == "headers":
        return resp.headers.get(".".join(parts[1:]))
    if parts[0] == "body":
        cur = resp.json()
        for p in parts[1:]:
            if isinstance(cur, list) and p.isdigit():
                cur = cur[int(p)]
            else:
                cur = cur[p]
        return cur
    raise ValueError(f"不支持的取值表达式: {expr}")


def _eq(resp, expr, expected):
    actual = get_value(resp, expr)
    assert actual == expected, f"断言失败: {expr} 期望 {expected!r}，实际 {actual!r}"


def _ne(resp, expr, expected):
    actual = get_value(resp, expr)
    assert actual != expected, f"断言失败: {expr} 不应等于 {expected!r}"


def _contains(resp, expr, substr):
    actual = get_value(resp, expr)
    assert substr in str(actual), f"断言失败: {expr} 未包含 {substr!r}，实际 {actual!r}"


def _exists(resp, expr):
    try:
        actual = get_value(resp, expr)
        assert actual is not None, f"断言失败: {expr} 不存在"
    except (KeyError, IndexError, TypeError):
        raise AssertionError(f"断言失败: {expr} 不存在")


def _schema(resp, expr, schema):
    import jsonschema

    instance = get_value(resp, expr)
    try:
        jsonschema.validate(instance, schema)
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "$"
        raise AssertionError(f"JSON Schema 校验失败: {e.message} (路径: {path})")


def _is_json(resp):
    """断言响应体是合法的 JSON 格式。"""
    try:
        resp.json()
    except ValueError:
        raise AssertionError(
            f"断言失败: 响应不是合法的 JSON 格式，Content-Type={resp.headers.get('Content-Type')!r}"
        )


VALIDATORS = {
    "eq": _eq,
    "ne": _ne,
    "contains": _contains,
    "exists": _exists,
    "schema": _schema,
    "is_json": _is_json,
}


def run_validators(resp, rules):
    for rule in rules or []:
        # rule 形如 {"eq": ["status_code", 200]}
        (op, args), = rule.items()
        fn = VALIDATORS.get(op)
        if fn is None:
            raise AssertionError(f"未知断言操作符: {op}")
        fn(resp, *args)
