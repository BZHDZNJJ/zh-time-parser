# zh-time-parser

中文自然语言时间表达解析器：把「上个月」「最近7天」「Q1」「H1」「3月1号到3月15号」
这类中文说法解析成具体的日期范围，并支持「同比」「环比」这类**双区间**比较表达。

- **零依赖** —— 只用 Python 标准库，不需要 `dateparser` 等第三方日期库
- **可重复** —— 支持注入固定的 `today`，相对日期在测试中完全确定
- **不乱猜** —— 无法识别时返回空结果并给出 `recognition_status`，绝不把整段文本硬套成日期
- Python 3.8+

## 安装

```bash
pip install -e .
```

## 快速开始

```python
from zh_time_parser import extract_date_range_v2

r = extract_date_range_v2("最近7天")
print(r.start, r.end)      # 2026-08-03 2026-08-09
```

传入固定的 `today`，让相对日期可重复（推荐在测试中使用）：

```python
from datetime import datetime
from zh_time_parser import extract_date_range_v2

r = extract_date_range_v2("上个月", today=datetime(2026, 5, 24))
print(r.start, r.end)      # 2026-04-01 2026-04-30
print(r.label)             # 上个月
print(r.range_type)        # range   —— 区间形态
print(r.granularity)       # month   —— 时间粒度
```

### 两个入口的分工

本库有两个解析入口，**返回类型互不干扰**：

| 函数 | 解析对象 | 返回 |
| --- | --- | --- |
| `extract_date_range_v2()` | **一个**日期区间 | 恒为 `DateRange`（永不返回 `ComparisonRange`） |
| `extract_comparison_range()` | 同比/环比的**两个**区间 | `ComparisonRange`，无比较语义时为 `None` |

同比/环比需要同时表达「本期」与「对比期」，一个 `DateRange` 装不下，
因此单独用 `ComparisonRange`，而不是把对比期塞进 `point` / `boundary`：

```python
from datetime import datetime
from zh_time_parser import extract_comparison_range

result = extract_comparison_range(
    "Q2同比",
    today=datetime(2026, 8, 9),
)

assert result.current.start == "2026-04-01"
assert result.current.end == "2026-06-30"
assert result.comparison.start == "2025-04-01"
assert result.comparison.end == "2025-06-30"
```

无法识别时不会抛异常，而是返回空的 `DateRange`：

```python
r = extract_date_range_v2("张三 有 12345 个")
print(bool(r))                  # False
print(r.recognition_status)     # no_time_phrase
```

`recognition_status` 有三种取值：

| 值 | 含义 |
| --- | --- |
| `ok` | 成功解析出日期范围 |
| `phrase_not_supported` | 文本里有时间词，但当前规则解析不了 |
| `no_time_phrase` | 文本里根本没有时间词 |

## 公开 API

```python
from zh_time_parser import (
    DateRange,                 # 单区间结果数据类
    ComparisonRange,           # 双区间（同比/环比）结果数据类
    extract_date_range_v2,     # 推荐入口，返回 DateRange
    extract_comparison_range,  # 同比/环比入口，返回 ComparisonRange 或 None
    extract_date_range,        # 兼容入口，返回 (start, end)
    parse_time_expression,     # 兼容入口，返回 (start, end) 或 None
)
```

### `extract_date_range_v2(user_message, today=None, week_start='monday') -> DateRange`

主入口。`today` 默认取 `datetime.now()`；`week_start` 可选 `'monday'` 或 `'sunday'`。
**返回类型恒定为 `DateRange`**。若输入含**明确的比较表达**（同比 / 环比 / 去年同期 /
上年同期 / 较上期 / 比上期），本函数**不再按普通日期区间解析**，而是返回空 `DateRange`
（`recognition_status='phrase_not_supported'`、`range_type='unknown'`，`label` 提示改用
`extract_comparison_range`）。这是为了防止 `extract_date_range_v2("去年同期")` 误返回去年全年、
`extract_date_range_v2("上月环比")` 误只返回上个月。注意 `extract_comparison_range` 会先剥离比较词
再调用本函数，因此「本月同比」等正常比较解析不受影响（传入的是剥离后的「本月」）。

### `extract_comparison_range(user_message, today=None, week_start='monday') -> Optional[ComparisonRange]`

解析同比/环比，返回**本期 + 对比期**两个区间。无法确定比较语义时返回 `None`，
不抛异常、不编造区间。

### `DateRange`

`range_type`（区间的**形态**）与 `granularity`（时间**粒度**）是两个独立维度，
不要混用。例如「到2027年末」的 `range_type='range'` 而 `granularity='year'`。

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `start` | `Optional[str]` | `None` | 起始日期 `YYYY-MM-DD` |
| `end` | `Optional[str]` | `None` | 结束日期 `YYYY-MM-DD` |
| `range_type` | `str` | `'range'` | 区间形态：`range` / `point` / `quarter` / `ytd` / `unknown`（另有历史取值 `yoy` / `mom`，见下方说明） |
| `granularity` | `str` | `'day'` | 时间粒度：`day` / `week` / `month` / `quarter` / `half_year` / `year` |
| `original_text` | `str` | `''` | 命中的原始文本片段 |
| `label` | `str` | `''` | 人类可读标签，如「上个月」 |
| `is_relative` | `bool` | `False` | 是否相对 `today`（如「最近7天」为 `True`，写死日期为 `False`） |
| `includes_end` | `bool` | `True` | 是否含右端点（当前恒为 `True`，见 DESIGN.md） |
| `week_start` | `str` | `'monday'` | 本次解析使用的周起始日：`monday` / `sunday` |
| `confidence` | `float` | `1.0` | 置信度 0.0–1.0 |
| `recognition_status` | `str` | `'ok'` | `ok` / `phrase_not_supported` / `no_time_phrase` |
| `point` | `Optional[str]` | `None` | 截止点日期。仅「到X/截至X/月底/年末」这类强调截止边界的表达才填充；普通区间为 `None` |
| `boundary` | `Optional[str]` | `None` | 被强调的边界方向：`'end'` 表示强调结束边界；未强调为 `None` |

`point` / `boundary` 是**附加**信息：填充它们时 `start` / `end` 仍保留完整区间。
例如「到2027年末」→ `start='2027-01-01'`、`end='2027-12-31'`、`point='2027-12-31'`、
`boundary='end'`，便于调用方区分「时点计算」与「区间统计」。

**方法**

| 方法 | 说明 |
| --- | --- |
| `to_tuple()` | 返回 `(start, end)` |
| `to_dict()` | 返回含全部字段的 `dict`，可直接 JSON 序列化 |
| `bool(r)` | **`start` 和 `end` 同时存在**才为 `True`；只有其一仍为 `False` |
| `iter(r)` / `r[0]` | 支持解包与索引，兼容旧的 `(start, end)` 用法 |

> **关于 `range_type='yoy'` / `'mom'`**：同比/环比现由 `ComparisonRange` 表达，
> 这两个取值在当前解析链中已不可达，保留仅为向后兼容，新代码不要依赖。
> 详见 [DESIGN.md](DESIGN.md)。

### `ComparisonRange`

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `current` | `DateRange` | 必填 | 本期区间，必为有效 `DateRange` |
| `comparison` | `DateRange` | 必填 | 对比期区间，必为有效 `DateRange` |
| `comparison_type` | `str` | 必填 | `'yoy'`（同比）或 `'previous_period'`（环比） |
| `original_text` | `str` | `''` | 原始匹配文本 |
| `label` | `str` | `''` | 人类可读标签 |
| `confidence` | `float` | `1.0` | 置信度 0.0–1.0 |

构造时会校验：两个区间都必须有效、`comparison_type` 必须合法，否则抛 `ValueError`。
`to_dict()` 返回嵌套展开的 dict，可直接 JSON 序列化。

### 兼容 API

`extract_date_range(msg, today=None)` 返回 `(start, end)`，失败为 `(None, None)`；
`parse_time_expression(text, today=None)` 返回 `(start, end)`，失败为 `None`。

## 支持的表达

| 类别 | 示例 |
| --- | --- |
| 单日 | 今天、今日、当天、本日、昨天、昨日、前天、前日、明天 |
| 精确日期 | `2026-04-15`、`2026/04/15`、`2026年4月15日` |
| 周 | 本周、上周、下周、上上周、周一到周三、本周一到周五、本周至今 |
| 月 | 本月、上个月、下个月、上上个月、月初、月末、3月到5月、`1-3月` |
| 季度 | 本季度、上季度、下季度、Q1–Q4、`2026Q1`、2026年第一季度、Q1到Q2、上季度至今 |
| 年 | 今年、去年、前年、明年、2025年、25年、年初、年末、年初至今、YTD |
| 半年 | 上半年、下半年、全年至今、`H1`/`h1`/`H2`/`h2`、`2025H1`、`2025 H2`、`2025年H1`、`H1到H2` |
| 相对 | 最近N天/周/月/年、近N个月、近半年、近一年、过去N天 |
| 范围 | `2026-04-01 至 2026-04-30`、从X到Y、`X~Y` |
| 口语 | 5号到15号、3月1号到3月15号、上个月1号到今天、上月至今 |
| **同比** | 同比、去年同期、本月同比、上个月同比、今年同比去年、`Q2同比`、`2025Q1同比`、`H1同比`、`2025H2同比` |
| **环比** | 环比、本月环比、上个月环比、`Q2环比`、`Q1环比`、`H1环比`、`H2环比`、`2025Q1环比`、`2025H1环比` |

> **触发器收紧**：环比**只**由「环比 / 较上期 / 比上期」触发；单独的「环」字不再触发，
> 因此「环境数据 / 环节分析 / 循环统计 / 环岛记录」等不会被误判为环比。
> 同比只由「同比 / 去年同期 / 上年同期 / 同期」触发，且用负向前瞻排除
> 「同比例」与「同期生 / 同期刊 / 同期声」等近似普通词；环比也排除「环比例 / 环比较」。
> 单独出现的「环比率」仍按环比处理。

> **一次只支持一种比较类型**：若同一句话**同时**出现「同比」与「环比」
> （如「同比环比都要」「本月同比和环比」「Q2同比、环比」「同比及环比」），
> `extract_comparison_range` 会返回 `None`，**不会擅自选一个**——
> 同时为两种类型是丢失用户意图，应交给调用方澄清。未来若需要，可另行设计
> 列表型 API（如返回 `list[ComparisonRange]`），本次**不扩展**返回类型。
> 旧 `DateRange.range_type` 的 `'yoy'` / `'mom'` 取值在当前解析链中已不可达（见 DESIGN.md）。

### 「近半年」与「H1/H2」的区别

这是两种**完全不同**的语义，务必区分：

| 表达 | 含义 | 以 `today=2026-08-09` 为例 |
| --- | --- | --- |
| `近半年` | 滑动窗口，约 **183 天** | `2026-02-07 ~ 2026-08-09` |
| `H1` | 自然半年（上半年） | `2026-01-01 ~ 2026-06-30` |
| `H2` | 自然半年（下半年） | `2026-07-01 ~ 2026-12-31` |

`H1`/`H2` 的 `granularity='half_year'`；`近半年` 保持原有的滑动天数语义，
`granularity` 不是 `half_year`。

暂**不支持**跨年份半年范围（如 `2025H2到2026H1`），以免在未校验起止顺序时给出错误区间。

## 同比 / 环比的精确定义

**同比（`comparison_type='yoy'`）**
当前区间与**上一年度相同日历位置**的区间比较。实现为整体平移一年（保持月/日不变），
**不使用固定 365 天**。上一年度没有 2月29日时回退到 2月28日。

**环比（`comparison_type='previous_period'`）**
与**紧邻的同粒度前一个周期**比较。中文「环比」统一建模为 `previous_period`，
而不是一律当作 month-over-month —— 季度的环比是上一季度，半年的环比是上一个半年。
**不使用固定 30 天**：

- 完整周期 → 与完整前周期比，各自使用**真实月末**（7月31天 vs 6月30天）
- 进行中的周期 → 使用**相同已过天数**，避免拿 9 天和完整上月比

以 `today=2026-08-09` 为例：

| 输入 | current | comparison |
| --- | --- | --- |
| `本月同比` | `2026-08-01 ~ 2026-08-09` | `2025-08-01 ~ 2025-08-09` |
| `上个月同比` | `2026-07-01 ~ 2026-07-31` | `2025-07-01 ~ 2025-07-31` |
| `同比` / `去年同期` | `2026-01-01 ~ 2026-08-09` | `2025-01-01 ~ 2025-08-09` |
| `本月环比` | `2026-08-01 ~ 2026-08-09` | `2026-07-01 ~ 2026-07-09` |
| `上个月环比` | `2026-07-01 ~ 2026-07-31` | `2026-06-01 ~ 2026-06-30` |
| `Q1环比` | `2026-01-01 ~ 2026-03-31` | `2025-10-01 ~ 2025-12-31` |
| `H1环比` | `2026-01-01 ~ 2026-06-30` | `2025-07-01 ~ 2025-12-31` |

单独出现的「同比」默认解释为「今年截至今天 同比 去年同期」；
单独出现的「环比」默认解释为「本月截至今天 vs 上月相同已过天数」。

## 项目结构

```
src/zh_time_parser/
├── __init__.py            # 公开 API
├── date_parser.py         # 主入口，只负责调度解析顺序
├── models.py              # DateRange / ComparisonRange + 时间常量
├── normalization.py       # 格式化、校验、中文数字、月份日历工具
├── explicit_parser.py     # 显式/精确日期、中文日期段、号段
├── relative_parser.py     # 最近N天/周/月/年、单日同义词
├── week_parser.py         # 周相关
├── month_parser.py        # 月相关
├── quarter_parser.py      # 季度相关
├── year_parser.py         # 年/半年相关（含 H1/H2）
├── boundary_parser.py     # 到X/截至X 等截止点
└── comparison_parser.py   # 同比/环比，复用上述解析器 + 日历平移

tests/
├── test_date_parse.py         # 解析规则（主）
├── test_date_parser.py        # 解析规则（补充）
├── test_half_year.py          # H1/H2 半年表达
├── test_comparison.py         # 同比/环比解析
├── test_comparison_fix.py      # 比较词误识别回归（环/默认周期/同环比并存/旧API保护）
├── test_comparison_boundary.py  # 比较词边界修复（同期生/同比例/环比例/白名单/旧API边界）
├── test_comparison_model.py   # ComparisonRange 契约
├── test_models.py             # DateRange 契约：to_dict / __bool__ / 字段默认值
└── test_error_propagation.py  # 异常边界：编程错误必须暴露
```

解析器按优先级依次尝试（强匹配在前），命中即返回；顺序定义在 `date_parser.py`。

## 错误处理

无法识别时返回空 `DateRange`，**不抛异常**。畸形输入（不存在的日历日、
超大数字等）在解析链内部被跳过，安全降级为 `phrase_not_supported`。

但**编程错误不会被隐藏**：`NameError` / `AttributeError` / `TypeError`
会原样抛出，而不是被伪装成「解析不了」。解析链只吞掉
`ValueError` / `OverflowError` / `KeyError` / `IndexError`
这类由输入导致的可预期异常。`tests/test_error_propagation.py` 锁定了这一契约。

## 开发

```bash
pip install -e ".[dev]"

python -m ruff check src tests    # 静态检查
python -m pytest tests -v         # 测试
```

当前 373 项测试全部通过，ruff 无告警。CI 在 Python 3.8–3.12 上同时运行两者。

## 已知语义分歧

「本月」截断到今天而「本季度」返回完整季度、「最近N月」是滑动窗口而非自然月、
两位年份一律补 `20` 前缀（`99年 → 2099`）等问题**尚未定论**，
已完整记录在 [DESIGN.md](DESIGN.md)，抽离阶段一律保持原行为不变。

## License

MIT
