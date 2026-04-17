"""
PlanFile 类 - 用于解析和生成 HEC-RAS 计划文件 (p01)

采用 block 分割解析，参考 GeometryFile 的设计：
  - PlanHead: Plan Title / Short Identifier / Simulation Date
  - PlanFileRef: Geom File / Flow File
  - PlanTimeInterval: Computation / Output / Instantaneous / Mapping Interval
  - PlanRunOptions: Run HTab / Run UNet / Run PostProcess / DSS File
  - PlanBreach: 溃坝结构（Breach Loc / Breach Geom / Breach Start）
  - 其余键保留为普通 key=value 格式，兼容旧代码
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
    """Plan 头信息：Plan Title / Short Identifier / Simulation Date"""

    order = 0.0
    HEAD_KEYS = frozenset(("Plan Title", "Short Identifier", "Simulation Date"))

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
            key = key.strip()
            value = value.strip()
            if key in self.HEAD_KEYS:
                self._kv[key] = StringValue(value)

    def generate(self) -> List[str]:
        result = []
        for key in ("Plan Title", "Short Identifier", "Simulation Date"):
            if key in self._kv:
                result.append(f"{key}={self._kv[key].value}")
        return result

    def __getitem__(self, key: str) -> Value:
        return self._kv[key]

    def __setitem__(self, key: str, value: Value):
        self._kv[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._kv

    @property
    def plan_title(self) -> Optional[str]:
        return self._kv["Plan Title"].value if "Plan Title" in self._kv else None

    @property
    def short_identifier(self) -> Optional[str]:
        return self._kv["Short Identifier"].value if "Short Identifier" in self._kv else None

    @property
    def simulation_date(self) -> Optional[str]:
        return self._kv["Simulation Date"].value if "Simulation Date" in self._kv else None


class PlanFileRef:
    """文件引用：Geom File / Flow File（可能在一行或多行）"""

    order = 5.0
    REFS_KEYS = frozenset(("Geom File", "Flow File"))

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
            key = key.strip()
            value = value.strip()
            if key in self.REFS_KEYS:
                self._kv[key] = StringValue(value)

    def generate(self) -> List[str]:
        result = []
        for key in ("Geom File", "Flow File"):
            if key in self._kv:
                result.append(f"{key}={self._kv[key].value}")
        return result

    def __getitem__(self, key: str) -> Value:
        return self._kv[key]

    def __setitem__(self, key: str, value: Value):
        self._kv[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._kv

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
            key = key.strip()
            value = value.strip()
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
            key = key.strip()
            value = value.strip()
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


class PlanBreach:
    """溃坝结构块：Breach Loc / Breach Method / Breach Geom / Breach Start 等

    Breach Loc 格式（逗号分隔）：
        river, reach, station, is_active(bool), structure
    若前3个字段非空，以此定位；若为空则以 structure 字段匹配。
    """

    order = 30.0

    # Breach Loc 5个字段的索引
    LOC_RIVER = 0
    LOC_REACH = 1
    LOC_STATION = 2
    LOC_IS_ACTIVE = 3
    LOC_STRUCTURE = 4

    def __init__(self, lines: List[str] | None = None):
        self._loc: Optional[CommaSeparatedValue] = None
        self._geom: Optional[CommaSeparatedValue] = None
        self._start: Optional[CommaSeparatedValue] = None
        self._other_lines: List[str] = []  # 保留块内其余行（如 Breach Method 等）
        if lines:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        for line in lines:
            line = line.rstrip("\n")
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
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
        """溃坝所在河流名称"""
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_RIVER].value.strip() if len(parts) > self.LOC_RIVER else ""

    @property
    def reach(self) -> str:
        """溃坝所在河段名称"""
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_REACH].value.strip() if len(parts) > self.LOC_REACH else ""

    @property
    def station(self) -> str:
        """溃坝所在断面桩号"""
        if self._loc is None:
            return ""
        parts = self._loc.value
        return parts[self.LOC_STATION].value.strip() if len(parts) > self.LOC_STATION else ""

    @property
    def is_active(self) -> bool:
        """溃坝是否激活"""
        if self._loc is None:
            return False
        parts = self._loc.value
        if len(parts) > self.LOC_IS_ACTIVE:
            return parts[self.LOC_IS_ACTIVE].value.strip().lower() == "true"
        return False

    @property
    def structure_name(self) -> str:
        """从 Breach Loc 提取 structure 名称（最后一个字段，strip 空白）"""
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
        """设置 Breach Loc"""
        self._loc = CommaSeparatedValue(f"{river},{reach},{station},{is_active},{structure}")

    def set_geom(self, values: Tuple):
        """设置 Breach Geom（逗号分隔的数值列表）"""
        self._geom = CommaSeparatedValue(",".join(str(v) if v is not None else "" for v in values))

    def set_start(self, values: Tuple):
        """设置 Breach Start（逗号分隔的数值列表）"""
        self._start = CommaSeparatedValue(",".join(str(v) if v is not None else "" for v in values))


# ---------------------------------------------------------------------------
# PlanFile 主类
# ---------------------------------------------------------------------------


class PlanFile:
    """HEC-RAS 计划文件解析器（block 分割版本）"""

    # 块起始前缀
    BLOCK_STARTS = [
        "Plan Title=",
        "Geom File=",
        "Flow File=",
        "Computation Interval=",
        "Run HTab=",
        "Breach Loc=",
    ]

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._blocks: List = []  # 混合类型的 block 列表
        self._kv_block: Dict[str, str] = {}  # 未归入任何 block 的 key=value
        self._kv_order: List[str] = []  # 保持 key 的原始顺序

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
        blocks: List[List[str]] = []
        current_block: List[str] = []
        pending_kv: List[str] = []
        # 当前上下文：当前块对应的 block_type（初始 None）
        ctx_block_type: Optional[str] = None

        def flush_current():
            nonlocal current_block, ctx_block_type
            if current_block:
                blocks.append(current_block)
                current_block = []
                ctx_block_type = None

        def flush_pending():
            nonlocal pending_kv
            for ln in pending_kv:
                if "=" in ln:
                    k, v = ln.split("=", 1)
                    k, v = k.strip(), v.strip()
                    self._kv_block[k] = v
                    if k not in self._kv_order:
                        self._kv_order.append(k)
            pending_kv = []

        # 判断某行属于哪个 block type（None 表示不属于任何已知 block）
        def _key_block_type(key: str) -> Optional[str]:
            if key in PlanHead.HEAD_KEYS:
                return "PlanHead"
            if key in PlanFileRef.REFS_KEYS:
                return "PlanFileRef"
            if key in PlanTimeInterval.KEYS:
                return "PlanTimeInterval"
            if key in PlanRunOptions.KEYS:
                return "PlanRunOptions"
            return None

        FILE_REF_PREFIXES = ("Geom File=", "Flow File=")

        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]
            stripped = line.strip()

            if not stripped:
                flush_current()
                flush_pending()
                i += 1
                continue

            is_block_start = any(stripped.startswith(p) for p in self.BLOCK_STARTS)
            is_file_ref = any(stripped.startswith(p) for p in FILE_REF_PREFIXES)

            # Breach Loc 特殊处理：收集从 Breach Loc= 到下一个 Breach Loc= 或空行 之间的所有行
            if stripped.startswith("Breach Loc="):
                flush_current()
                flush_pending()
                block_lines = [line]
                j = i + 1
                while j < len(raw_lines):
                    nxt = raw_lines[j].strip()
                    if not nxt or nxt.startswith("Breach Loc="):
                        break
                    block_lines.append(raw_lines[j])
                    j += 1
                blocks.append(block_lines)
                i = j
                continue

            if is_block_start or is_file_ref:
                if is_file_ref:
                    # 文件引用行单独处理：可能需要 flush 前的 block
                    first_key = stripped.split("=", 1)[0].strip()
                    kt = _key_block_type(first_key) or "PlanFileRef"
                    if current_block and ctx_block_type is not None and ctx_block_type != kt:
                        flush_current()
                        flush_pending()
                    elif not current_block:
                        flush_pending()
                    current_block.append(line)
                    ctx_block_type = kt
                else:
                    # 普通块起始行
                    if current_block:
                        flush_current()
                        flush_pending()
                    current_block.append(line)
                    first_key = stripped.split("=", 1)[0].strip()
                    ctx_block_type = _key_block_type(first_key)
                i += 1
            else:
                # 普通行：检查是否属于当前上下文的 block
                if "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if current_block and _key_block_type(key) == ctx_block_type:
                        # 属于当前 block 的子键，加入 current_block
                        current_block.append(line)
                        i += 1
                        continue
                # 不属于当前 block
                flush_current()
                pending_kv.append(line)
                i += 1

        flush_current()
        flush_pending()
        return blocks

    def _determine_block_type(self, block: List[str]) -> Optional[Type]:
        first = block[0].strip()
        key = first.split("=", 1)[0].strip()

        type_map = {
            "Plan Title": PlanHead,
            "Geom File": PlanFileRef,
            "Flow File": PlanFileRef,
            "Computation Interval": PlanTimeInterval,
            "Run HTab": PlanRunOptions,
            "Breach Loc": PlanBreach,
        }
        return type_map.get(key)

    # -------------------------------------------------------------------------
    # 解析与生成
    # -------------------------------------------------------------------------

    def _parse_lines(self, lines: List[str]):
        blocks = self._split_into_blocks(lines)

        for block in blocks:
            block_type = self._determine_block_type(block)
            if block_type is None:
                for line in block:
                    stripped = line.strip()
                    if "=" in stripped:
                        k, v = stripped.split("=", 1)
                        k, v = k.strip(), v.strip()
                        self._kv_block[k] = v
                        if k not in self._kv_order:
                            self._kv_order.append(k)
                continue

            block_instance = block_type(block)
            self._blocks.append(block_instance)

    def generate(self) -> List[str]:
        result: List[str] = []
        sorted_blocks = sorted(self._blocks, key=lambda b: getattr(b, "order", 100.0))
        for i, block in enumerate(sorted_blocks):
            block_lines = block.generate()
            result.extend(block_lines)
            if i < len(sorted_blocks) - 1 and block_lines:
                result.append("")
        for key in self._kv_order:
            if key in self._kv_block:
                result.append(f"{key}={self._kv_block[key]}")
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
    def file_ref(self) -> Optional[PlanFileRef]:
        blocks = self.get_blocks_by_type(PlanFileRef)
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
        """按 river/reach/station 匹配溃坝块（忽略大小写和空格）"""
        target_river = river.strip().lower()
        target_reach = reach.strip().lower()
        target_station = station.strip()
        for b in self.get_breaches():
            if b.river.lower() == target_river and b.reach.lower() == target_reach and b.station == target_station:
                return b
        return None

    # -------------------------------------------------------------------------
    # 简单 key=value 访问（兼容旧代码）
    # -------------------------------------------------------------------------

    def get(self, key: str) -> Optional[str]:
        if key in self._kv_block:
            return self._kv_block[key]
        for block in self._blocks:
            if key in block:
                return str(block[key].value)
        return None

    def set(self, key: str, value: str):
        self._kv_block[key] = value
        if key not in self._kv_order:
            self._kv_order.append(key)

    @property
    def geom_file(self) -> Optional[str]:
        fr = self.file_ref
        return fr.geom_file if fr else None

    @property
    def flow_file(self) -> Optional[str]:
        fr = self.file_ref
        return fr.flow_file if fr else None

    @property
    def plan_title(self) -> Optional[str]:
        h = self.head
        return h.plan_title if h else None
