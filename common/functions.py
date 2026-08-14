# -*- coding: utf-8 -*-
"""公共函数白名单：YAML 里通过 ${函数名(参数)} 调用，只允许调用这里的函数。

新增函数只需在此定义（函数名不要以 _ 开头），YAML 即可使用，实现"收口"管理。
"""
import random
import string
import time


def timestamp():
    """当前 Unix 时间戳（秒）。"""
    return int(time.time())


def random_string(length=8):
    """随机字符串（默认 8 位）。"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_digits(length=6):
    """随机数字串（默认 6 位）。"""
    return "".join(random.choices(string.digits, k=length))


def random_phone():
    """随机手机号（11 位，1 开头）。"""
    return "1" + "".join(random.choices(string.digits, k=10))
