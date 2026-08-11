# Changelog

本文件记录本项目的所有重要变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-08-11

### Added

- **1.0 工程质量门禁**：统一包元数据与运行时版本来源为 `1.0.0`，发布包加入
  `py.typed`；新增 mypy 源码类型检查、85% 分支覆盖率门禁、Hypothesis 生成式测试、
  超长输入压力测试、共享时间锚点夹具、打包契约测试及 CI 发布构建验证。
- 新增 `CONTRIBUTING.md` 与 `CODE_OF_CONDUCT.md`，明确本地开发、DateRange
  兼容性、测试门禁、PR 检查清单、社区行为和事件处理规则。

- **可组合自然月位移解析**：
  - 连续「上/下」按出现次数计算月份偏移，支持「上上上个月」「下下下个月」并自动跨年
  - 月份链逐项求值：「上个月的下个月」回到本月，
    「上上个月的下个月」得到上个月，不再只截取第一个局部词组
  - 支持「一季度后的一个月」「一季度后的下一个月」「Q4后的一个月」及
    「2025年第四季度后的一个月」等季度结束后首个自然月
  - 组合结果回到当前月时沿用既有本月 MTD 口径；其他目标月返回完整自然月
- **TemporalAnchor as-of 评估时钟锚点**：
  - 新增独立数据类 `TemporalAnchor` 和公开 API `extract_temporal_anchor()`
  - 区分「截至昨天」的 `TemporalBoundary <=` 与「在昨天的时候」的
    `TemporalAnchor as_of`，避免把状态评估时点误当成记录筛选条件
  - 支持从完整业务句「到这个月底的时候客户欠款超期金额是多少」中提取
    `as_of=2026-08-31`，并通过 `is_future` 标记未来评估时点
  - 支持日期和具体时刻锚点；对「在下个月的时候」这类仍缺具体日期的表达不猜月初/月末
  - 新入口不修改 `DateRange` / `TemporalBoundary` 的既有行为和返回契约
- **TemporalBoundary Deadline / Boundary 解析**：
  - 新增独立数据类 `TemporalBoundary` 和公开 API `extract_temporal_boundary()`
  - 支持「周五之前」「月底以前」「三天以内」「两小时内」「从明天开始」
    「下周以后」「截至月底」「最迟周三」等单侧边界
  - 明确保留 `<` / `<=` / `>` / `>=` 运算符以及 `date` / `datetime` 值类型，
    不把截止或开始语义降级为普通闭区间
  - 相对时长边界嵌套保留 `RelativeTime`，便于 SLA/任务系统审计原始 duration
  - 新入口与原有 `DateRange` 调度链隔离
- **AmbiguousTemporal 模糊时间识别与防猜保护**：
  - 新增独立数据类 `AmbiguousTemporal` 和 `extract_ambiguous_temporal()`，支持
    「最近几天」「最近一段时间」「前段时间」「过几天」「晚一点」「月底左右」「近期」
  - 输出 `type/status/direction/unit/value`，其中模糊数值 `value` 始终为 `None`
  - `extract_date_range_v2()` 遇到明确模糊表达时返回空区间和
    `recognition_status='ambiguous'`，不再把“几天”替换成任意默认数字
  - 明确数值表达（如「最近7天」）及其他 DateRange 核心规则保持不变
- **TemporalSelector 事件顺序选择器**：
  - 新增独立数据类 `TemporalSelector` 和公开 API `extract_temporal_selector()`
  - 支持「最近一次」「上一次」「最后一次」「第一次」「最早一次」「最近3次」
    「前3次」「倒数第二次」，输出 `order`、`limit` 和 `offset`
  - 支持与日期范围组合：「去年最近一次」返回去年 `DateRange + latest/1`，
    「上个月最近3次」返回上个月 `DateRange + latest/3`
  - 不猜测事件发生日期，不进入原有日期解析调度链；调用方可选地映射到
    SQL `ORDER BY / LIMIT / OFFSET`、CRM 或搜索系统
- **DateTimeRange 时刻区间与旧系统日期投影**：
  - 新增独立数据类 `DateTimeRange` 和 `extract_datetime_range()`，支持
    「8月1日至昨天中午」以及「直到昨天中午」这类单侧结束边界
  - 精确 `start/end` 与兼容旧系统的 `date_start/date_end` 同时保留；
    有损日期投影通过 `precision_lost=True` 明确标记
  - `to_date_tuple()` 支持 `calendar_date`、`completed_days`、`reject_lossy` 三种策略，
    由调用方明确决定多查、少查或拒绝有损执行
  - 新解析器不进入 `DateRange` 调度链，原有日期范围返回契约保持不变
- **RelativeTime 相对时长解析**：
  - 新增独立数据类 `RelativeTime` 和公开 API `extract_relative_time(user_message, anchor=None)`；
    不接入原有日期范围或日期时刻调度链
  - 支持「半小时后」「10分钟后」「3天后」「两周前」「一个月以后」
    「过两小时」「再过三天」等锚点偏移表达
  - 结果同时保留标准化的 `value`、`unit`、`direction` 和精确到分钟的 `resolved_at`
  - 月份使用真实日历平移并安全处理月末，不使用固定 30 天近似
  - 新增 RelativeTime 模型、解析规则、月末和 DateRange 隔离回归测试
- **DateTimePoint 日期时刻解析**：
  - 新增独立数据类 `DateTimePoint` 和公开 API `extract_datetime_point()`；不接入
    `extract_date_range_v2()` 调度链，保持 `DateRange` 返回契约和核心日期范围行为不变
  - 支持相对日、周几、显式年月日与中文时段/钟点组合，包括「明天下午3点」
    「今天晚上8点半」「下周三上午10点」「8月20日14:30」「后天凌晨2点」
  - 「今晚」「明早」分别使用 20:00、08:00 的约定值，并以较低置信度和
    `precision='period'` 明确标记
  - 支持「昨天中午」「前天晚上8点」「昨晚」「今早」等过去日期 + 时段组合，
    避免过去日期被错误回落到今天
  - 新增日期时刻与 DateRange 隔离回归测试
- **H1/H2 半年表达**（大小写均支持）：
  - 无年份 `H1` / `h1` / `H2` / `h2` → 当年上/下半年，`is_relative=True`
  - 指定年份 `2025H1` / `2025 H1` / `2025年H1` → `is_relative=False`
  - 半年范围 `H1到H2` / `H1至H2` / `H1~H2` / `2025H1到2025H2` → 覆盖全年
  - 统一 `range_type='range'`、`granularity='half_year'`、`label='2026H1'` 形式
  - 解析顺序置于年份解析器之前，确保 `2025H1` 不被 `2025年` 截获；
    范围形式先于单个形式匹配，确保 `H1到H2` 不被单个 `H1` 截获
  - **跨年份范围（`2025H2到2026H1`）刻意不支持**，避免在未校验起止顺序时产出错误区间
- **同比 / 环比解析**：
  - 新增数据类 `ComparisonRange`（`current` + `comparison` + `comparison_type`），
    构造时校验两个区间有效性与 `comparison_type` 合法性，含 `to_dict()` / `__repr__`
  - 新增公开 API `extract_comparison_range(user_message, today=None, week_start='monday')`，
    无法确定比较语义时返回 `None`，不抛异常、不编造区间
  - 新增模块 `comparison_parser.py`：先剥离比较词、复用既有解析器确定本期区间，
    再按粒度做**日历平移**得出对比期。不复制季度/半年/月份计算逻辑
  - 同比按日历平移一年（**非固定 365 天**），闰年 2月29日回退到 2月28日
  - 环比统一建模为 `previous_period`（**非固定 30 天**）：完整周期比完整前周期
    并使用各自真实月末；进行中的周期使用相同已过天数
  - 从包顶层导出 `ComparisonRange` 与 `extract_comparison_range`
- `tests/test_half_year.py`（48 项）、`tests/test_comparison.py`（52 项）、
  `tests/test_comparison_model.py`（17 项），共新增 117 项测试。
- `DateRange.to_dict()`：返回含全部字段的 dict（基于 `dataclasses.asdict`），
  可直接 JSON 序列化。此前 README 已写明该方法，但实现中并不存在。
- `tests/test_models.py`（23 项）：锁定 `to_dict()`、`__bool__`、tuple 兼容、
  字段默认值，以及 README 示例输出。
- `tests/test_error_propagation.py`（23 项）：锁定异常处理契约 —— 编程错误必须冒泡。
- dev 依赖加入 `ruff`；CI 在 pytest 之前运行 `ruff check src tests`。
- `[project.urls]`（Homepage / Repository / Issues / Changelog）与
  `authors` / `maintainers` 元数据占位（值为 `TODO`，发布前替换）。

### Fixed

- **DateRange 截止点优先级与非法降级修复**：句首「到/截至/截止 + 结构化日期」
  现在优先保留 `point` / `boundary='end'`，不再被普通月份规则提前截走；
  「截至上个月底」正确处理可选「个」及跨年；「截至13月底」「截至本月32号」
  不再悄悄退化为当前月底或本月范围。

- **模糊数量不再默认等于 2**：`_parse_cn_number('几')` 现返回 `None`；
  「近几年」「前几年」「最近几周/几个月」「过几小时/分钟」统一交给
  `AmbiguousTemporal` 并保持 `value=None`。明确数字表达不受影响。
- **多范围连接符不再静默返回部分结果**：「从3月到5月到昨天」此前可能只返回
  「昨天」或单侧结束边界，现由 `DateRange` / `DateTimeRange` 明确返回不支持。
  「到期」等普通业务词中的“到”不会被计作范围连接符。
- **Sunday 周内日期偏移修复**：`week_start='sunday'` 时，「本周一到周五」此前
  错算为周日到周四，现正确按周日起始口径转换周几偏移。
- `TemporalSelector` 在复用 `DateRange` 前会清理「在/于」「范围内/里/期间」等
  日期上下文连接词。
- 所有公开解析入口补充非字符串输入契约测试；支持 `week_start` 的入口统一拒绝非法值。
- 新增 Sunday 起始周测试矩阵，覆盖周范围、周内日期段、周至今、日期时刻、
  带时刻区间和边界解析。
- **同比/环比此前完全无法识别**，且会给出误导性结果：
  - 「去年同期」错误退化为**去年全年**，现返回今年至今 vs 去年同期两个区间
  - 「今年同比去年」只解析出今年，现返回两个区间
  - 「上月环比」只解析出上个月，现返回上月 vs 上上月两个区间
  - 比较词残留会干扰基础日期解析（如「今年同比去年」被当作年份范围），
    现已在解析前剥离
- **主入口不再吞掉编程错误**：`extract_date_range_v2` 的解析链原本用
  `except Exception` 兜底，会把 `NameError` / `AttributeError` / `TypeError`
  静默转成 `recognition_status='phrase_not_supported'`，让真实 bug
  伪装成「解析不了」。现在只捕获
  `ValueError` / `OverflowError` / `KeyError` / `IndexError`
  这类由输入导致的可预期异常。
- 修正 README 与实现不符之处：
  - `bool(DateRange)` 要求 `start` 和 `end` **同时**存在，此前误写为「有 start 即为真」；
  - 快速上手示例中「上个月」的 `range_type` 误写为 `month`，实际为 `range`，
    `month` 是 `granularity`；
  - 补全 `granularity` / `is_relative` / `week_start` / `point` / `boundary`
    字段说明，并明确 `range_type`（区间形态）与 `granularity`（时间粒度）是两个维度。
- **比较词误识别修复（2026-08）**：
  - 收紧环比触发器：移除单独的「环」，仅「环比 / 较上期 / 比上期」触发。
    修复「环境数据 / 环节分析 / 循环统计 / 环岛记录」被误判为环比的问题。
  - 限制默认比较周期的使用条件：仅当比较词**独立出现**
    （剥离后剩余为空或仅含无语义标点/询问后缀，如「同比」「去年同期」
    「同比是多少」「去年同期怎么样」）才回退默认周期；
    若剥离后仍含实质性时间表达但无法解析（如「前阵子同比」「第五季度同比」
    「H3环比」「不支持的时间环比」），一律返回 `None`，不再编造默认周期。
  - 同时含「同比」与「环比」时返回 `None`（如「同比环比都要」「本月同比和环比」
    「Q2同比、环比」「同比及环比」），不再静默只取同比，以免丢失用户意图。
    `extract_comparison_range` 本次仍只支持单次一种比较类型；
    同/环比并存的多组比较需另行设计列表型 API，本次**不扩展返回类型**（见 DESIGN.md §8）。
  - `extract_date_range_v2` 新增明确比较表达保护：输入含「同比 / 环比 / 去年同期 /
    上年同期 / 较上期 / 比上期」时，不再按普通 DateRange 解析，返回空区间
    （`recognition_status='phrase_not_supported'`、`range_type='unknown'`、
    `label='比较表达请使用 extract_comparison_range'`）。保护名单刻意不含单独「同」「环」，
    故「同期生」「环境数据」不受影响；comparison_parser 先剥离比较词再调用，
    「本月同比」等正常功能不受影响。
  - 新增回归测试 `tests/test_comparison_fix.py`（34 项），覆盖上述全部反例与保留用例；
    总测试数 339 → 373。对原有非比较语料做行为基线比对，差异为 0。
- **比较词边界二次修复（2026-08 第二轮）**：
  - 同比检测用负向前瞻排除「同比例」（`同比(?!例)`）与「同期生/同期刊/同期声」
    （`同期(?!生|刊|声)`）；环比排除「环比例」（`环比(?!例)`，而「环比较」因不含连续
    「环比」子串天然不命中）；单独出现的「环比率」仍按环比识别。
  - 重写独立默认周期判定：删除「剩余文本是否含时间词」的过宽推断，改为对原始输入
    使用**首尾锚定的严格白名单** `_STANDALONE_DEFAULT_PAT`（核心表达 + 有限前缀/后缀 +
    标点）。「同期生/同期刊/同期声/同比例/环比例/环比较/前阵子同比/第五季度同比/H3环比」
    等均因无法首尾精确匹配而被拒绝，回退 `None`，不再编造默认周期。
  - `date_parser._COMPARISON_PHRASE_PAT` 同步收紧（同负向前瞻），使 `extract_date_range_v2`
    对「同比例/同期生/同期刊/同期声」维持普通 `no_time_phrase` 行为，而非误报
    `phrase_not_supported`；明确比较表达（同比/环比/去年同期/上月环比/Q2同比）仍返回
    `phrase_not_supported`。
  - 新增回归测试 `tests/test_comparison_boundary.py`（约 30 项）；总测试数 373 → 403
    （实际以 pytest 运行结果为准）。非比较语料行为基线比对差异仍为 0。

### Changed

- 清理 ruff 报出的 90 项问题（78 处未使用导入 —— 模块拆分时机械复制导入块的遗留、
  12 处导入排序）。仅涉及导入与换行，不改动任何解析逻辑。
- 测试与源码注释中的业务痕迹中性化（详见 Removed），仅改文本，
  测试意图与期望值不变。
- 与抽离前基线比对 470 组解析结果，差异 0 组，行为未改变。
- `extract_date_range_v2()` 的**返回类型保持恒定为 `DateRange`**，
  不会因为输入含「同比/环比」而改为返回 `ComparisonRange`；
  对比期也不会被塞进 `DateRange.point` / `boundary`。
- `近半年` 保持原有的滑动 183 天语义，未因新增 H1/H2 而改变。
- 本次改动与改动前基线比对 676 组解析结果，
  除新支持的 H1/H2 表达外，原有解析结果**零差异**。

### Removed

- 删除一次性脚本 `_split.py`，清理 `__pycache__` / `.pytest_cache` / `.ruff_cache`。
- 测试与注释中的业务痕迹：真实客户名统一替换为虚构名称「张三」，
  「销售额→数据量」「销售→数据」「回款→记录」「开单→登记」（共 22 处），
  测试用例中的具体药品名 →「记录」，
  `models.py` / `boundary_parser.py` 注释中的 `debt`、「欠款」「超期」等下游业务描述
  改为中性表述。

### 1.x 稳定语义

- 「本月/今年」保持 MTD/YTD；「本周/本季度」保持完整自然周期
- 「最近 N 月」保持滑动窗口；日期端点保持闭区间（`includes_end=True`）
- 两位年份保持补 `20`（`99年 → 2099`）
- `DateRange.range_type` 的 `'yoy'` / `'mom'` 取值已不可达，
  1.x 保留以避免破坏兼容性；下个 major 版本再评估清理
- 跨年份半年范围（`2025H2到2026H1`）在 1.x 保持不支持
- 单独「同比」「环比」保持默认周期（YTD / 本月至今）

详见 [DESIGN.md](DESIGN.md)。

## [0.1.0] - 2026-08-09

首个版本。从业务项目中抽离为独立、零依赖的中文时间解析库。

### Added

- 公开 API：`extract_date_range_v2`、`extract_date_range`、
  `parse_time_expression`、`DateRange`
- `pyproject.toml`（src layout，零运行时依赖，Python 3.8+）
- MIT LICENSE、README.md、DESIGN.md
- GitHub Actions pytest 工作流（Python 3.8–3.12 矩阵）
- 176 项日期解析测试

### Changed

- 按维度把单文件（1697 行）拆分为 `models`、`normalization` 与
  `explicit` / `relative` / `week` / `month` / `quarter` / `year` / `boundary`
  七个解析模块；`date_parser.py` 仅保留调度逻辑。
  拆分前后对 77 个表达做输出比对，结果完全一致，解析行为未改变。

### Removed

清除业务耦合（详见 README 与迁移说明）：

- 删除记录日期字段排序功能 `_get_date_value()` 及其常量
  `_DATE_FIELDS`、`_DATE_FORMATS`（该函数仅供原业务项目的结算模块使用，
  与时间表达解析无关，仍保留在原项目中）
- 删除未完整接入的 `dateparser` 兜底逻辑 `_safe_dateparser_parse()`：
  该函数引用了文件中从未定义的 `_HAS_DATEPARSER` / `_dateparser`，
  一旦被调用必然抛 `NameError`，且全项目无任何调用点，属死代码。
  同时移除主入口 docstring 中与之对应的「16. dateparser 兜底」条目。
  本项目由此实现零第三方依赖。
- 未复制任何业务数据、环境变量、Prompt 或客户名称；
  一处使用真实客户名的测试用例已改写为中性数据。
