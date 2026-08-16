# 日志功能设计规格

- 日期：2026-08-16
- 状态：已评审待实现
- 关联：接口自动化测试框架（Pytest + YAML 零代码用例）

## 1. 背景

当前框架对用例执行过程的可见性依赖两处：

- **Allure 附件**：`core/runner.py` 的 `_attach` 为每个用例附带请求/响应文本，但需打开 HTML 报告才能看。
- **pytest 控制台**：`pytest.ini` 已开启 `-v`，但控制台输出由 pytest 捕获管理，无统一格式、无时间戳、无持久化。

缺少一套贯穿"用例执行 → 发请求 → 断言 → 结果"的标准日志，导致用例失败时排查要跨多个载体、无法回看历史运行。

## 2. 目标与非目标

### 目标

- 用例失败时，能从**一处**快速定位：用例名、请求（method + url）、响应状态码、断言失败详情、异常堆栈。
- 日志同时落地**文件 + 控制台**，文件便于回看，控制台便于 CI 实时观察。
- 纯文本格式，人眼可直接阅读。

### 非目标（YAGNI）

- 不做结构化 JSON 日志、不做日志采集/ELK 接入。
- 不做日志轮转（RotatingFileHandler）、不做按用例拆分的独立日志文件。
- 不做敏感信息脱敏（用户明确选择"原样记录"）。
- 不做结果通知改造（企微/钉钉通知保持现状）。

## 3. 关键决策

| 决策点 | 结论 |
|--------|------|
| 主要目的 | 失败排查 |
| 输出位置 | 文件 + 控制台 |
| 日志格式 | 纯文本 |
| 敏感信息 | 原样记录（不脱敏） |
| 技术选型 | Python 标准库 `logging`（零新依赖） |

## 4. 架构

### 4.1 模块划分

新增一个模块，改动三个既有文件：

| 文件 | 类型 | 职责 |
|------|------|------|
| `core/logger.py` | 新增 | 日志初始化 + 取 logger |
| `core/http_client.py` | 改动 | 埋点：HTTP 请求/响应 |
| `core/runner.py` | 改动 | 埋点：用例生命周期、断言、异常 |
| `conftest.py` | 改动 | `pytest_configure` 中初始化日志 |

### 4.2 `core/logger.py`

对外两个函数：

- `setup_logging(level=None, log_dir=None)`：幂等初始化根 logger，配置两个 handler：
  - `FileHandler` → `{log_dir}/test.log`，编码 UTF-8，`mode='w'`。
  - `StreamHandler` → 控制台（stderr）。
  - 统一格式：`%(asctime)s [%(levelname)s] %(message)s`。
  - `level` 与 `log_dir` 为空时分别从环境变量 `LOG_LEVEL`（默认 `INFO`）、`LOG_DIR`（默认 `logs`）读取。
  - 幂等：若已初始化过，直接返回，避免重复添加 handler。
  - 失败降级：目录不可写等异常时捕获并降级为仅控制台，不阻断测试。
- `get_logger(name)`：返回 `logging.getLogger(name)`。

### 4.3 埋点

`core/http_client.py`：

- 请求：`INFO` 记录 `请求 METHOD URL`，`DEBUG` 追加请求头与 body。
- 响应：`INFO` 记录 `响应 STATUS（耗时 Xms）`，`DEBUG` 追加响应头与 body。
- 记录耗时：`time.perf_counter()` 起止差值。

`core/runner.py`：

- 用例开始：`INFO` 记录 `用例开始：{模块名}::{用例名}`。
- extract：`DEBUG` 记录 `提取 {key} = {value}`。
- 断言结果：断言失败通过捕获的 `AssertionError` 用 `ERROR` 记录 `断言失败：{模块}::{用例} — {异常消息}`（异常消息已含操作符/表达式/期望/实际值，由 `validators.py` 抛出的 `AssertionError` 文案提供）；断言通过不逐条记录。
- 结果：`INFO` 记录 `用例结束：PASS` 或 `用例结束：FAIL`。
- 异常：捕获 `AssertionError` / 其他异常 → `ERROR` 记录 `用例失败：{异常}` 并 `logging` 输出 traceback → 重新 `raise`（保证 pytest 仍标记失败，Allure 附件与结果通知不受影响）。

`conftest.py`：

- `pytest_configure` 中调用 `setup_logging()`，保证用例执行前初始化；pytest-xdist 下各 worker 进程各自初始化，均生效。

### 4.4 xdist 并发处理

`pytest -n 4` 时主进程与各 worker 独立进程。策略：

- 文件 handler 统一 `mode='a'` 追加到 `logs/test.log`。为保证"每次运行覆盖"，主进程在 `pytest_configure` 中先清空该文件（`open(path, 'w').close()`）；pytest-xdist 的 worker 进程（通过 `PYTEST_XDIST_WORKER` 环境变量识别）不重复清空，直接 append。
- 并发写入可能出现行交错，纯文本调试场景可接受（每条日志含时间戳，可 grep 定位）。

## 5. 日志级别语义

| 级别 | 内容 |
|------|------|
| INFO（默认） | 用例开始/结束、请求 method+url、响应状态码与耗时、PASS/FAIL |
| DEBUG | 额外打印完整请求/响应头 + body（原样，不脱敏）、extract |
| ERROR | 用例失败、断言失败详情、异常与 traceback |

## 6. 配置

| 配置项 | 来源 | 默认值 | 说明 |
|--------|------|--------|------|
| 日志级别 | 环境变量 `LOG_LEVEL` | `INFO` | 可选 `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| 日志目录 | 环境变量 `LOG_DIR` | `logs` | 相对项目根 |

`.gitignore` 追加 `logs/`。

## 7. 数据流

```
conftest.pytest_configure ──> setup_logging()（初始化根 logger）
        │
        ▼
runner.run_case ──> logger.info(用例开始)
        │
        ▼
HttpClient.request ──> logger.info(请求) / logger.debug(请求头+body)
        │                 logger.info(响应 状态码 耗时) / logger.debug(响应头+body)
        ▼
runner.run_case ──> 断言结果、extract、PASS/FAIL
        │ 失败时：logger.error + traceback，随后重新 raise
        ▼
pytest 标记失败 ──> Allure 附件 / 结果通知（现有逻辑不变）
```

## 8. 错误处理

- 日志初始化失败（目录不可写、权限不足）：捕获后降级为仅控制台，不影响测试执行。
- 用例失败：日志记录后重新 `raise`，交由 pytest 现有失败处理链路（Allure、通知）不变。
- 日志写入自身异常：由 `logging` 内部吞掉（默认 `raiseExceptions` 行为），不阻断用例。

## 9. 验证

1. 运行 demo 用例：`pytest`，确认控制台出现日志、`logs/test.log` 生成。
2. 故意让一条用例断言失败，确认日志文件与控制台均能看到：用例名、请求 method+url、响应状态码、断言失败详情、异常堆栈。
3. 设置 `LOG_LEVEL=DEBUG` 运行，确认请求/响应头 + body 原样打印。
4. 运行 `pytest -n 4`，确认并发下日志仍正常写入 `logs/test.log`。

## 10. 文档

README.md 新增"日志"小节：说明日志位置（`logs/test.log`）、级别（`LOG_LEVEL`）、如何按用例名 grep 排查。

## 11. 范围边界

- 不新增第三方依赖（`requirements.txt` 不变）。
- 不改动 YAML 用例规范、不改动 `validators.py` / `variables.py` / `excel_loader.py` / `notifier.py` / `context.py` / `functions.py`。
