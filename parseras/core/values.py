from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple, Type, Optional


class Value(ABC):
    @abstractmethod
    def __init__(self, value_str: Optional[str] = None):
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    @abstractmethod
    def value(self) -> Any:
        pass

    @value.setter
    @abstractmethod
    def value(self, new_value: Any) -> None:
        pass


class StringValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = value_str.strip() if value_str else ""

    def __str__(self) -> str:
        return self._value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value


class IntValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = int(value_str.strip()) if value_str else 0

    def __str__(self) -> str:
        return str(self._value)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_value: int) -> None:
        self._value = new_value


class FloatValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = float(value_str.strip()) if value_str else 0.0

    def __str__(self) -> str:
        v = self._value
        return str(int(v) if v.is_integer() else v)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        self._value = new_value


class CommaSeparatedValue(Value):
    def __init__(self, value_str: Optional[str] = None, element_type: Type[Value] = StringValue):
        self._element_type = element_type
        if value_str:
            self._value = tuple(element_type(part.strip()) for part in value_str.split(","))
        else:
            self._value = tuple()

    def __str__(self) -> str:
        return ",".join(str(v) if v is not None else "" for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value

    @value.setter
    def value(self, new_value: Tuple[Any, ...]) -> None:
        self._value = new_value


class SpaceSeparatedValue(Value):
    def __init__(self, value_str: Optional[str] = None, element_type: Type[Value] = StringValue):
        self._element_type = element_type
        if value_str:
            self._value = tuple(element_type(part.strip()) for part in value_str.split())
        else:
            self._value = tuple()

    def __str__(self) -> str:
        return " ".join(str(v) for v in self._value)

    @property
    def value(self) -> Tuple[Any, ...]:
        return self._value

    @value.setter
    def value(self, new_value: Tuple[Any, ...]) -> None:
        self._value = new_value


class LinesValue(Value):
    def __init__(self, value_str: Optional[str] = None):
        self._value = value_str if value_str else ""

    def __str__(self) -> str:
        return self._value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value


@dataclass
class BreachGeomValue:
    """Breach Geom 解析结果（10个字段）

    Fields:
        centerline: Breach centerline/station location
        final_bottom_width: Final breach bottom width
        final_bottom_elev: Final breach bottom elevation
        left_slope: Left side slope (H:V)
        right_slope: Right side slope (H:V)
        failure_mode: "overtopping" | "piping"
        piping_coef: 只在 piping 模式时有效
        initial_piping_elev: 只在 piping 模式时有效
        formation_time: Time (hrs)
        breach_weir_coef: Breach weir coefficient
    """
    centerline: float
    final_bottom_width: float
    final_bottom_elev: float
    left_slope: float
    right_slope: float
    failure_mode: str  # "overtopping" | "piping"
    piping_coef: Optional[float]
    initial_piping_elev: Optional[float]
    formation_time: float
    breach_weir_coef: float


class BreachGeomFieldValue(Value):
    """Breach Geom 字段值，解析 HEC-RAS 的 Breach Geom CSV 格式

    格式: centerline,final_bottom_width,final_bottom_elev,left_slope,right_slope,failure_mode,piping_coef,initial_piping_elev,formation_time,breach_weir_coef

    failure_mode:
        True / Piping  -> "piping"
        False / Overtopping -> "overtopping"
    """

    def __init__(self, value_str: Optional[str] = None):
        self._value: Optional[BreachGeomValue] = None
        if value_str:
            self._parse(value_str.strip())

    def _parse(self, s: str):
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 10:
            self._value = None
            return

        def _float(v: str) -> float:
            return float(v) if v else 0.0

        fm_raw = parts[5].lower()
        failure_mode = "piping" if fm_raw in ("true", "piping") else "overtopping"

        self._value = BreachGeomValue(
            centerline=_float(parts[0]),
            final_bottom_width=_float(parts[1]),
            final_bottom_elev=_float(parts[2]),
            left_slope=_float(parts[3]),
            right_slope=_float(parts[4]),
            failure_mode=failure_mode,
            piping_coef=_float(parts[6]) if failure_mode == "piping" else None,
            initial_piping_elev=_float(parts[7]) if failure_mode == "piping" else None,
            formation_time=_float(parts[8]),
            breach_weir_coef=_float(parts[9]),
        )

    def __str__(self) -> str:
        if self._value is None:
            return ""
        v = self._value
        fm = "True" if v.failure_mode == "piping" else "False"
        parts = [
            str(v.centerline),
            str(v.final_bottom_width),
            str(v.final_bottom_elev),
            str(v.left_slope),
            str(v.right_slope),
            fm,
            str(v.piping_coef if v.piping_coef is not None else ""),
            str(v.initial_piping_elev if v.initial_piping_elev is not None else ""),
            str(v.formation_time),
            str(v.breach_weir_coef),
        ]
        return ",".join(parts)

    @property
    def value(self) -> Optional[BreachGeomValue]:
        return self._value

    @value.setter
    def value(self, new_value: BreachGeomValue) -> None:
        self._value = new_value


# ---------------------------------------------------------------------------
# Breach Start 字段值（3种模式）
# ---------------------------------------------------------------------------

@dataclass
class BreachStartValue:
    """Breach Start 解析结果（3种模式）

    mode 决定哪些字段有效:
      - "elevation_only": [0]=True, [4]=False，仅关注 elevation（[1]）
      - "water_level_duration": [0]=False, [4]=True，关注 elevation/water_level/duration/accumulated（[1]/[5]/[6]/[7]）
      - "specific_time": [0]=False, [4]=False，关注 day/time（[3]/[4]）
    """
    mode: str  # "elevation_only" | "water_level_duration" | "specific_time"
    elevation: Optional[float]
    water_level: Optional[float]
    duration_hours: Optional[float]
    accumulated: Optional[bool]  # -1=True, 0=False
    day: Optional[int]
    time: Optional[str]  # "HH:MM"


class BreachStartFieldValue(Value):
    """Breach Start 字段值，解析 HEC-RAS 的 Breach Start CSV 格式（8个字段）

    根据 [0] 和 [4] 的组合确定模式：
      - [0]=True, [4]=False  -> elevation_only，字段 [1] 有意义，[7] 总为 0
      - [0]=False, [4]=True  -> water_level_duration，字段 [1]/[5]/[6]/[7] 有意义
      - [0]=False, [4]=False -> specific_time，字段 [3]/[4] 有意义，[7] 总为 0
    """

    def __init__(self, value_str: Optional[str] = None):
        self._value: Optional[BreachStartValue] = None
        if value_str:
            self._parse(value_str.strip())

    def _parse(self, s: str):
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 8:
            self._value = None
            return

        flag0 = parts[0].lower() in ("true", "1", "yes")
        flag4 = parts[4].lower() in ("true", "1", "yes")

        if flag0 and not flag4:
            mode = "elevation_only"
            elevation = float(parts[1]) if parts[1] else None
            self._value = BreachStartValue(
                mode=mode,
                elevation=elevation,
                water_level=None,
                duration_hours=None,
                accumulated=None,
                day=None,
                time=None,
            )
        elif not flag0 and flag4:
            mode = "water_level_duration"
            elevation = float(parts[1]) if parts[1] else None
            water_level = float(parts[5]) if parts[5] else None
            duration_hours = float(parts[6]) if parts[6] else None
            acc_raw = parts[7].strip()
            accumulated = (acc_raw == "-1") if acc_raw in ("-1", "0") else None
            self._value = BreachStartValue(
                mode=mode,
                elevation=elevation,
                water_level=water_level,
                duration_hours=duration_hours,
                accumulated=accumulated,
                day=None,
                time=None,
            )
        else:
            mode = "specific_time"
            day = int(parts[3]) if parts[3] else None
            time = parts[4] if parts[4] else None
            self._value = BreachStartValue(
                mode=mode,
                elevation=None,
                water_level=None,
                duration_hours=None,
                accumulated=None,
                day=day,
                time=time,
            )

    def __str__(self) -> str:
        if self._value is None:
            return ""
        v = self._value
        if v.mode == "elevation_only":
            elevation = str(v.elevation) if v.elevation is not None else ""
            return f"True,{elevation},,,,False,,0"
        elif v.mode == "water_level_duration":
            elevation = str(v.elevation) if v.elevation is not None else ""
            water_level = str(v.water_level) if v.water_level is not None else ""
            duration = str(v.duration_hours) if v.duration_hours is not None else ""
            acc = "-1" if v.accumulated else "0"
            return f"False,{elevation},,{water_level},True,{duration},{acc}"
        else:
            day = str(v.day) if v.day is not None else ""
            time = v.time if v.time is not None else ""
            return f"False,,1,{day},False,,,0"

    @property
    def value(self) -> Optional[BreachStartValue]:
        return self._value

    @value.setter
    def value(self, new_value: BreachStartValue) -> None:
        self._value = new_value


@dataclass
class DataValue:
    data: Tuple
    value_width: int
    values_per_line: int
    items_per_value: int
    header_values: Tuple
    count: int


class DataBlockValue(Value):
    def __init__(
        self, value_str: Optional[str] = None, value_width: int = 0, values_per_line: int = 0, items_per_value: int = 0
    ):
        if value_str:
            lines = value_str.split("\n")

            header_line = lines[0].strip()
            header_parts = [part.strip() for part in header_line.split(",")]
            header_values = tuple(header_parts)
            count = int(header_parts[0])

            data_lines = lines[1:]

            result = []
            for line in data_lines:
                line = line.rstrip()
                pos = 0
                while pos < len(line):
                    chunk = line[pos : pos + value_width].lstrip()
                    result.append(FloatValue(chunk))
                    pos += value_width

            data = tuple(result)

            self._value = DataValue(data, value_width, values_per_line, items_per_value, header_values, count)
        else:
            # 创建空的DataBlockValue
            self._value = DataValue(tuple(), value_width, values_per_line, items_per_value, ("0",), 0)

    def __str__(self) -> str:
        data_lines = []
        for i in range(0, len(self._value.data), self._value.values_per_line):
            chunk = self._value.data[i : i + self._value.values_per_line]
            line = "".join(str(v).rjust(self._value.value_width)[:self._value.value_width] for v in chunk)
            data_lines.append(line)

        return "\n".join([",".join(self._value.header_values)] + data_lines)

    @property
    def value(self) -> DataValue:
        return self._value

    @value.setter
    def value(self, new_value: DataValue) -> None:
        self._value = new_value
