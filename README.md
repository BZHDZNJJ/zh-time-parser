# zh-time-parser

中文自然语言时间表达解析器：把「上个月」「最近7天」「Q1」「H1」「3月1号到3月15号」
这类中文说法解析成具体的日期范围，并支持「同比」「环比」这类**双区间**比较表达，
以及「明天下午3点」这类精确日期时刻。

## 为什么需要

这个项目最初并不是作为一个独立的时间解析库设计的。

它最早是我为自己的 Agent 系统实现的一个内部模块。Agent 接收自然语言查询并将其转换为结构化请求的过程中，时间表达是一个高频、同时也最容易产生歧义的问题。

起初只需要处理简单的日期和范围。但随着使用场景增加，需要理解的表达逐渐扩展到「上个月」「最近几天」「今年以来」「Q2」「去年同期」等更自然的中文时间语义。

在继续开发的过程中我意识到，这部分能力不依赖我的 Agent，也不依赖某种具体业务。任何需要让程序理解中文时间表达的系统——Agent、BI、自然语言查询、搜索、报表、工作流——都可能遇到同样的问题。

于是我把这部分从原有系统中独立出来，重新整理和泛化，形成了 **zh-time-parser**。

它的目标很简单：**将自然语言中的中文时间表达，转换为稳定、结构化、可供下游程序直接使用的时间语义。**

### 为什么不用现有的方案

在决定独立开发之前，我评估过几种常见做法，每一种都有明确的不足：

| 方案 | 问题 |
|------|------|
| 手写正则 | 中文时间表达的多样性远超正则能覆盖的范围。「上个月1号到今天」「Q2同比」「上个月的下个月」——每增加一种模式就要写一条新正则，很快变成不可维护的规则泥潭 |
| `dateparser` 等英文日期库 | 对中文表达完全无能为力。`"上个月"` `"去年同期"` 这类基础中文时间词都识别不了，更不用说同比/环比、口语号段、农历或中文数字 |
| 调用大模型 | 引入网络延迟和不确定性。同一个"最近7天"，不同模型、甚至同一模型的不同调用可能返回略有差异的结果。对于需要确定性输出的查询系统、报表或自动化任务，这种不可复现性是不可接受的 |
| 用固定常量近似 | 不少系统用 `30天 ≈ 一个月`、`365天 ≈ 一年` 来简化计算，但在财务、合同、SLA 等对日历精度有要求的场景中，这种近似会导致边界错误 |

### zh-time-parser 的优势

- **零依赖** —— 纯 Python 标准库实现，不需要 `dateparser`、不需要网络、不需要 GPU
- **延迟低** —— 纯 CPU 正则 + 日历计算，单次解析通常在微秒到毫秒级，不涉及任何 I/O
- **确定性高** —— 同样的输入、同样的 `today`，输出完全一致。支持注入固定 `today`，测试可重复
- **稳定性高** —— 不依赖外部服务，不受 API 限流、模型更新、网络波动影响。1.x 语义已冻结，不会悄悄改变行为
- **不乱猜** —— 无法识别时返回空结果并给出 `recognition_status`；模糊表达（「最近几天」）只返回语义意图，不擅自编造日期
- Python 3.8+

### 能力概览

| 功能 | 示例 | 入口函数 | 返回类型 |
|------|------|----------|----------|
| 日期范围 | `最近7天` `上个月` `Q1` `去年` `本周` | `extract_date_range_v2()` | `DateRange` |
| 同比/环比 | `本月同比` `Q2环比` `去年同期` | `extract_comparison_range()` | `ComparisonRange` |
| 日期时刻 | `明天下午3点` `昨天中午` `晚上八点半` | `extract_datetime_point()` | `DateTimePoint` |
| 相对时长 | `半小时后` `两周前` `过三天` | `extract_relative_time()` | `RelativeTime` |
| 带时刻区间 | `8月1日至昨天中午` `直到明天下午3点` | `extract_datetime_range()` | `DateTimeRange` |
| 事件顺序 | `最近一次` `倒数第二次` `最近3次` | `extract_temporal_selector()` | `TemporalSelector` |
| 模糊时间 | `最近几天` `前阵子` `晚一点` `近期` | `extract_ambiguous_temporal()` | `AmbiguousTemporal` |
| 筛选边界 | `截至月底` `周五之前` `从明天开始` | `extract_temporal_boundary()` | `TemporalBoundary` |
| 评估锚点 | `在昨天的时候` `到月底的时候` | `extract_temporal_anchor()` | `TemporalAnchor` |

### 适用场景

**Agent / 智能助手**
用户说「帮我查上个月的数据」，Agent 需要把「上个月」变成 `2026-07-01 ~ 2026-07-31` 才能调 API 或写 SQL。中文时间解析是自然语言接口的必备组件。

**BI / 自然语言查询**
业务人员输入「今年 Q2 同比去年 Q2」，系统解析出本期和对比期两个区间，自动生成对比图表或两段 SQL。

**客服 / 工单系统**
用户问「我前天提交的工单怎么还没处理」，系统解析出日期后自动筛选对应时间范围的工单。

**报表 / 数据看板**
「最近 7 天新增用户」「本月初至今收入」——前端直接传中文短语，后端统一解析，避免每个报表硬编码日期计算逻辑。

**搜索引擎 / 知识库**
搜索框输入「上周发布的需求文档」，解析出日期范围后过滤索引；用 `TemporalSelector` 选「最近 3 次变更记录」。

**工作流 / 自动化任务**
定时任务配置「每季度最后一天执行」；任务描述「截至明天下午 3 点未处理的工单」，用 `TemporalBoundary` 直接映射为 `<` / `<=` 查询条件。

**日志 / 监控查询**
运维输入「最近半小时的错误日志」或「从昨晚 8 点到现在的报警」，解析为精确时间范围后查询日志平台。

**招聘 / 简历筛选**
筛选条件中的日期字段（如"2024 年入职""去年至今在某公司"），解析为具体日期后自动匹配候选人或计算工作年限。

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

### 九个入口的分工

本库有九个解析入口，**返回类型互不干扰**：

| 函数 | 解析对象 | 返回 |
| --- | --- | --- |
| `extract_date_range_v2()` | **一个**日期区间 | 恒为 `DateRange`（永不返回 `ComparisonRange`） |
| `extract_comparison_range()` | 同比/环比的**两个**区间 | `ComparisonRange`，无比较语义时为 `None` |
| `extract_datetime_point()` | 日期 + 时刻 | 恒为 `DateTimePoint` |
| `extract_relative_time()` | 锚点 + 时长 | 恒为 `RelativeTime` |
| `extract_datetime_range()` | 带具体时刻的区间或单边界 | 恒为 `DateTimeRange` |
| `extract_temporal_selector()` | 按事件顺序选择若干次 | 恒为 `TemporalSelector`，可携带 `DateRange` |
| `extract_ambiguous_temporal()` | 识别模糊时间意图但不猜值 | 恒为 `AmbiguousTemporal` |
| `extract_temporal_boundary()` | 单侧截止/开始边界 | 恒为 `TemporalBoundary` |
| `extract_temporal_anchor()` | 站在某个时点评估（as-of） | 恒为 `TemporalAnchor` |

日期时刻使用独立入口，不进入 `DateRange` 的调度链：

```python
from datetime import datetime
from zh_time_parser import extract_datetime_point

result = extract_datetime_point(
    "明天下午3点",
    today=datetime(2026, 8, 11),
)
assert result.datetime == "2026-08-12 15:00:00"
```

支持「昨天中午」「今天晚上8点半」「下周三上午10点」「8月20日14:30」
「后天凌晨2点」等表达。
「今晚」「明早」没有明确钟点，约定分别解析为 20:00、08:00；此时
`precision='period'`、`confidence=0.7`，调用方可以据此要求用户确认。

相对时长同样使用独立入口：

```python
from datetime import datetime
from zh_time_parser import extract_relative_time

result = extract_relative_time(
    "半小时后",
    anchor=datetime(2026, 8, 11, 12, 0),
)
assert result.value == 30
assert result.unit == "minute"
assert result.direction == "future"
assert result.resolved_at == "2026-08-11 12:30"
```

当区间边界包含具体时刻时，使用 `DateTimeRange`：

```python
from datetime import datetime
from zh_time_parser import extract_datetime_range

result = extract_datetime_range(
    "8月1日至昨天中午",
    today=datetime(2026, 8, 11, 12, 0),
)
assert result.start == "2026-08-01 00:00:00"
assert result.end == "2026-08-10 12:00:00"

# 兼容只接受 YYYY-MM-DD 的旧系统，但该投影会丢失“中午”的精度。
assert result.to_date_tuple() == ("2026-08-01", "2026-08-10")
assert result.precision_lost is True
```

“最近一次”描述的是事件顺序，不会猜测具体日期：

```python
from datetime import datetime
from zh_time_parser import extract_temporal_selector

result = extract_temporal_selector(
    "上个月最近3次",
    today=datetime(2026, 8, 11),
)
assert result.order == "latest"
assert result.limit == 3
assert result.offset == 0
assert result.date_range.start == "2026-07-01"
assert result.date_range.end == "2026-07-31"
```

模糊时间只识别意图，不强行生成日期：

```python
from zh_time_parser import extract_ambiguous_temporal

result = extract_ambiguous_temporal("最近几天")
assert result.to_dict()["type"] == "date_range"
assert result.status == "ambiguous"
assert result.direction == "recent"
assert result.unit == "day"
assert result.value is None
```

截止或开始语义使用单侧边界，而不是普通日期区间：

```python
from datetime import datetime
from zh_time_parser import extract_temporal_boundary

result = extract_temporal_boundary(
    "三天以内",
    today=datetime(2026, 8, 11, 12, 0),
)
assert result.operator == "<="
assert result.value == "2026-08-14 12:00"
assert result.value_type == "datetime"
assert result.duration.value == 3
assert result.duration.unit == "day"
```

“在某日的时候”是评估时钟锚点，不是筛选边界：

```python
from datetime import datetime
from zh_time_parser import extract_temporal_anchor

result = extract_temporal_anchor(
    "到这个月底的时候客户欠款超期金额是多少",
    today=datetime(2026, 8, 11, 12, 0),
)
assert result.mode == "as_of"
assert result.value == "2026-08-31"
assert result.value_type == "date"
assert result.is_future is True
```

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

`recognition_status` 有四种取值：

| 值 | 含义 |
| --- | --- |
| `ok` | 成功解析出日期范围 |
| `phrase_not_supported` | 文本里有时间词，但当前规则解析不了 |
| `no_time_phrase` | 文本里根本没有时间词 |
| `ambiguous` | 识别到模糊时间意图，但缺少确定数值；应追问或由上层应用策略处理 |

## 公开 API

```python
from zh_time_parser import (
    DateRange,                 # 单区间结果数据类
    DateTimePoint,             # 日期时刻结果数据类
    RelativeTime,              # 锚点 + 时长结果数据类
    DateTimeRange,             # 带时刻的区间或单边界
    TemporalSelector,          # 事件顺序选择器，可携带 DateRange
    AmbiguousTemporal,         # 模糊时间语义，不包含猜测出的日期
    TemporalBoundary,          # < / <= / > / >= 单侧时间边界
    TemporalAnchor,            # as-of 评估时钟锚点
    ComparisonRange,           # 双区间（同比/环比）结果数据类
    extract_date_range_v2,     # 推荐入口，返回 DateRange
    extract_datetime_point,    # 日期时刻入口，返回 DateTimePoint
    extract_relative_time,     # 相对时长入口，返回 RelativeTime
    extract_datetime_range,    # 带时刻区间入口，返回 DateTimeRange
    extract_temporal_selector, # 事件顺序选择器入口
    extract_ambiguous_temporal,# 模糊时间识别入口
    extract_temporal_boundary, # Deadline / Boundary 入口
    extract_temporal_anchor,   # “在某时点看”的评估锚点入口
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

### `extract_datetime_point(user_message, today=None, week_start='monday') -> DateTimePoint`

解析一个日期时刻，输出格式固定为 `YYYY-MM-DD HH:MM:SS`。无法识别时返回空的
`DateTimePoint`，并通过 `recognition_status` 区分无时间表达与暂不支持的表达。
未写日期的明确钟点按今天解释；未写年份的月日按 `today` 所在年份解释。

`DateTimePoint` 字段包括 `datetime`、`original_text`、`label`、`is_relative`、
`precision`、`confidence` 和 `recognition_status`，支持 `bool(result)`、`repr(result)`
与 `to_dict()`。

### `extract_relative_time(user_message, anchor=None) -> RelativeTime`

解析“半小时后”“两周前”“再过三天”这类相对于时间锚点的时长表达。
`anchor` 默认为 `datetime.now()`；结果精确到分钟，并同时保留标准化后的 `value`、
`unit`（`minute` / `hour` / `day` / `week` / `month`）和 `direction`
（`future` / `past`）。其中“半小时”标准化为 `value=30, unit='minute'`。

月份按真实日历月平移，不按固定 30 天计算；目标月份不存在同一天时回退到月末，
例如 2026-01-31 的“一个月后”为 2026-02-28 09:30（锚点时间为 09:30 时）。
无法识别时返回空的 `RelativeTime`。该入口不会改变或接管 `DateRange` 解析。

### `extract_datetime_range(user_message, today=None, week_start='monday') -> DateTimeRange`

解析“8月1日至昨天中午”这类带具体时刻的区间，也支持“直到昨天中午”这种只能
确定结束边界的表达。后者返回 `start=None`、`end='2026-08-10 12:00:00'`。

为了兼容只接受日期的旧系统，结果同时提供 `date_start` / `date_end` 和
`to_date_tuple(policy=...)`：

- `calendar_date`（默认）：取边界所在日期，例如中午投影为当天；可能多查当天下午。
- `completed_days`：只返回完整包含的自然日，例如结束于昨天中午时投影到前天；会漏掉昨天上午。
- `reject_lossy`：存在时刻精度损失时抛出 `ValueError`，适合不允许改变语义的调用方。

`precision_lost=True` 明确表示日期投影是有损的。精确的 `start/end` 始终保留，
不会因为旧系统只能接收日期而丢弃原始语义。

### `extract_temporal_selector(user_message, today=None, week_start='monday') -> TemporalSelector`

解析“最近一次”“最早一次”“最近3次”“倒数第二次”等事件顺序表达，不虚构事件日期。
结果由以下核心字段组成：

- `order`：`latest` 或 `earliest`。
- `limit`：需要多少条事件。
- `offset`：跳过多少条；“倒数第二次”为 `latest + limit 1 + offset 1`。
- `date_range`：同句中存在日期约束时携带对应 `DateRange`，否则为 `None`。

因此“去年最近一次”为去年范围加 `latest/1`，“上个月最近3次”为上个月范围加
`latest/3`。调用方可以直接映射到 SQL 的 `ORDER BY`、`LIMIT`、`OFFSET`；不支持
顺序选择的调用方可以不调用这个独立入口。

### `extract_ambiguous_temporal(user_message) -> AmbiguousTemporal`

识别“最近几天/几周/几个月/几年”“过几小时”“最近一段时间”“前段时间”
“过段时间”“不久以后”“很早以前”“晚一点”“月底左右”“近期”等模糊表达，
只返回 `type`、`direction`、`unit` 等已知语义，`value` 始终为 `None`。
上层可以据此追问、应用自己的默认值或扩大搜索召回范围。

`extract_date_range_v2()` 对这些明确模糊表达设有防猜保护：返回空 `DateRange`，
`recognition_status='ambiguous'`，不会把“最近几天”或“近几年”擅自解释为 2 天、
7 天或 2 年。底层中文数字解析也不再把“几”映射成任何具体数字。
有明确数值的“最近7天”不受影响。

同一个单区间表达若包含多个范围连接符，例如“从3月到5月到昨天”，由于无法确定
唯一结合顺序，`DateRange` / `DateTimeRange` 会返回 `phrase_not_supported`，不会静默
丢掉前半段并只返回“昨天”。

### `extract_temporal_boundary(user_message, today=None, week_start='monday') -> TemporalBoundary`

解析 Deadline / Boundary 单侧比较语义，可直接映射到 SQL、SLA 或任务规则：

| 表达 | `operator` | 示例 `value`（`today=2026-08-11 12:00`） |
| --- | --- | --- |
| 周五之前 | `<` | `2026-08-14` |
| 月底以前 | `<` | `2026-08-31` |
| 三天以内 | `<=` | `2026-08-14 12:00` |
| 两小时内 | `<=` | `2026-08-11 14:00` |
| 从明天开始 | `>=` | `2026-08-12` |
| 下周以后 | `>=` | `2026-08-17` |
| 截至月底 | `<=` | `2026-08-31` |
| 最迟周三 | `<=` | `2026-08-12` |

结果同时提供 `value_type='date'/'datetime'`。相对时长边界还会在 `duration` 中嵌套
原始 `RelativeTime`，避免计算出截止点后丢失“三天”或“两小时”的 SLA 定义。
该解析器为独立入口，不改变 `DateRange` 的闭区间契约。

### `extract_temporal_anchor(user_message, today=None, week_start='monday') -> TemporalAnchor`

解析“在昨天的时候”“到这个月底的时候”等 as-of 评估语义。它只改变下游进行状态
判断时采用的参考时钟，不生成 `<` / `<=` 等记录筛选条件：

| 表达 | 结果 |
| --- | --- |
| 截至昨天 | `TemporalBoundary(operator='<=', value='2026-08-10')` |
| 在昨天的时候 | `TemporalAnchor(mode='as_of', value='2026-08-10')` |
| 截至月底 | `TemporalBoundary(operator='<=', value='2026-08-31')` |
| 到这个月底的时候 | `TemporalAnchor(mode='as_of', value='2026-08-31', is_future=True)` |

如果表达只有一个时间段而没有确定评估日，例如“在下个月的时候”，本入口不会擅自选择
月初或月末，而是返回空结果和 `phrase_not_supported`。这是独立 API；原有 `DateRange`
和 `TemporalBoundary` 的解析顺序、字段与返回类型均未改变。

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
| `recognition_status` | `str` | `'ok'` | `ok` / `phrase_not_supported` / `no_time_phrase` / `ambiguous` |
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

### 兼容 API（Legacy）

`extract_date_range(msg, today=None)` 返回 `(start, end)`，失败为 `(None, None)`；
`parse_time_expression(text, today=None)` 返回 `(start, end)`，失败为 `None`。

这两个入口仅为向后兼容而继续导出。元组无法携带 `point`、`boundary`、`confidence`、
`recognition_status` 或新增时间语义；新代码应优先使用对应的结构化 API。它们不会在当前
主版本中删除，未来若移除将通过主版本升级处理。

## 支持的表达

| 类别 | 示例 |
| --- | --- |
| 单日 | 今天、今日、当天、本日、昨天、昨日、前天、前日、明天 |
| 精确日期 | `2026-04-15`、`2026/04/15`、`2026年4月15日` |
| 周 | 本周、上周、下周、上上周、周一到周三、本周一到周五、本周至今 |
| 月 | 本月、上个月、下个月、上上月、上上上个月、上个月的下个月、月初、月末、3月到5月、`1-3月` |
| 季度 | 本季度、上季度、下季度、Q1–Q4、`2026Q1`、2026年第一季度、Q1到Q2、上季度至今 |
| 年 | 今年、去年、前年、明年、2025年、25年、年初、年末、年初至今、YTD |
| 半年 | 上半年、下半年、全年至今、`H1`/`h1`/`H2`/`h2`、`2025H1`、`2025 H2`、`2025年H1`、`H1到H2` |
| 相对 | 最近N天/周/月/年、近N个月、近半年、近一年、过去N天 |
| 范围 | `2026-04-01 至 2026-04-30`、从X到Y、`X~Y` |
| 口语 | 5号到15号、3月1号到3月15号、上个月1号到今天、上月至今 |
| **同比** | 同比、去年同期、本月同比、上个月同比、今年同比去年、`Q2同比`、`2025Q1同比`、`H1同比`、`2025H2同比` |
| **环比** | 环比、本月环比、上个月环比、`Q2环比`、`Q1环比`、`H1环比`、`H2环比`、`2025Q1环比`、`2025H1环比` |
| **日期时刻** | 昨天中午、明天下午3点、今天晚上8点半、下周三上午10点、8月20日14:30、后天凌晨2点、昨晚、今晚、明早 |
| **相对时长** | 半小时后、10分钟后、3天后、两周前、一个月以后、过两小时、再过三天 |
| **时刻区间/边界** | 8月1日至昨天中午、今天上午10点到下午3点、直到昨天中午、截至明天下午3点 |
| **事件顺序选择** | 最近一次、上一次、最后一次、第一次、最早一次、最近3次、前3次、倒数第二次、去年最近一次 |
| **模糊时间** | 最近几天/几周/几个月/几年、最近一段时间、前段时间、过几天/几小时、过段时间、不久以后、很早以前、晚一点、月底左右、近期（只识别语义，不猜日期） |
| **截止/开始边界** | 周五之前、月底以前、三天以内、两小时内、从明天开始、下周以后、截至月底、最迟周三 |
| **评估时点锚点** | 在昨天的时候、到这个月底的时候、在昨天下午3点的时候（返回 as-of，不返回比较运算符） |

### 可组合的自然月位移

月份组合不是通过截取某一个局部词组实现，而是先计算相对月份偏移：

| 表达 | 以 `today=2026-08-11` 为例 |
| --- | --- |
| 上上月 | `2026-06-01 ~ 2026-06-30` |
| 上上上个月 | `2026-05-01 ~ 2026-05-31` |
| 上个月的下个月 | `2026-08-01 ~ 2026-08-11`（回到本月，沿用 MTD 口径） |
| 上上个月的下个月 | `2026-07-01 ~ 2026-07-31` |
| 一季度后的一个月 | `2026-04-01 ~ 2026-04-30` |
| 一季度后的下一个月 | `2026-04-01 ~ 2026-04-30` |
| `Q4` 后的一个月 | `2027-01-01 ~ 2027-01-31` |

连续“上/下”支持任意长度并自动跨年；显式季度年份（如“2025年第四季度后的一个月”）
不会依赖 `today`。普通“上个月”等既有表达保持原行为。

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
├── models.py              # 全部结构化时间结果模型
├── py.typed               # PEP 561 类型信息标记
├── normalization.py       # 格式化、校验、中文数字、月份日历工具
├── explicit_parser.py     # 显式/精确日期、中文日期段、号段
├── relative_parser.py     # 最近N天/周/月/年、单日同义词
├── week_parser.py         # 周相关
├── month_parser.py        # 月相关
├── quarter_parser.py      # 季度相关
├── year_parser.py         # 年/半年相关（含 H1/H2）
├── boundary_parser.py     # DateRange 的到X/截至X 截止点
├── datetime_parser.py     # DateTimePoint 日期时刻
├── datetime_range_parser.py # DateTimeRange 时刻区间
├── relative_time_parser.py  # RelativeTime 锚点 + duration
├── temporal_*_parser.py   # Selector / Boundary / Anchor / 模糊语义 / 月份链
└── comparison_parser.py   # 同比/环比，复用上述解析器 + 日历平移

tests/
├── conftest.py                # 跨模块共享时间锚点夹具
├── test_date_parse.py         # DateRange 完整规则契约（主矩阵）
├── test_date_parser.py        # 不同锚点下的端到端补充冒烟
├── test_half_year.py          # H1/H2 半年表达
├── test_comparison.py         # 同比/环比解析
├── test_comparison_fix.py      # 比较词误识别回归（环/默认周期/同环比并存/旧API保护）
├── test_comparison_boundary.py  # 比较词边界修复（同期生/同比例/环比例/白名单/旧API边界）
├── test_comparison_model.py   # ComparisonRange 契约
├── test_models.py             # DateRange 契约：to_dict / __bool__ / 字段默认值
├── test_properties.py         # Hypothesis 生成式输入与解析不变量
├── test_parser_stress.py      # 超长输入与正则回溯预算
├── test_packaging_contract.py # 版本与 py.typed 发布契约
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
python -m mypy src/zh_time_parser # 源码类型检查
python -m pytest tests -v         # 测试 + 分支覆盖率门禁
python -m build --no-isolation    # 构建 wheel 与 sdist
```

pytest 默认启用 `zh_time_parser` 分支覆盖率并要求至少 85%；生成式测试负责随机
中文输入不崩溃，压力测试限制病理输入的解析时间。CI 在 Python 3.8–3.12 上运行
Ruff 与完整测试，并在 Python 3.12 上额外执行 mypy 和发布构建。

欢迎提交 Issue 和 Pull Request。开发流程、兼容性要求和提交检查清单见
[CONTRIBUTING.md](CONTRIBUTING.md)；参与项目时请遵守
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 1.x 稳定语义

「本月」截断到今天而「本季度」返回完整季度、「最近N月」是滑动窗口而非自然月、
两位年份一律补 `20` 前缀（`99年 → 2099`）等既有行为已冻结为 1.x 兼容契约。
未来若调整这些口径，将通过新的 major 版本进行；完整决策见 [DESIGN.md](DESIGN.md)。

## License

MIT
