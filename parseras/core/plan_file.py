"""
PlanFile 类 - 用于解析和生成 HEC-RAS 计划文件 (p01)

采用 block 分割解析，参考 GeometryFile 的设计：
  - PlanHead: Plan Title / Short Identifier / Simulation Date / Geom File / Flow File
  - PlanTimeInterval: Computation / Output / Instantaneous / Mapping Interval
  - PlanRunOptions: Run HTab / Run UNet / Run PostProcess / DSS File
  - PlanBreach: 溃坝结构（Breach Loc / Breach Geom / Breach Start 等）
  - 其余所有 key=value 直接丢弃
"""

from typing import Dict, List, Optional, Tuple, Type

from parseras.core.values import (
    Value,
    StringValue,
    CommaSeparatedValue,
)


# ---------------------------------------------------------------------------
# Plan 文件中的 block 类型
# ---------------------------------------------------------------------------


class PlanHead:
    """Plan 头信息：Plan Title / Short Identifier / Simulation Date / Geom File / Flow File"""

    order = 0.0
    KEYS = frozenset(
        ("Plan Title", "Short Identifier", "Simulation Date", "Geom File", "Flow File")
    )

    def __init__(self, lines: List[str] | None = None):
        self._kv: Dict[str, Value] = {}
        if lines:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        for line in lines:
            line = line.rstrip("\n")
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in self.KEYS:
                self._kv[key] = StringValue(value)

    def generate(self) -> List[str]:
        result = []
        for key in ("Plan Title", "Short Identifier", "Simulation Date", "Geom File", "Flow File"):
            if key in self._kv:
                result.append(f"{key}={self._kv[key].value}")
        return result

    def __getitem__(self, key: str) -> Value:
        return self._kv[key]

    def __setitem__(self, key: str, value: Value):
        self._kv[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._kv

    def __delitem__(self, key: str) -> None:
        del self._kv[key]

    @property
    def plan_title(self) -> Optional[str]:
        return self._kv["Plan Title"].value if "Plan Title" in self._kv else None

    @property
    def short_identifier(self) -> Optional[str]:
        return self._kv["Short Identifier"].value if "Short Identifier" in self._kv else None

    @property
    def simulation_date(self) -> Optional[str]:
        return self._kv["Simulation Date"].value if "Simulation Date" in self._kv else None

    @property
    def geom_file(self) -> Optional[str]:
        return self._kv["Geom File"].value if "Geom File" in self._kv else None

    @property
    def flow_file(self) -> Optional[str]:
        return self._kv["Flow File"].value if "Flow File" in self._kv else None


class PlanTimeInterval:
    """时间间隔：Computation / Output / Instantaneous / Mapping Interval"""

    order = 10.0
    KEYS = frozenset(
        (
            "Computation Interval",
            "Output Interval",
            "Instantaneous Interval",
            "Mapping Interval",
        )
    )

    def __init__(self, lines: List[str] | None = None):
        self._kv: Dict[str, Value] = {}
        if lines:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        for line in lines:
            line = line.rstrip("\n")
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in self.KEYS:
                self._kv[key] = StringValue(value)

    def generate(self) -> List[str]:
        result = []
        for key in self.KEYS:
            if key in self._kv:
                result.append(f"{key}={self._kv[key].value}")
        return result

    def __getitem__(self, key: str) -> Value:
        return self._kv[key]

    def __setitem__(self, key: str, value: Value):
        self._kv[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._kv

    def __delitem__(self, key: str) -> None:
        del self._kv[key]


class PlanRunOptions:
    """运行选项：Run HTab / Run UNet / Run PostProcess / DSS File"""

    order = 20.0
    KEYS = frozenset(
        (
            "Run HTab",
            "Run UNet",
            "Run PostProcess",
            "DSS File",
        )
    )

    def __init__(self, lines: List[str] | None = None):
        self._kv: Dict[str, Value] = {}
        if lines:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        for line in lines:
            line = line.rstrip("\n")
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in self.KEYS:
                self._kv[key] = StringValue(value)

    def generate(self) -> List[str]:
        result = []
        for key in self.KEYS:
            if key in self._kv:
                result.append(f"{key}={self._kv[key].value}")
        return result

    def __getitem__(self, key: str) -> Value:
        return self._kv[key]

    def __setitem__(self, key: str, value: Value):
        self._kv[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._kv

    def __delitem__(self, key: str) -> None:
        del self._kv[key]


class PlanBreach:
    """溃坝结构块：Breach Loc / Breach Method / Breach Geom / Breach Start 等

    Breach Loc 格式（逗号分隔）：
        river, reach, station, is_active(bool), structure
    若前3个字段非空，以此定位；若为空则以 structure 字段匹配。
    """

    order = 30.0

    LOC_RIVER = 0
    LOC_REACH = 1
    LOC_STATION = 2
    LOC_IS_ACTIVE = 3
    LOC_STRUCTURE = 4

    def __init__(self, lines: List[str] | None = None):
        self._loc: Optional[CommaSeparatedValue] = None
        self._geom: Optional[CommaSeparatedValue] = None
        self._start: Optional[CommaSeparatedValue] = None
        self._other_lines: List[str] = []
        if lines:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        for line in lines:
            line = line.rstrip("\n")
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key == "Breach Loc":
                self._loc = CommaSeparatedValue(value)
            elif key == "Breach Geom":
                self._geom = CommaSeparatedValue(value)
            elif key == "Breach Start":
                self._start = CommaSeparatedValue(value)
            else:
                self._other_lines.append(line)

    def generate(self) -> List[str]:
        result = []
        if self._loc is not None:
            result.append(f"Breach Loc={self._loc}")
        result.extend(self._other_lines)
        if self._geom is not None:
            result.append(f"Breach Geom={self._geom}")
        if self._start is not None:
            result.append(f"Breach Start={self._start}")
        return result

    @property
    def river(self) -> str:
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_RIVER].value.strip() if len(parts) > self.LOC_RIVER else ""

    @property
    def reach(self) -> str:
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_REACH].value.strip() if len(parts) > self.LOC_REACH else ""

    @property
    def station(self) -> str:
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_STATION].value.strip() if len(parts) > self.LOC_STATION else ""

    @property
    def is_active(self) -> bool:
        if self._loc is None:
            return False
        parts = self._loc.value
        if len(parts) > self.LOC_IS_ACTIVE:
            return parts[self.LOC_IS_ACTIVE].value.strip().lower() == "true"
        return False

    @property
    def structure_name(self) -> str:
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_STRUCTURE].value.strip() if len(parts) > self.LOC_STRUCTURE else ""

    @property
    def loc(self) -> Optional[CommaSeparatedValue]:
        return self._loc

    @property
    def geom(self) -> Optional[CommaSeparatedValue]:
        return self._geom

    @property
    def start(self) -> Optional[CommaSeparatedValue]:
        return self._start

    def set_loc(
        self, river: str = "", reach: str = "", station: str = "", is_active: bool = True, structure: str = ""
    ):
        self._loc = CommaSeparatedValue(f"{river},{reach},{station},{is_active},{structure}")

    def set_geom(self, values: Tuple):
        self._geom = CommaSeparatedValue(",".join(str(v) if v is not None else "" for v in values))

    def set_start(self, values: Tuple):
        self._start = CommaSeparatedValue(",".join(str(v) if v is not None else "" for v in values))

    def apply_geom(self, gv: "BreachGeomValue") -> None:
        """用 BreachGeomValue 设置 Breach Geom（自动生成 CSV）"""
        from parseras.core.values import BreachGeomFieldValue

        field = BreachGeomFieldValue()
        field.value = gv
        self._geom = CommaSeparatedValue(str(field))

    def apply_start(self, sv: "BreachStartValue") -> None:
        """用 BreachStartValue 设置 Breach Start（自动生成 CSV）"""
        from parseras.core.values import BreachStartFieldValue

        field = BreachStartFieldValue()
        field.value = sv
        self._start = CommaSeparatedValue(str(field))


# ---------------------------------------------------------------------------
# 校验函数（供 API 层使用）
# ---------------------------------------------------------------------------


class BreachValidationError(ValueError):
    """校验失败时抛出"""
    pass


REQUIRED_GEOM_FIELDS = frozenset(
    (
        "centerline",
        "final_bottom_width",
        "final_bottom_elev",
        "left_slope",
        "right_slope",
        "failure_mode",
        "formation_time",
        "breach_weir_coef",
    )
)
OPTIONAL_GEOM_FIELDS = frozenset(("piping_coef", "initial_piping_elev"))


def validate_breach_geom(data: dict):
    """校验 breach_geom 字典，强校验模式字段组合

    规则：
      - failure_mode == "piping" 时：必须有 piping_coef 和 initial_piping_elev
      - failure_mode == "overtopping" 时：不得有 piping_coef / initial_piping_elev
      - 不得传入未定义字段

    Returns:
        BreachGeomValue on success

    Raises:
        BreachValidationError: 校验失败
    """
    keys = frozenset(data.keys())
    extra = keys - (REQUIRED_GEOM_FIELDS | OPTIONAL_GEOM_FIELDS)
    if extra:
        raise BreachValidationError(f"breach_geom 不支持字段: {sorted(extra)}")

    missing = REQUIRED_GEOM_FIELDS - keys
    if missing:
        raise BreachValidationError(f"breach_geom 缺少必填字段: {sorted(missing)}")

    failure_mode = data["failure_mode"]
    if failure_mode not in ("overtopping", "piping"):
        raise BreachValidationError(f"failure_mode 必须是 'overtopping' 或 'piping'，得到 '{failure_mode}'")

    if failure_mode == "piping":
        if "piping_coef" not in data or data["piping_coef"] is None:
            raise BreachValidationError("failure_mode='piping' 时必须提供 piping_coef")
        if "initial_piping_elev" not in data or data["initial_piping_elev"] is None:
            raise BreachValidationError("failure_mode='piping' 时必须提供 initial_piping_elev")
    else:
        if "piping_coef" in data and data["piping_coef"] is not None:
            raise BreachValidationError("failure_mode='overtopping' 时不得提供 piping_coef")
        if "initial_piping_elev" in data and data["initial_piping_elev"] is not None:
            raise BreachValidationError("failure_mode='overtopping' 时不得提供 initial_piping_elev")

    from parseras.core.values import BreachGeomValue

    return BreachGeomValue(
        centerline=float(data["centerline"]),
        final_bottom_width=float(data["final_bottom_width"]),
        final_bottom_elev=float(data["final_bottom_elev"]),
        left_slope=float(data["left_slope"]),
        right_slope=float(data["right_slope"]),
        failure_mode=failure_mode,
        piping_coef=float(data["piping_coef"]) if failure_mode == "piping" else None,
        initial_piping_elev=float(data["initial_piping_elev"]) if failure_mode == "piping" else None,
        formation_time=float(data["formation_time"]),
        breach_weir_coef=float(data["breach_weir_coef"]),
    )


def validate_breach_start(data: dict):
    """校验 breach_start 字典，强校验 mode 字段组合

    mode 规则：
      - mode == "elevation_only"：必填 elevation，不得有 water_level/duration/accumulated/day/time
      - mode == "water_level_duration"：必填 elevation/water_level/duration_hours/accumulated，不得有 day/time
      - mode == "specific_time"：必填 day/time，不得有 elevation/water_level/duration/accumulated

    Returns:
        BreachStartValue on success

    Raises:
        BreachValidationError: 校验失败
    """
    if "mode" not in data:
        raise BreachValidationError("breach_start 缺少必填字段: mode")

    mode = data["mode"]
    if mode not in ("elevation_only", "water_level_duration", "specific_time"):
        raise BreachValidationError(
            f"mode 必须是 'elevation_only' / 'water_level_duration' / 'specific_time'，得到 '{mode}'"
        )

    from parseras.core.values import BreachStartValue

    if mode == "elevation_only":
        if "elevation" not in data or data["elevation"] is None:
            raise BreachValidationError("mode='elevation_only' 时必须提供 elevation")
        bad = frozenset(k for k in ("water_level", "duration_hours", "accumulated", "day", "time") if data.get(k) is not None)
        if bad:
            raise BreachValidationError(f"mode='elevation_only' 时不得提供字段: {sorted(bad)}")
        return BreachStartValue(
            mode=mode,
            elevation=float(data["elevation"]),
            water_level=None,
            duration_hours=None,
            accumulated=None,
            day=None,
            time=None,
        )

    elif mode == "water_level_duration":
        for f in ("elevation", "water_level", "duration_hours", "accumulated"):
            if f not in data or data[f] is None:
                raise BreachValidationError(f"mode='water_level_duration' 时必须提供 {f}")
        bad = frozenset(k for k in ("day", "time") if data.get(k) is not None)
        if bad:
            raise BreachValidationError(f"mode='water_level_duration' 时不得提供字段: {sorted(bad)}")
        return BreachStartValue(
            mode=mode,
            elevation=float(data["elevation"]),
            water_level=float(data["water_level"]),
            duration_hours=float(data["duration_hours"]),
            accumulated=bool(data["accumulated"]),
            day=None,
            time=None,
        )

    else:
        for f in ("day", "time"):
            if f not in data or data[f] is None:
                raise BreachValidationError(f"mode='specific_time' 时必须提供 {f}")
        bad = frozenset(k for k in ("elevation", "water_level", "duration_hours", "accumulated") if data.get(k) is not None)
        if bad:
            raise BreachValidationError(f"mode='specific_time' 时不得提供字段: {sorted(bad)}")
        return BreachStartValue(
            mode=mode,
            elevation=None,
            water_level=None,
            duration_hours=None,
            accumulated=None,
            day=int(data["day"]),
            time=str(data["time"]),
        )


# ---------------------------------------------------------------------------
# PlanFile 主类
# ---------------------------------------------------------------------------


class PlanFile:
    """HEC-RAS 计划文件解析器（block 分割版本）"""

    BLOCK_STARTS = [
        "Plan Title=",
        "Short Identifier=",
        "Simulation Date=",
        "Geom File=",
        "Flow File=",
        "Computation Interval=",
        "Output Interval=",
        "Instantaneous Interval=",
        "Mapping Interval=",
        "Run HTab=",
        "Run UNet=",
        "Run PostProcess=",
        "DSS File=",
        "Breach Loc=",
    ]

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._blocks: List = []
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self._parse_lines(lines)
        elif lines is not None:
            self._parse_lines(lines)

    # -------------------------------------------------------------------------
    # Block 分割
    # -------------------------------------------------------------------------

    def _split_into_blocks(self, raw_lines: List[str]) -> List[List[str]]:
        """只收集已知类型的块，未知行直接丢弃"""
        blocks: List[List[str]] = []
        current_block: List[str] = []
        current_type: Optional[str] = None

        def flush():
            nonlocal current_block, current_type
            if current_block:
                blocks.append(current_block)
                current_block = []
                current_type = None

        # key -> block type name
        ALL_KEYS: Dict[str, str] = {}
        for k in PlanHead.KEYS:
            ALL_KEYS[k] = "PlanHead"
        for k in PlanTimeInterval.KEYS:
            ALL_KEYS[k] = "PlanTimeInterval"
        for k in PlanRunOptions.KEYS:
            ALL_KEYS[k] = "PlanRunOptions"

        def _block_type(line: str) -> Optional[str]:
            key = line.strip().split("=", 1)[0].strip()
            return ALL_KEYS.get(key)

        def _is_breach_start(line: str) -> bool:
            return line.strip().startswith("Breach Loc=")

        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                flush()
                continue

            if _is_breach_start(stripped):
                flush()
                block_lines = [line]
                j = raw_lines.index(line) + 1
                while j < len(raw_lines):
                    nxt = raw_lines[j].strip()
                    if not nxt or _is_breach_start(nxt):
                        break
                    block_lines.append(raw_lines[j])
                    j += 1
                blocks.append(block_lines)
                continue

            bt = _block_type(line)
            if bt is None:
                continue

            if bt != current_type:
                flush()
                current_block = [line]
                current_type = bt
            else:
                current_block.append(line)

        flush()
        return blocks

    def _determine_block_type(self, block: List[str]) -> Type:
        first = block[0].strip()
        key = first.split("=", 1)[0].strip()

        type_map: Dict[str, Type] = {}
        for k in PlanHead.KEYS:
            type_map[k] = PlanHead
        for k in PlanTimeInterval.KEYS:
            type_map[k] = PlanTimeInterval
        for k in PlanRunOptions.KEYS:
            type_map[k] = PlanRunOptions
        type_map["Breach Loc"] = PlanBreach

        return type_map.get(key, PlanHead)

    # -------------------------------------------------------------------------
    # 解析与生成
    # -------------------------------------------------------------------------

    def _parse_lines(self, lines: List[str]):
        blocks = self._split_into_blocks(lines)
        for block in blocks:
            block_type = self._determine_block_type(block)
            self._blocks.append(block_type(block))

    def generate(self) -> List[str]:
        result: List[str] = []
        sorted_blocks = sorted(self._blocks, key=lambda b: getattr(b, "order", 100.0))
        for i, block in enumerate(sorted_blocks):
            block_lines = block.generate()
            result.extend(block_lines)
            if i < len(sorted_blocks) - 1 and block_lines:
                result.append("")
        return result

    # -------------------------------------------------------------------------
    # Block 访问
    # -------------------------------------------------------------------------

    def get_blocks(self) -> List:
        return self._blocks

    def get_blocks_by_type(self, block_type: Type):
        return [b for b in self._blocks if isinstance(b, block_type)]

    @property
    def head(self) -> Optional[PlanHead]:
        blocks = self.get_blocks_by_type(PlanHead)
        return blocks[0] if blocks else None

    @property
    def time_interval(self) -> Optional[PlanTimeInterval]:
        blocks = self.get_blocks_by_type(PlanTimeInterval)
        return blocks[0] if blocks else None

    @property
    def run_options(self) -> Optional[PlanRunOptions]:
        blocks = self.get_blocks_by_type(PlanRunOptions)
        return blocks[0] if blocks else None

    def get_breaches(self) -> List[PlanBreach]:
        return self.get_blocks_by_type(PlanBreach)

    def get_breach_by_structure(self, name: str) -> Optional[PlanBreach]:
        for b in self.get_breaches():
            if b.structure_name == name:
                return b
        return None

    def get_breach(self, river: str = "", reach: str = "", station: str = "") -> Optional[PlanBreach]:
        target_river = river.strip().lower()
        target_reach = reach.strip().lower()
        target_station = station.strip()
        for b in self.get_breaches():
            if b.river.lower() == target_river and b.reach.lower() == target_reach and b.station == target_station:
                return b
        return None

    # -------------------------------------------------------------------------
    # 读写 key=value
    # -------------------------------------------------------------------------

    def get(self, key: str) -> Optional[str]:
        for block in self._blocks:
            if key in block:
                return str(block[key].value)
        return None

    def set(self, key: str, value: str):
        """设置字段值，空字符串删除该键"""
        if value == "":
            self.delete(key)
            return
        bt = self._key_block_type(key)
        if bt == PlanBreach:
            raise ValueError("Breach 块请使用 add_breach() 新增，或通过 get_breaches()[n] 直接修改")
        blocks = self.get_blocks_by_type(bt)
        if blocks:
            blocks[0][key] = StringValue(value)
        else:
            new_block = bt()
            new_block[key] = StringValue(value)
            self._blocks.append(new_block)
            self._blocks.sort(key=lambda b: getattr(b, "order", 100.0))

    def delete(self, key: str):
        bt = self._key_block_type(key)
        blocks = self.get_blocks_by_type(bt)
        if not blocks:
            return
        if key not in blocks[0]:
            return
        del blocks[0][key]

    def add_breach(self, breach: PlanBreach):
        self._blocks.append(breach)

    def _key_block_type(self, key: str) -> Type:
        if key in PlanHead.KEYS:
            return PlanHead
        if key in PlanTimeInterval.KEYS:
            return PlanTimeInterval
        if key in PlanRunOptions.KEYS:
            return PlanRunOptions
        raise KeyError(f"未知字段: {key}")

    # -------------------------------------------------------------------------
    # 属性快捷访问
    # -------------------------------------------------------------------------

    @property
    def geom_file(self) -> Optional[str]:
        h = self.head
        return h.geom_file if h else None

    @property
    def flow_file(self) -> Optional[str]:
        h = self.head
        return h.flow_file if h else None

    @property
    def plan_title(self) -> Optional[str]:
        h = self.head
        return h.plan_title if h else None
