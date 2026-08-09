"""DateRange / ComparisonRange 数据类与时间常量。"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

# ─────────────────────────────────────────────────────────
#  时间常量（统一口径，避免魔法数字）
# ─────────────────────────────────────────────────────────
YEAR_DAYS = 365
HALF_YEAR_DAYS = 183


# ═════════════════════════════════════════════════════════
#  DateRange 数据类（v2 专属）
# ═════════════════════════════════════════════════════════

@dataclass
class DateRange:
    """
    结构化日期范围。
    支持 tuple 解包（向后兼容旧 API）和属性访问（新 API）。
    """
    start: Optional[str] = None          # 'YYYY-MM-DD'
    end: Optional[str] = None            # 'YYYY-MM-DD'
    # range_type: 'range' / 'point' / 'quarter' / 'ytd' / 'unknown'
    #   另有历史取值 'yoy' / 'mom'：同比/环比现由 ComparisonRange 表达，
    #   这两个取值保留仅为向后兼容，不要在新代码中依赖（详见 DESIGN.md）。
    range_type: str = 'range'
    # granularity: 'day' / 'week' / 'month' / 'quarter' / 'half_year' / 'year'
    granularity: str = 'day'
    original_text: str = ''              # 原始匹配片段
    label: str = ''                      # 给人看的标签："最近7天" / "上个月" / "Q1 2026"
    is_relative: bool = False            # 是否相对今天（每次调用可能不同）
    includes_end: bool = True            # 端点是否包含（用于 SQL BETWEEN）
    week_start: str = 'monday'           # 'monday' / 'sunday'
    confidence: float = 1.0              # 解析置信度 0~1，调用方可用于降级
    recognition_status: str = 'ok'       # 'ok' / 'no_time_phrase' / 'phrase_not_supported'
    # ── 截止点语义（用于"到X/截至X"的确定截止边界，不影响原有 start/end/range_type）──
    # point: 单点日期（YYYY-MM-DD）。表达指向明确截止日（如"到月底""到8月31日""截至今天"）时填充。
    #        调用方可用它作为"截至某日"的时点基准，而 start/end 仍保留完整区间。
    point: Optional[str] = None
    # boundary: 被强调的边界方向。"end"=表达强调结束边界（到/截至/截止/月底/年末）；None=未强调。
    boundary: Optional[str] = None

    def __iter__(self):
        """支持 tuple 解包：start, end = extract_date_range_v2(msg)"""
        return iter((self.start, self.end))

    def __getitem__(self, i):
        return (self.start, self.end)[i]

    def __eq__(self, other):
        if isinstance(other, tuple):
            return (self.start, self.end) == other
        if isinstance(other, DateRange):
            return (self.start, self.end) == (other.start, other.end)
        return NotImplemented

    def __bool__(self):
        return self.start is not None and self.end is not None

    def __repr__(self):
        if not self:
            return "DateRange(empty)"
        if self.range_type == 'point':
            return f"DateRange(point={self.start} [{self.label}])"
        return f"DateRange({self.start} ~ {self.end} [{self.label}, type={self.range_type}])"

    def to_tuple(self) -> Tuple[Optional[str], Optional[str]]:
        return (self.start, self.end)

    def to_dict(self) -> Dict[str, Any]:
        """
        转成普通 dict（便于 JSON 序列化 / 日志输出）。

        返回全部字段，键名与属性名一致；使用 dataclasses.asdict，
        新增字段会自动出现在结果中，无需同步维护。
        """
        return asdict(self)


# ═════════════════════════════════════════════════════════
#  ComparisonRange 数据类（同比 / 环比）
# ═════════════════════════════════════════════════════════

# comparison_type 合法取值
COMPARISON_YOY = 'yoy'                          # 同比：与上一年度相同日历位置比较
COMPARISON_PREVIOUS_PERIOD = 'previous_period'  # 环比：与紧邻的同粒度前一周期比较
_VALID_COMPARISON_TYPES = (COMPARISON_YOY, COMPARISON_PREVIOUS_PERIOD)


@dataclass
class ComparisonRange:
    """
    比较区间：同时表达「本期」与「对比期」两个区间。

    刻意与 DateRange 分开，而不是把两个区间塞进一个 DateRange：
    - DateRange 只表达**一个**区间，其 point/boundary 字段有各自的语义，
      不能挪用来存放对比期；
    - extract_date_range_v2() 的返回类型因此保持恒定为 DateRange，
      调用方不需要做类型判断。

    字段：
        current         本期区间（必须是有效 DateRange）
        comparison      对比期区间（必须是有效 DateRange）
        comparison_type 'yoy'（同比）或 'previous_period'（环比）
        original_text   原始匹配片段
        label           给人看的标签，如 "2026Q2 同比 2025Q2"
        confidence      解析置信度 0~1
    """
    current: DateRange
    comparison: DateRange
    comparison_type: str
    original_text: str = ''
    label: str = ''
    confidence: float = 1.0

    def __post_init__(self):
        """构造即校验：两个区间必须有效，比较类型必须合法。"""
        if not isinstance(self.current, DateRange) or not self.current:
            raise ValueError(
                f'ComparisonRange.current 必须是有效 DateRange（start/end 均非 None），'
                f'实际得到：{self.current!r}'
            )
        if not isinstance(self.comparison, DateRange) or not self.comparison:
            raise ValueError(
                f'ComparisonRange.comparison 必须是有效 DateRange（start/end 均非 None），'
                f'实际得到：{self.comparison!r}'
            )
        if self.comparison_type not in _VALID_COMPARISON_TYPES:
            raise ValueError(
                f'comparison_type 必须是 {_VALID_COMPARISON_TYPES} 之一，'
                f'实际得到：{self.comparison_type!r}'
            )

    def __repr__(self):
        kind = '同比' if self.comparison_type == COMPARISON_YOY else '环比'
        return (f'ComparisonRange[{kind}]('
                f'current={self.current.start}~{self.current.end}, '
                f'comparison={self.comparison.start}~{self.comparison.end})')

    def to_dict(self) -> Dict[str, Any]:
        """
        转成可直接 JSON 序列化的 dict（嵌套的 DateRange 也会展开为 dict）。
        """
        return asdict(self)
