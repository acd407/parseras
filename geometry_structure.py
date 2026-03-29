from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Type, TypeVar, Union
import math


class Value(ABC):
    @classmethod
    @abstractmethod
    def __init__(cls, value_str: str):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass


class StringValue(Value):
    def __init__(self, value_str: str):
        self._value = value_str.strip()

    def __str__(self) -> str:
        return self._value

    @property
    def value(self) -> str:
        return self._value


class IntValue(Value):
    def __init__(self, value_str: str):
        self._value = int(value_str.strip())

    def __str__(self) -> str:
        return str(self._value)

    @property
    def value(self) -> int:
        return self._value


class FloatValue(Value):
    def __init__(self, value_str: str):
        self._value = float(value_str.strip())

    def __str__(self) -> str:
        v = self._value
        return str(int(v) if v.is_integer() else v)

    @property
    def value(self) -> float:
        return self._value


class CommaSeparatedValue(Value):
    def __init__(self, value_str: str, element_type: Type[Value] = StringValue):
        parts = value_str.split(",")
        result = []
        for part in parts:
            part = part.strip()
            if part:
                result.append(element_type(part))
            else:
                result.append(None)
        self._value = tuple(result)
        self._element_type = element_type

    def __str__(self) -> str:
        return ",".join(str(v) if v is not None else "" for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value


class SpaceSeparatedValue(Value):
    def __init__(self, value_str: str, element_type: Type[Value] = StringValue):
        parts = value_str.split()
        self._value = tuple(element_type(part) for part in parts)
        self._element_type = element_type

    def __str__(self) -> str:
        return " ".join(str(v) for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value


class NumericTupleValue(Value):
    def __init__(self, value_str: str):
        parts = value_str.split()
        result = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                result.append(int(part))
            except ValueError:
                result.append(float(part))
        self._value = tuple(result)

    def __str__(self) -> str:
        return " ".join(str(v) for v in self._value)

    @property
    def value(self) -> Tuple[Union[int, float], ...]:
        return self._value


class DataBlockValue(Value):
    def __init__(self, value_str: str, value_width: int, values_per_line: int, items_per_value: int):
        """
        value_str: 包含header和多行数据的完整字符串
        """
        lines = value_str.split("\n")
        data_lines = lines[1:]

        self._value_width = value_width
        self._values_per_line = values_per_line
        self._items_per_value = items_per_value

        self._count = int(lines[0].strip())

        result = []
        for line in data_lines:
            pos = 0
            while pos < len(line):
                chunk = line[pos : pos + self._value_width]
                result.append(FloatValue(chunk.strip()))
                pos += self._value_width

        self._data = tuple(result)

    def __str__(self) -> str:
        data_lines = []
        for i in range(0, len(self._data), self._values_per_line):
            chunk = self._data[i : i + self._values_per_line]
            line = "".join(str(v).rjust(self._value_width) for v in chunk)
            data_lines.append(line)

        return "\n".join([str(self._count)] + data_lines)

    @property
    def value(self) -> int:
        return self._count

    def __len__(self) -> int:
        return len(self._data)


T = TypeVar("T", bound="GeometryStructure")


class GeometryStructure(ABC):
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
        if not isinstance(other, GeometryStructure):
            return False
        return self._key_value_pairs == other._key_value_pairs

    def _parse_key_value_line(self, line: str) -> Tuple[str, str]:
        if "=" not in line:
            raise ValueError(f"Invalid key-value line: {line}")
        key, value = line.split("=", 1)
        return key.strip(), value.strip()

    def _format_key_value_line(self, key: str, value: Value) -> str:
        return f"{key}={str(value)}\n"

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
                        count = int(value_str.strip())
                        num_items_per_line = kwargs["values_per_line"] / kwargs["items_per_value"]
                        num_lines = math.ceil(count / num_items_per_line)

                        block_content = "\n".join([value_str] + lines[i + 1 : i + 1 + num_lines])

                        self[key] = DataBlockValue(block_content, **kwargs)
                        i += 1 + num_lines
                    else:
                        value = value_type(value_str, **kwargs)
                        self[key] = value
                        i += 1
                elif isinstance(value_type_info, type) and issubclass(value_type_info, Value):
                    value = value_type_info(value_str)
                    self[key] = value
                    i += 1
            else:
                i += 1

        return self

    def generate(self) -> List[str]:
        result = []
        for key, value in self._key_value_pairs.items():
            result.append(self._format_key_value_line(key, value))
        return result


class River(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "River Reach": (CommaSeparatedValue, {"element_type": StringValue}),
            "Reach XY": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "Rch Text X Y": (CommaSeparatedValue, {"element_type": StringValue}),
            "Reverse River Text": IntValue,
        }
        super().__init__(lines)


class BreakLine(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "BreakLine Name": StringValue,
            "BreakLine CellSize Min": StringValue,
            "BreakLine CellSize Max": StringValue,
            "BreakLine Near Repeats": IntValue,
            "BreakLine Protection Radius": IntValue,
            "BreakLine Polyline": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "LCMann Time": StringValue,
            "LCMann Region Time": StringValue,
            "LCMann Table": IntValue,
            "Chan Stop Cuts": IntValue,
        }
        super().__init__(lines)


class CrossSection(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Type RM Length L Ch R": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS GIS Cut Line": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "Node Last Edited Time": StringValue,
            "#Sta/Elev": (DataBlockValue, {"value_width": 8, "values_per_line": 10, "items_per_value": 2}),
            "#Mann": (CommaSeparatedValue, {"element_type": StringValue}),
            "Bank Sta": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS Rating Curve": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS HTab Starting El and Incr": (CommaSeparatedValue, {"element_type": StringValue}),
            "XS HTab Horizontal Distribution": (CommaSeparatedValue, {"element_type": StringValue}),
            "Exp/Cntr(USF)": (CommaSeparatedValue, {"element_type": StringValue}),
            "Exp/Cntr": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class Foot(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Use User Specified Reach Order": IntValue,
            "GIS Ratio Cuts To Invert": IntValue,
            "GIS Limit At Bridges": IntValue,
            "Composite Channel Slope": IntValue,
        }
        super().__init__(lines)


class Head(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Geom Title": StringValue,
            "Program Version": StringValue,
            "Viewing Rectangle": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class LateralWeir(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Type RM Length L Ch R": (CommaSeparatedValue, {"element_type": StringValue}),
            "Node Name": StringValue,
            "Node Last Edited Time": StringValue,
            "Lateral Weir Pos": IntValue,
            "Lateral Weir End": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir Distance": IntValue,
            "Lateral Weir TW Multiple XS": IntValue,
            "Lateral Weir WD": IntValue,
            "Lateral Weir Coef": FloatValue,
            "LW OverFlow Method 2D": IntValue,
            "LW OverFlow Use Velocity Into 2D": IntValue,
            "Lateral Weir WSCriteria": IntValue,
            "Lateral Weir Flap Gates": IntValue,
            "Lateral Weir Hagers EQN": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir SS": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir Type": IntValue,
            "Lateral Weir Connection Pos and Dist": (CommaSeparatedValue, {"element_type": StringValue}),
            "Lateral Weir SE": IntValue,
            "Lateral Weir Centerline": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
            "LW Div RC": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class StorageArea(GeometryStructure):
    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Storage Area": (CommaSeparatedValue, {"element_type": StringValue}),
            "Storage Area Surface Line": (DataBlockValue, {"value_width": 16, "values_per_line": 2, "items_per_value": 2}),
            "Storage Area Type": IntValue,
            "Storage Area Area": StringValue,
            "Storage Area Min Elev": StringValue,
            "Storage Area Is2D": IntValue,
            "Storage Area Point Generation Data": (CommaSeparatedValue, {"element_type": StringValue}),
            "Storage Area 2D Points": (DataBlockValue, {"value_width": 16, "values_per_line": 4, "items_per_value": 2}),
        }
        super().__init__(lines)
