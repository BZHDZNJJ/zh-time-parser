"""
zh-time-parser —— 中文自然语言时间表达解析器。

把"昨天"、"上个月"、"最近7天"、"Q1"、"2026-04-01 至 2026-04-30"等中文时间表达
解析成具体的日期范围。纯 Python 标准库实现，无第三方依赖。

基本用法：

    >>> from zh_time_parser import extract_date_range_v2
    >>> r = extract_date_range_v2("最近7天")
    >>> r.start, r.end
    ('2026-08-03', '2026-08-09')

传入固定的 today 可获得可重复的结果：

    >>> from datetime import datetime
    >>> r = extract_date_range_v2("上个月", today=datetime(2026, 5, 24))
    >>> r.start, r.end
    ('2026-04-01', '2026-04-30')

解析同比/环比时使用 extract_comparison_range()，它返回**两个**区间：

    >>> from zh_time_parser import extract_comparison_range
    >>> c = extract_comparison_range("Q2同比", today=datetime(2026, 8, 9))
    >>> c.current.start, c.current.end
    ('2026-04-01', '2026-06-30')
    >>> c.comparison.start, c.comparison.end
    ('2025-04-01', '2025-06-30')
"""

from .comparison_parser import extract_comparison_range
from .date_parser import (
    DateRange,
    extract_date_range,
    extract_date_range_v2,
    parse_time_expression,
)
from .models import ComparisonRange

__version__ = "0.2.0"

__all__ = [
    "DateRange",
    "ComparisonRange",
    "extract_date_range_v2",
    "extract_date_range",
    "extract_comparison_range",
    "parse_time_expression",
    "__version__",
]
