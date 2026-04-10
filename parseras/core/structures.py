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
    order = 100

    def __init__(self, lines: List[str]):
        self._key_value_pairs = {}
        self._parse_lines(lines)

    def __getitem__(self, key: str) -> Value:
        value = self._key_value_pairs.get(key)
        if value is None:
            raise KeyError(f"Key '{key}' not found")
        return value

    def __setitem__(self, key: str, value: Value) -> None:
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
        return key.rstrip(), value.strip()

    def _format_key_value_line(self, key: str, value: Value) -> str:
        return f"{key}={str(value)}\n"

    def _parse_lines(self, lines: List[str]):
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            key, value_str = self._parse_key_value_line(line)

            # 查找匹配的键（比较去除尾随空格的版本）
            matched_key = None
            for dict_key in self._key_value_types:
                if dict_key.rstrip() == key.rstrip():
                    matched_key = dict_key
                    break

            if matched_key is not None:
                value_type_info = self._key_value_types[matched_key]

                if isinstance(value_type_info, tuple) and len(value_type_info) == 2:
                    value_type, kwargs = value_type_info

                    if value_type == DataBlockValue:
                        header_parts = value_str.strip().split(",")
                        count = int(header_parts[0].strip())
                        num_items_per_line = kwargs["values_per_line"] / kwargs["items_per_value"]
                        num_lines = math.ceil(count / num_items_per_line)

                        block_content = "\n".join([value_str] + lines[i + 1 : i + 1 + num_lines])

                        self[matched_key] = DataBlockValue(block_content, **kwargs)
                        i += 1 + num_lines
                    else:
                        value = value_type(value_str, **kwargs)
                        self[matched_key] = value
                        i += 1
                elif value_type_info == LinesValue:
                    count = int(value_str.strip())
                    block_content = value_str
                    if count:
                        block_content += "\n" + "".join(lines[i + 1 : i + 1 + count])
                    self[matched_key] = LinesValue(block_content)
                    i += 1 + count
                elif isinstance(value_type_info, type) and issubclass(value_type_info, Value):
                    value = value_type_info(value_str)
                    self[matched_key] = value
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


class BCLineItem(RASStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "BC Line Name": StringValue,
            "BC Line Storage Area": StringValue,
            "BC Line Arc": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
        }
        super().__init__(lines)


class BCLine:
    order = 160.0

    def __init__(self, lines: List[str]):
        self._value = []

        current_bc_item = None

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("BC Line Name="):
                if current_bc_item is not None:
                    self._value.append(BCLineItem(current_bc_item))

                current_bc_item = [line]
            elif current_bc_item is not None:
                current_bc_item.append(line)

        if current_bc_item is not None:
            self._value.append(BCLineItem(current_bc_item))

    def generate(self) -> List[str]:
        return [line for item in self._value for line in item.generate()]

    @property
    def value(self) -> List[BCLineItem]:
        return self._value


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

        current_single_breakline = None
        meta_lines = []
        in_meta = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("BreakLine Name="):
                # 新的SingleBreakLine开始
                if current_single_breakline is not None:
                    # 保存当前的SingleBreakLine
                    self._value.append(SingleBreakLine(current_single_breakline))

                # 开始新的SingleBreakLine
                current_single_breakline = [line]
                in_meta = False

            elif stripped.startswith("LCMann"):
                # 遇到LCMann，开始BreakLineMeta部分
                if current_single_breakline is not None:
                    # 保存当前的SingleBreakLine
                    self._value.append(SingleBreakLine(current_single_breakline))
                    current_single_breakline = None

                # 收集所有剩余行作为BreakLineMeta
                meta_lines.append(line)
                in_meta = True

            else:
                # 普通行
                if in_meta:
                    # 在BreakLineMeta部分
                    meta_lines.append(line)
                elif current_single_breakline is not None:
                    # 在SingleBreakLine部分
                    current_single_breakline.append(line)
                else:
                    # 文件不以BreakLine Name开头，可能是格式错误
                    # 暂时忽略或作为BreakLineMeta处理
                    pass

        # 处理最后一个SingleBreakLine（如果没有遇到LCMann）
        if current_single_breakline is not None:
            self._value.append(SingleBreakLine(current_single_breakline))

        # 如果有BreakLineMeta行
        if meta_lines:
            self._value.append(BreakLineMeta(meta_lines))

    def generate(self) -> List[str]:
        return [line for item in self._value for line in item.generate()]

    @property
    def value(self) -> List[SingleBreakLine | BreakLineMeta]:
        return self._value


class CrossSection(RASStructure):
    order = 30.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Type RM Length L Ch R ": (CommaSeparatedValue, {"element_type": StringValue}),
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

        # 根据station更新order
        if "Type RM Length L Ch R " in self:
            type_rm = self["Type RM Length L Ch R "].value
            if len(type_rm) >= 2:
                try:
                    station = float(type_rm[1].value)
                    if station > 0:
                        self.order = 30 + 1 / station
                except (ValueError, AttributeError):
                    pass


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
            "Type RM Length L Ch R ": (CommaSeparatedValue, {"element_type": StringValue}),
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

        # 根据station更新order
        if "Type RM Length L Ch R " in self:
            type_rm = self["Type RM Length L Ch R "].value
            if len(type_rm) >= 2:
                try:
                    station = float(type_rm[1].value)
                    if station > 0:
                        self.order = 30 + 1 / station
                except (ValueError, AttributeError):
                    pass


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
            "Storage Area Vol Elev": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
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
