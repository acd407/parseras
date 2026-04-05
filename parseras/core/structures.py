import math
from abc import ABC
from typing import Any, Dict, List, Tuple

from parseras.core.values import (
    Value,
    StringValue,
    IntValue,
    FloatValue,
    CommaSeparatedValue,
    LinesValue,
    DataBlockValue,
)


class RASStructure(ABC):
    _key_value_pairs: Dict[str, Value]
    _key_value_types: Dict[str, Any]

    def __init__(self, lines: List[str]):
        self._key_value_pairs = {}
        self._parse_lines(lines)

    def __getitem__(self, key: str) -> Value:
        value = self._key_value_pairs.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found")
        return value

    def __setitem__(self, key: str, value: Value) -> None:
        # 如果传入的是原始 Python 值，自动包装成对应的 Value 类型
        if not isinstance(value, Value):
            value = self._wrap_value(value)
        self._key_value_pairs[key] = value

    def __delitem__(self, key: str) -> None:
        if key not in self._key_value_pairs:
            raise KeyError(f"Key '{key}' not found")
        del self._key_value_pairs[key]

    def __contains__(self, key: str) -> bool:
        return key in self._key_value_pairs

    def __len__(self) -> int:
        return len(self._key_value_pairs)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RASStructure):
            return False
        return self._key_value_pairs == other._key_value_pairs

    def _parse_key_value_line(self, line: str) -> Tuple[str, str]:
        if "=" not in line:
            raise ValueError(f"Invalid key-value line: {line}")
        key, value = line.split("=", 1)
        return key.strip(), value.strip()

    def _format_key_value_line(self, key: str, value: Value) -> str:
        return f"{key}={str(value)}\n"

    def _wrap_value(self, value) -> Value:
        """将原始 Python 值自动包装成 Value 类型"""
        if isinstance(value, bool):
            return IntValue(int(value))
        elif isinstance(value, int):
            return IntValue(value)
        elif isinstance(value, float):
            return FloatValue(value)
        elif isinstance(value, str):
            return StringValue(value)
        elif isinstance(value, (list, tuple)):
            # 尝试解析为逗号分隔值
            return CommaSeparatedValue(",".join(str(v) for v in value))
        else:
            return StringValue(str(value))

    def _parse_lines(self, lines: List[str]):
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            key, value_str = self._parse_key_value_line(line)

            if key in self._key_value_types:
                value_type_info = self._key_value_types[key]

                if isinstance(value_type_info, tuple) and len(value_type_info) == 2:
                    value_type, kwargs = value_type_info

                    if value_type == DataBlockValue:
                        header_parts = value_str.strip().split(",")
                        count = int(header_parts[0].strip())
                        num_items_per_line = kwargs["values_per_line"] / kwargs["items_per_value"]
                        num_lines = math.ceil(count / num_items_per_line)

                        block_content = "\n".join([value_str] + lines[i + 1 : i + 1 + num_lines])

                        self[key] = DataBlockValue(block_content, **kwargs)
                        i += 1 + num_lines
                    else:
                        value = value_type(value_str, **kwargs)
                        self[key] = value
                        i += 1
                elif value_type_info == LinesValue:
                    count = int(value_str.strip())
                    block_content = value_str
                    if count:
                        block_content += "\n" + "".join(lines[i + 1 : i + 1 + count])
                    self[key] = LinesValue(block_content)
                    i += 1 + count
                elif isinstance(value_type_info, type) and issubclass(value_type_info, Value):
                    value = value_type_info(value_str)
                    self[key] = value
                    i += 1
            else:
                if line.startswith("Permanent Ineff"):
                    i += 1
                i += 1

        return self

    def generate(self) -> List[str]:
        result = []
        for key, value in self._key_value_pairs.items():
            result.append(self._format_key_value_line(key, value))
        return result


class River(RASStructure):
    order = 10.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "River Reach": (CommaSeparatedValue, {"element_type": StringValue}),
            "Reach XY": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "Rch Text X Y": (CommaSeparatedValue, {"element_type": StringValue}),
            "Reverse River Text": IntValue,
        }
        super().__init__(lines)


class SingleBreakLine(RASStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "BreakLine Name": StringValue,
            "BreakLine CellSize Min": StringValue,
            "BreakLine CellSize Max": StringValue,
            "BreakLine Near Repeats": IntValue,
            "BreakLine Protection Radius": IntValue,
            "BreakLine Polyline": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
        }
        super().__init__(lines)


class BreakLineMeta(RASStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "LCMann Time": StringValue,
            "LCMann Region Time": StringValue,
            "Chan Stop Cuts": IntValue,
            "LCMann Table": LinesValue,
            "LCMann Region Name": StringValue,
            "LCMann Region Table": LinesValue,
            "LCMann Region Polygon": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
        }
        super().__init__(lines)


class BreakLine:
    order = 150.0

    def __init__(self, lines: List[str]):
        self._value = []
        iterator = iter(lines)
        current_block = []

        for line in iterator:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("BreakLine"):
                if current_block:
                    self._value.append(SingleBreakLine(current_block))
                current_block = [line]
            elif stripped.startswith("LCMann"):
                if current_block:
                    self._value.append(SingleBreakLine(current_block))
                self._value.append(BreakLineMeta([line] + list(iterator)))
                break
            else:
                current_block.append(line)

    def generate(self) -> List[str]:
        return [line for item in self._value for line in item.generate()]

    @property
    def value(self) -> List[SingleBreakLine | BreakLineMeta]:
        return self._value


class CrossSection(RASStructure):
    order = 30.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Type RM Length L Ch R": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS GIS Cut Line": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "Node Last Edited Time": StringValue,
            "#Sta/Elev": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
            "#Mann": (DataBlockValue, {"value_width": 8, "values_per_line": 9, "items_per_value": 3}),
            "#XS Ineff": (DataBlockValue, {"value_width": 8, "values_per_line": 9, "items_per_value": 3}),
            "Bank Sta": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS Rating Curve": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS HTab Starting El and Incr": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS HTab Horizontal Distribution": (CommaSeparatedValue, {"element_type": StringValue}),
            "Exp/Cntr(USF)": (CommaSeparatedValue, {"element_type": StringValue}),
            "Exp/Cntr": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class Foot(RASStructure):
    order = 200.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Use User Specified Reach Order": IntValue,
            "GIS Ratio Cuts To Invert": IntValue,
            "GIS Limit At Bridges": IntValue,
            "Composite Channel Slope": IntValue,
        }
        super().__init__(lines)


class Head(RASStructure):
    order = 0.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Geom Title": StringValue,
            "Program Version": StringValue,
            "Viewing Rectangle": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class LateralWeir(RASStructure):
    order = 30.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Type RM Length L Ch R": (CommaSeparatedValue, {"element_type": StringValue}),
            "Node Name": StringValue,
            "Node Last Edited Time": StringValue,
            "Lateral Weir Pos": IntValue,
            "Lateral Weir End": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir Distance": FloatValue,
            "Lateral Weir TW Multiple XS": IntValue,
            "Lateral Weir WD": FloatValue,
            "Lateral Weir Coef": FloatValue,
            "LW OverFlow Method 2D": IntValue,
            "LW OverFlow Use Velocity Into 2D": IntValue,
            "Lateral Weir WSCriteria": IntValue,
            "Lateral Weir Flap Gates": IntValue,
            "Lateral Weir Hagers EQN": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir SS": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir Type": IntValue,
            "Lateral Weir Connection Pos and Dist": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir SE": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
            "Lateral Weir Centerline": (
                DataBlockValue,
                {"value_width": 16, "values_per_line": 4, "items_per_value": 2},
            ),
            "LW Div RC": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class StorageArea(RASStructure):
    order = 50.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Storage Area": (CommaSeparatedValue, {"element_type": StringValue}),
            "Storage Area Surface Line": (
                DataBlockValue,
                {"value_width": 16, "values_per_line": 2, "items_per_value": 2},
            ),
            "Storage Area Type": IntValue,
            "Storage Area Area": StringValue,
            "Storage Area Min Elev": StringValue,
            "Storage Area Is2D": IntValue,
            "Storage Area Point Generation Data": (CommaSeparatedValue, {"element_type": StringValue}),
            "Storage Area 2D Points": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "Storage Area 2D PointsPerimeterTime": StringValue,
            "Storage Area Mannings": FloatValue,
            "2D Cell Volume Filter Tolerance": FloatValue,
            "2D Cell Minimum Area Fraction": FloatValue,
            "2D Face Profile Filter Tolerance": FloatValue,
            "2D Face Area Elevation Profile Filter Tolerance": FloatValue,
            "2D Face Area Elevation Conveyance Ratio": FloatValue,
            "2D Face Min Length Ratio": FloatValue,
            "2D Face Area Laminar Depth": FloatValue,
            "2D Multiple Face Mann n": IntValue,
            "2D Composite LC": FloatValue,
        }
        super().__init__(lines)
