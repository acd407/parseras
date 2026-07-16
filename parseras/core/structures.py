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

            if "=" not in line:
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
                # 未知键 — 保留为 LinesValue（含多行体块）
                body_lines = []
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if "=" in nxt or not nxt.strip():
                        break
                    body_lines.append(nxt.rstrip("\n"))
                    i += 1
                body = value_str + "\n" + "\n".join(body_lines) if body_lines else value_str
                self._key_value_pairs[key] = LinesValue(body)
                continue

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


class SingleBCLine(RASStructure):
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
                    self._value.append(SingleBCLine(current_bc_item))

                current_bc_item = [line]
            elif current_bc_item is not None:
                current_bc_item.append(line)

        if current_bc_item is not None:
            self._value.append(SingleBCLine(current_bc_item))

    def generate(self) -> List[str]:
        return [line for item in self._value for line in item.generate()]

    @property
    def value(self) -> List[SingleBCLine]:
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
            "#Sta/Elev": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
            "#Mann": (DataBlockValue, {"value_width": 8, "values_per_line": 9, "items_per_value": 3}),
            "Bank Sta": (CommaSeparatedValue, {"element_type": StringValue}),
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

class Head(RASStructure):
    order = 0.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Geom Title": StringValue,
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
            "Storage Area Mannings": FloatValue,
            "Storage Area Is2D": IntValue,
            # 2D Flow Area
            "Storage Area Point Generation Data": (CommaSeparatedValue, {"element_type": StringValue}),
            "Storage Area 2D Points": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            # StorageArea
            "Storage Area Vol Elev": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
        }
        super().__init__(lines)


class Connection(RASStructure):
    order = 110.0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Connection": (CommaSeparatedValue, {"element_type": StringValue}),
            "Connection Line": (
                DataBlockValue,
                {"value_width": 16, "values_per_line": 4, "items_per_value": 2},
            ),
            "Connection Up SA": StringValue,
            "Connection Dn SA": StringValue,
            "Conn Weir WD": IntValue,
            "Conn Weir SE": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
        }
        super().__init__(lines)


class Junction(RASStructure):
    """HEC-RAS Stream Junction block.

    Represents a confluence/diversion point connecting multiple upstream reaches
    to a single downstream reach. Example 10 (JUNCTION.g01) is the reference.

    Key structural differences from other RASStructure subclasses:
    - "Up River,Reach" can appear multiple times (one per upstream reach)
    - "Junc L&A" can appear multiple times (one per upstream reach)
    - "Dn River,Reach" appears exactly once (single downstream reach)
    """
    order = 8.0  # Before River(10.0), after Head(0.0)

    def __init__(self, lines: List[str]):
        # Keys that can appear multiple times → accumulate into lists
        self._multi_keys = {"Up River,Reach": [], "Junc L&A": []}

        self._key_value_types = {
            "Junct Name": StringValue,
            "Junct Desc": StringValue,
            "Junct X Y & Text X Y": (CommaSeparatedValue, {"element_type": StringValue}),
            "Up River,Reach": (CommaSeparatedValue, {"element_type": StringValue}),
            "Dn River,Reach": (CommaSeparatedValue, {"element_type": StringValue}),
            "Junc L&A": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)

    def _parse_lines(self, lines: List[str]):
        """Override to handle multi-occurrence keys (Up River,Reach; Junc L&A)."""
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            if "=" not in line:
                i += 1
                continue

            key, value_str = self._parse_key_value_line(line)

            # Fuzzy match
            matched_key = None
            for dict_key in self._key_value_types:
                if dict_key.rstrip() == key.rstrip():
                    matched_key = dict_key
                    break

            if matched_key is not None:
                value_type_info = self._key_value_types[matched_key]

                if isinstance(value_type_info, tuple) and len(value_type_info) == 2:
                    value_type, kwargs = value_type_info
                    value = value_type(value_str, **kwargs)
                elif isinstance(value_type_info, type) and issubclass(value_type_info, Value):
                    value = value_type_info(value_str)
                else:
                    value = value_str

                # Accumulate multi-occurrence keys into lists
                if matched_key in self._multi_keys:
                    self._multi_keys[matched_key].append(value)
                    self._key_value_pairs[matched_key] = value  # keep last one for generate()
                else:
                    self._key_value_pairs[matched_key] = value
                i += 1
            else:
                i += 1

        return self

    @property
    def up_reaches(self) -> List[Tuple[str, str]]:
        """Return list of (river, reach) tuples for upstream reaches."""
        result = []
        for val in self._multi_keys.get("Up River,Reach", []):
            parts = str(val).split(",")
            if len(parts) >= 2:
                result.append((parts[0].strip(), parts[1].strip()))
        return result

    @property
    def dn_reach(self) -> Tuple[str, str]:
        """Return (river, reach) tuple for the single downstream reach."""
        val = self._key_value_pairs.get("Dn River,Reach")
        if val is not None:
            parts = str(val).split(",")
            if len(parts) >= 2:
                return (parts[0].strip(), parts[1].strip())
        return ("", "")

    @property
    def junc_lengths_angles(self) -> List[Tuple[str, str]]:
        """Return list of (length, angle) tuples, one per upstream reach."""
        result = []
        for val in self._multi_keys.get("Junc L&A", []):
            parts = str(val).split(",")
            length = parts[0].strip() if len(parts) > 0 else ""
            angle = parts[1].strip() if len(parts) > 1 else ""
            result.append((length, angle))
        return result

    def generate(self) -> List[str]:
        result = []
        # Single-value keys
        for key in ["Junct Name", "Junct Desc", "Junct X Y & Text X Y"]:
            if key in self._key_value_pairs:
                result.append(self._format_key_value_line(key, self._key_value_pairs[key]))

        # Multiple "Up River,Reach=" lines
        for val in self._multi_keys.get("Up River,Reach", []):
            result.append(f"Up River,Reach={val}\n")

        # Single "Dn River,Reach=" line
        if "Dn River,Reach" in self._key_value_pairs:
            result.append(self._format_key_value_line("Dn River,Reach", self._key_value_pairs["Dn River,Reach"]))

        # Multiple "Junc L&A=" lines
        for val in self._multi_keys.get("Junc L&A", []):
            result.append(f"Junc L&A={val}\n")

        return result
