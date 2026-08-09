"""周相关表达：本周/上周/下周、周一到周三、本周至今。"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .models import DateRange
from .normalization import (
    _fmt,
)


def _week_range(ref_date: datetime, offset_weeks: int = 0,
                week_start: str = 'monday') -> Tuple[datetime, datetime]:
    """计算某周范围（周一/周日起）"""
    if week_start == 'sunday':
        days_since_start = (ref_date.weekday() + 1) % 7
        start = ref_date - timedelta(days=days_since_start) + timedelta(weeks=offset_weeks)
    else:
        start = ref_date - timedelta(days=ref_date.weekday()) + timedelta(weeks=offset_weeks)
    end = start + timedelta(days=6)
    return start, end


# 中文/数字 → 周几索引（周一=0 ... 周日=6）
_WEEKDAY_MAP = {
    '一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6,
    '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6,
}


def _resolve_week_offset(token: str) -> int:
    """把'本周/上周/下周/上上周'解析为 offset 周数；不匹配返回 None"""
    t = token.strip()
    if not t or re.fullmatch(r'(本|这|当前)?(周|星期|礼拜)', t) or t == '':
        return 0
    if re.fullmatch(r'(本|这|当前)(周|星期|礼拜)', t):
        return 0
    if re.fullmatch(r'上上(周|星期|礼拜)', t):
        return -2
    if re.fullmatch(r'上(个?周|星期|礼拜)', t):
        return -1
    if re.fullmatch(r'下下(周|星期|礼拜)', t):
        return 2
    if re.fullmatch(r'下(个?周|星期|礼拜)', t):
        return 1
    return None


def _parse_week_day_range(msg: str, today: datetime,
                          week_start: str = 'monday') -> Optional[DateRange]:
    """
    周内号段：
    - 周一到周三 / 周一至周五 / 周1到周3
    - 本周一到周五 / 本周一到本周五 / 上周一到周五
    - 星期一到星期三 / 礼拜一到礼拜三
    """
    # 同一周内：[本周/上周/下周]?周X 到 [本周/上周/下周]?周Y
    # 注意："上周一" 中"上周"已是 token 的一部分，"周"分隔符可选
    pat = (
        r'(?<![上下])((?:本周|上周|下周|上上周|下下周|这周|当前周))\s*(?:周|星期|礼拜)?\s*([一二三四五六日天1-7])'
        r'\s*(?:到|至|~|-)\s*'
        r'(?:(?<![上下])((?:本周|上周|下周|上上周|下下周|这周|当前周))\s*(?:周|星期|礼拜)?|(?:周|星期|礼拜))\s*([一二三四五六日天1-7])'
    )
    m = re.search(pat, msg)
    if m:
        wleft = m.group(1)
        d1_raw, d2_raw = m.group(2), m.group(4)
        wright = m.group(3) or wleft
        off_l = _resolve_week_offset(wleft)
        off_r = _resolve_week_offset(wright)
        if off_l is None or off_r is None:
            return None
        i1 = _WEEKDAY_MAP.get(d1_raw)
        i2 = _WEEKDAY_MAP.get(d2_raw)
        if i1 is None or i2 is None:
            return None
        s_week_l, _ = _week_range(today, off_l, week_start)
        s_week_r, _ = _week_range(today, off_r, week_start)
        s = s_week_l + timedelta(days=i1)
        e = s_week_r + timedelta(days=i2)
        if s > e:
            return None
        return DateRange(_fmt(s), _fmt(e), range_type='range', granularity='day',
                         original_text=m.group(0),
                         label=f'{wleft}{d1_raw}到{wright}{d2_raw}',
                         is_relative=True, week_start=week_start)

    # 无前缀的纯"周X到周Y"（默认本周）
    pat2 = (
        r'(?<![本上下这])(?:周|星期|礼拜)\s*([一二三四五六日天1-7])'
        r'\s*(?:到|至|~|-)\s*'
        r'(?:周|星期|礼拜)?\s*([一二三四五六日天1-7])'
    )
    m = re.search(pat2, msg)
    if m:
        d1_raw, d2_raw = m.group(1), m.group(2)
        i1 = _WEEKDAY_MAP.get(d1_raw)
        i2 = _WEEKDAY_MAP.get(d2_raw)
        if i1 is None or i2 is None or i1 > i2:
            return None
        s_week, _ = _week_range(today, 0, week_start)
        s = s_week + timedelta(days=i1)
        e = s_week + timedelta(days=i2)
        return DateRange(_fmt(s), _fmt(e), range_type='range', granularity='day',
                         original_text=m.group(0),
                         label=f'本周周{d1_raw}到周{d2_raw}',
                         is_relative=True, week_start=week_start)
    return None


def _parse_week_to_today(msg: str, today: datetime,
                        week_start: str = 'monday') -> Optional[DateRange]:
    """
    周 + 至今：
    - 本周到今天 / 本周至今 / 这周到今天
    - 上周到今天 / 上周至今
    - 上上周到今天
    - 下周到今天（少见，但支持）
    """
    patterns = [
        (r'上上(周|星期|礼拜)\s*(?:到|至|~|-)?\s*(?:今天|今儿|今日|当天|至今)', -2, '上上周'),
        (r'上(个?周|星期|礼拜)\s*(?:到|至|~|-)?\s*(?:今天|今儿|今日|当天|至今)', -1, '上周'),
        (r'下(个?周|星期|礼拜)\s*(?:到|至|~|-)?\s*(?:今天|今儿|今日|当天|至今)', 1, '下周'),
        (r'(本|这|当前)(周|星期|礼拜)\s*(?:到|至|~|-)?\s*(?:今天|今儿|今日|当天|至今)', 0, '本周'),
    ]
    for pat, offset, label in patterns:
        m = re.search(pat, msg)
        if m:
            s_week, _ = _week_range(today, offset, week_start)
            return DateRange(_fmt(s_week), _fmt(today), range_type='range', granularity='day',
                             original_text=m.group(0), label=f'{label}至今',
                             is_relative=True, week_start=week_start)
    return None


def _parse_week(msg: str, today: datetime, week_start: str = 'monday') -> Optional[DateRange]:
    """
    本周/上周/下周/上上周/本星期/这周/这星期
    """
    # 计算当前周（周一起 or 周日起）
    def week_range(ref_date: datetime, offset_weeks: int = 0) -> Tuple[str, str]:
        if week_start == 'sunday':
            # 周日 = 0
            days_since_start = (ref_date.weekday() + 1) % 7
            start = ref_date - timedelta(days=days_since_start) + timedelta(weeks=offset_weeks)
        else:  # monday
            start = ref_date - timedelta(days=ref_date.weekday()) + timedelta(weeks=offset_weeks)
        end = start + timedelta(days=6)
        return _fmt(start), _fmt(end)

    # 本周/这周/这星期/本星期
    if re.search(r'(本|这|当前)(周|星期)', msg):
        s, e = week_range(today, 0)
        return DateRange(s, e, range_type='range', granularity='week',
                         original_text='本周', label='本周', is_relative=True, week_start=week_start)

    # 上周/上个周/上星期
    if re.search(r'上(周|个?周|星期)', msg) and not re.search(r'上上(周|星期)', msg):
        s, e = week_range(today, -1)
        return DateRange(s, e, range_type='range', granularity='week',
                         original_text='上周', label='上周', is_relative=True, week_start=week_start)

    # 下周/下个周
    if re.search(r'下(周|个?周|星期)', msg) and not re.search(r'下下(周|星期)', msg):
        s, e = week_range(today, 1)
        return DateRange(s, e, range_type='range', granularity='week',
                         original_text='下周', label='下周', is_relative=True, week_start=week_start)

    # 上上周/上上星期
    if re.search(r'上上(周|星期)', msg):
        s, e = week_range(today, -2)
        return DateRange(s, e, range_type='range', granularity='week',
                         original_text='上上周', label='上上周', is_relative=True, week_start=week_start)

    return None
