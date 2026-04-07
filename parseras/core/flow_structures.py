"""
Flow 文件 (f01/f02) 的 RASStructure 子类
用于解析 HEC-RAS 流量结果文件
"""

from typing import Any, Dict, List

from parseras.core.values import (
    Value,
    StringValue,
    IntValue,
    FloatValue,
    CommaSeparatedValue,
)
from parseras.core.structures import RASStructure


class FlowHead(RASStructure):
    """Flow 文件头部信息

    包含: Flow Title, Program Version, Number of Profiles, Profile Names
    可能包含内联数据行（如 River Rch & RM 后面的数值）
    """
    order = 0.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Flow Title": StringValue,
            "Program Version": StringValue,
            "Number of Profiles": IntValue,
            "Profile Names": StringValue,
            "River Rch & RM": StringValue,
        }
        super().__init__(lines)

    def _parse_lines(self, lines: List[str]):
        """重写解析逻辑以处理 FlowHead 中的非 key=value 数据行"""
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # 如果不包含 = 号，可能是内联数据，跳过
            if "=" not in line:
                i += 1
                continue

            key, value_str = self._parse_key_value_line(line)

            if key in self._key_value_types:
                value_type_info = self._key_value_types[key]

                if isinstance(value_type_info, tuple) and len(value_type_info) == 2:
                    value_type, kwargs = value_type_info
                    value = value_type(value_str, **kwargs)
                elif isinstance(value_type_info, type) and issubclass(value_type_info, Value):
                    value = value_type_info(value_str)
                else:
                    value = StringValue(value_str)

                self._key_value_pairs[key] = value
                i += 1
            else:
                i += 1

        return self


class FlowProfile(RASStructure):
    """单个 Profile 的边界条件

    包含: Boundary for River Rch & Prof#, Up Type, Dn Type, Dn Known WS
    """
    order = 10.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Boundary for River Rch & Prof#": StringValue,
            "Up Type": IntValue,
            "Dn Type": IntValue,
            "Dn Known WS": FloatValue,
        }
        super().__init__(lines)


class ObservedWS(RASStructure):
    """观测水位数据

    包含: Observed WS 数据行
    """
    order = 20.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Observed WS": StringValue,
        }
        super().__init__(lines)


class DSSImport(RASStructure):
    """DSS 导入参数

    包含: DSS Import StartDate, StartTime, EndDate, EndTime, GetInterval, Interval, GetPeak, FillOption
    """
    order = 30.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "DSS Import StartDate": StringValue,
            "DSS Import StartTime": StringValue,
            "DSS Import EndDate": StringValue,
            "DSS Import EndTime": StringValue,
            "DSS Import GetInterval": IntValue,
            "DSS Import Interval": StringValue,
            "DSS Import GetPeak": IntValue,
            "DSS Import FillOption": IntValue,
        }
        super().__init__(lines)
