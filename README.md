# 接口自动化测试框架（零代码用例）

Pytest 引擎 + YAML 用例 + 多环境配置的轻量接口自动化测试框架。测试人员只需在 `cases/` 目录维护 YAML 文件即可编写用例，无需改代码。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行全部用例（串行）
pytest

# 并发执行（按 YAML 文件并发，文件内串行）
pytest -n 4

# 按标记运行（冒烟）
pytest -m smoke

pytest -k "case下的yaml文件名称"  # 只跑某个 YAML 文件
pytest -k "查询待办并提取用户ID" # 只跑某条用例
pytest -m smoke / pytest -m P0  # 按tag跑

# 切换环境
TEST_ENV=prod pytest
```

## 目录结构

```
auto_test/
├── conftest.py              # pytest 钩子：动态注册用例 + 并发分组 + 结果通知
├── test_api.py              # 唯一测试函数（所有 YAML 汇聚于此）
├── pytest.ini               # 标记注册、运行配置（含 --dist=loadgroup）
├── requirements.txt
├── Jenkinsfile              # Jenkins 流水线模板
├── .gitlab-ci.yml           # GitLab CI 流水线模板
├── run_report.bat           # 一键运行 + 生成 Allure 报告
├── config/
│   ├── env.yaml             # 多环境配置（base_url、全局变量）
│   └── notify.yaml          # 结果通知配置（企微/钉钉）
├── data/                    # ★ Excel 数据驱动文件（业务同学可维护）
│   └── todo_ids.xlsx
├── cases/                   # ★ 测试人员只维护这里
│   └── demo/
│       ├── demo.yaml
│       ├── demo_m2.yaml
│       └── demo_m4_excel.yaml
├── common/                  # ★ 公共函数白名单（${fn()} 调用）
│   └── functions.py
├── core/                    # ★ 引擎（开发维护，测试人员不碰）
│   ├── config.py            #   环境加载
│   ├── yaml_loader.py       #   YAML 扫描加载 + Excel 展开
│   ├── excel_loader.py      #   Excel 数据读取
│   ├── variables.py         #   $var / ${fn()} 替换
│   ├── functions.py         #   公共函数注册表
│   ├── context.py           #   文件级共享上下文（extract 传值）
│   ├── http_client.py       #   HTTP 请求封装
│   ├── validators.py        #   断言器
│   ├── runner.py            #   用例执行编排 + Allure 附件
│   └── notifier.py          #   结果通知（企微/钉钉）
└── README.md
```

## YAML 用例编写规范

### 基本结构

```yaml
name: 模块名
base_url: https://api.example.com   # 可选，覆盖全局 BASE_URL（不同微服务网关）
variables:                          # 文件级变量（本文件所有用例可用）
  user_id: 1

cases:                              # 用例列表（按顺序执行）
  - name: 用例名称
    tags: [smoke, P0]               # 标记，可用 pytest -m smoke 过滤
    request:
      method: POST
      url: /api/login
      headers:
        Content-Type: application/json
      json:                         # 或用 params / data / form
        username: $user_id          # $变量 引用
        sign: ${timestamp()}        # ${函数()} 引用公共函数
    extract:                        # 提取响应字段到共享上下文，供后续用例用
      token: body.data.token
    validate:                       # 断言列表，全部通过才算用例通过
      - eq: [status_code, 200]
      - eq: [body.code, 0]
      - exists: [body.data.token]
      - schema: [body, {type: object, required: [code, data]}]
```

### 变量引用

- `$name` 或 `${name}`：引用上下文变量
- `${fn(args)}`：调用 `common/functions.py` 中的公共函数（白名单收口）
- 变量来源优先级：环境 `variables` < 文件级 `variables` < Excel 行数据 < 会话共享变量（`extract` 提取）
- `extract` 提取的值在**同一 YAML 文件内**跨用例共享（如登录用例提取 token，后续用例 `$token` 引用）

### 断言操作符

| 操作符 | 用法 | 说明 |
|--------|------|------|
| `eq` | `eq: [取值表达式, 期望值]` | 相等 |
| `ne` | `ne: [取值表达式, 期望值]` | 不相等 |
| `contains` | `contains: [取值表达式, 子串]` | 包含子串 |
| `exists` | `exists: [取值表达式]` | 字段存在 |
| `schema` | `schema: [取值表达式, JSON Schema]` | JSON Schema 结构校验 |
| `is_json` | `is_json: []` | 响应体为合法 JSON |

### 取值表达式（断言/extract 通用）

| 表达式 | 含义 |
|--------|------|
| `status_code` | HTTP 状态码 |
| `text` | 响应文本 |
| `headers.Content-Type` | 响应头字段 |
| `body.data.token` | JSON 响应体字段路径（列表用下标，如 `body.list.0.id`） |

### 内置公共函数（common/functions.py）

| 函数 | 说明 |
|------|------|
| `${timestamp()}` | 当前时间戳（秒） |
| `${random_string(10)}` | 随机字符串（参数为长度） |
| `${random_digits(6)}` | 随机数字串 |
| `${random_phone()}` | 随机手机号 |

## Excel 数据驱动

当用例需要批量参数化时，用 Excel 代替在 YAML 里写多份用例。Excel 首行为表头（变量名），每行一组数据，**每行数据自动生成一个用例实例**。

```yaml
name: 模块名
data:
  file: data/user_login.xlsx   # Excel 路径（相对项目根）
  sheet: 登录数据                # 可选，默认第一个 sheet
cases:
  - name: 登录
    request:
      method: POST
      url: /api/login
      json:
        username: $username      # $username 来自 Excel 的 username 列
        password: $password
    validate:
      - eq: [status_code, 200]
      - eq: [body.code, $expect_code]
```

对应 Excel（`data/user_login.xlsx`）：

| username | password | expect_code |
|----------|----------|-------------|
| admin | 123456 | 0 |
| test | abc123 | 0 |

## 并发执行

```bash
pytest -n 4     # 已内置 --dist=loadgroup，无需额外参数
```

- 同一 YAML 文件内的用例**串行**执行（保证 `extract` 顺序传值）
- 不同 YAML 文件之间**并发**执行
- `extract` 变量按文件隔离，并发下不会串扰

## 如何新增用例

1. 在 `cases/` 下按业务模块建子目录（如 `cases/login/login.yaml`）
2. 按上面规范写 YAML 文件（需要参数化时配合 Excel 数据驱动）
3. 运行 `pytest`，自动被收集执行

## 如何新增公共函数

在 `common/functions.py` 里定义函数（函数名不要以 `_` 开头），YAML 即可通过 `${函数名(参数)}` 调用。

## 运行日志

每次运行会落一份纯文本日志（同时打印到控制台），串行写 `logs/test.log`、并发写 `logs/test-gw*.log`，用于用例失败排查。

- **位置**：串行运行写 `logs/test.log`；`pytest -n N` 并发时每个 worker 写独立的 `logs/test-gw*.log`（每次运行覆盖上一次）
- **级别**：默认 `INFO`；设环境变量 `LOG_LEVEL=DEBUG` 打印完整请求/响应头与 body
- **排查**：失败时按用例名 grep，例如 `grep "用例名" logs/test*.log`，可看到请求/响应/断言失败详情/异常堆栈

```bash
LOG_LEVEL=DEBUG pytest     # 更详细（含请求/响应头与 body）
```

## 测试报告（Allure）

报告按 YAML 的模块名（feature）、用例名（title）、tags 展示，并附带每个用例的请求/响应附件。

```bash
# 1. 安装 allure 命令行工具（报告查看器，与 pip 的 allure-pytest 是两个东西）
#    Windows: scoop install allure   或下载 allure-commandline 解压后加入 PATH

# 2. 运行并生成报告数据
python -m pytest --alluredir=reports/allure-results

# 3. 生成并打开报告
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report

# 或双击 run_report.bat 一键完成 2、3 两步
```

## 结果通知（企业微信/钉钉）

编辑 `config/notify.yaml`：

```yaml
enabled: true
type: wecom      # 或 dingtalk
webhook: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
```

测试结束后自动汇总通过/失败用例并推送（默认关闭，未填 webhook 不发送）。

## CI/CD 集成

- **Jenkins**：见 `Jenkinsfile`（需安装 Allure Jenkins 插件）
- **GitLab**：见 `.gitlab-ci.yml`（归档 Allure 结果，可接 GitLab 的 Allure 报告）

## 进阶扩展（Mock / 契约测试）

依赖第三方服务时可引入 Mock 与契约测试，作为独立能力与本框架配合：

- **Mock**：用 [WireMock](https://wiremock.org/) 或 [MockServer](https://www.mock-server.com/) 模拟依赖接口，在 `config/env.yaml` 里把被测系统的 `base_url` 指向 Mock 服务即可，用例无需改动。
- **契约测试**：用 [Pact](https://pact.io/) 在服务提供方与消费方之间校验接口契约，可与本框架的 YAML 用例互补。
