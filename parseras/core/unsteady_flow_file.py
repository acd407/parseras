from typing import List, Type

from parseras.core.values import (
    StringValue,
    IntValue,
    FloatValue,
    CommaSeparatedValue,
    DataBlockValue,
)
from parseras.core.structures import RASStructure


class UnsteadyFlowHead(RASStructure):
    order = 0

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Flow Title": StringValue,
        }
        super().__init__(lines)


class InitialStorageElev(RASStructure):
    order = 10

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Initial Storage Elev": (CommaSeparatedValue, {"element_type": StringValue}),
        }
        super().__init__(lines)


class BoundaryCondition(RASStructure):
    order = 20

    def __init__(self, lines: List[str]):
        self._key_value_types = {
            "Boundary Location": (CommaSeparatedValue, {"element_type": StringValue}),
            "Interval": StringValue,
            "Flow Hydrograph": (
                DataBlockValue,
                {"value_width": 8, "values_per_line": 10, "items_per_value": 1},
            ),
            "Flow Hydrograph Slope": StringValue,
            "Stage Hydrograph": (
                DataBlockValue,
                {"value_width": 8, "values_per_line": 10, "items_per_value": 1},
            ),
            "Stage Hydrograph Use Initial Stage": IntValue,
            "Stage and Flow Hydrograph": (
                DataBlockValue,
                {"value_width": 8, "values_per_line": 10, "items_per_value": 2},
            ),
            "Rating Curve": (
                DataBlockValue,
                {"value_width": 8, "values_per_line": 10, "items_per_value": 2},
            ),
            "Friction Slope": (CommaSeparatedValue, {"element_type": FloatValue}),
        }
        super().__init__(lines)


class UnsteadyFlowFile:
    BLOCK_STARTS = [
        "Flow Title=",
        "Initial Storage Elev=",
        "Boundary Location=",
    ]

    # 5种BC数据类型标识
    BC_TYPE_STAGE_HYDROGRAPH = "stage_hydrograph"
    BC_TYPE_FLOW_HYDROGRAPH = "flow_hydrograph"
    BC_TYPE_STAGE_FLOW_HYDROGRAPH = "stage_flow_hydrograph"
    BC_TYPE_RATING_CURVE = "rating_curve"
    BC_TYPE_FRICTION_SLOPE = "friction_slope"

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._blocks: List[RASStructure] = []

        if file_path:
            with open(file_path, "r", encoding='utf-8') as f:
                lines = f.readlines()
            self._parse_lines(lines)
        elif lines is not None:
            self._parse_lines(lines)

    def _split_into_blocks(self, lines: List[str]) -> List[List[str]]:
        blocks = []
        current_block = []

        for line in lines:
            for prefix in self.BLOCK_STARTS:
                if line.startswith(prefix):
                    if current_block:
                        blocks.append(current_block)
                        current_block = []
                    break

            current_block.append(line)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _determine_block_type(self, block: List[str]) -> Type[RASStructure]:
        if not block:
            raise ValueError("Empty block")

        first_line = block[0].strip()

        if first_line.startswith("Flow Title"):
            return UnsteadyFlowHead
        elif first_line.startswith("Initial Storage Elev"):
            return InitialStorageElev
        elif first_line.startswith("Boundary Location"):
            return BoundaryCondition

        raise ValueError(f"Unknown block type for first line: {first_line}")

    def _parse_lines(self, lines: List[str]):
        blocks = self._split_into_blocks(lines)

        for block in blocks:
            block_type = self._determine_block_type(block)
            block_instance = block_type(block)
            self._blocks.append(block_instance)

    def generate(self) -> List[str]:
        result = []
        sorted_blocks = sorted(self._blocks, key=lambda block: getattr(block, "order", 100.0))
        for i, block in enumerate(sorted_blocks):
            block_lines = block.generate()
            result.extend(block_lines)
            if i < len(sorted_blocks) - 1:
                result.append("")
        return result

    def get_blocks(self) -> List[RASStructure]:
        return self._blocks

    def get_blocks_by_type(self, block_type: Type[RASStructure]) -> List[RASStructure]:
        return [block for block in self._blocks if isinstance(block, block_type)]

    # ==================== BC 数据类型解析 ====================

    def get_bc_data_type(self, bc: BoundaryCondition) -> str | None:
        """判断BC的数据类型（5种之一），返回标识符字符串"""
        if "Stage and Flow Hydrograph" in bc:
            return self.BC_TYPE_STAGE_FLOW_HYDROGRAPH
        if "Rating Curve" in bc:
            return self.BC_TYPE_RATING_CURVE
        if "Friction Slope" in bc:
            return self.BC_TYPE_FRICTION_SLOPE
        if "Stage Hydrograph" in bc:
            return self.BC_TYPE_STAGE_HYDROGRAPH
        if "Flow Hydrograph" in bc:
            return self.BC_TYPE_FLOW_HYDROGRAPH
        return None

    def parse_bc_values(self, bc: BoundaryCondition) -> dict:
        """解析BC数据块的所有值，返回统一格式的字典

        Returns:
            {
                "data_type": "flow_hydrograph" | "stage_hydrograph" | ...,
                "interval": "1HOUR" | "6Min" | ...,
                "values": [...],          # 扁平值列表
                "paired_values": [...],    # [stage, flow, stage, flow, ...] 用于 type 3/4
                "slope": "0.1",            # Flow Hydrograph Slope / Friction Slope
                "use_initial_stage": -1,   # Stage Hydrograph 专用
            }
        """
        result: dict = {
            "data_type": self.get_bc_data_type(bc),
            "interval": bc["Interval"].value if "Interval" in bc else None,
            "values": [],
            "paired_values": [],
            "slope": None,
            "use_initial_stage": None,
        }

        # Flow Hydrograph
        if "Flow Hydrograph" in bc:
            hv = bc["Flow Hydrograph"].value
            if hasattr(hv, 'data') and hv.data:
                result["values"] = [float(d.value) for d in hv.data]
            result["slope"] = bc["Flow Hydrograph Slope"].value if "Flow Hydrograph Slope" in bc else None

        # Stage Hydrograph
        elif "Stage Hydrograph" in bc:
            hv = bc["Stage Hydrograph"].value
            if hasattr(hv, 'data') and hv.data:
                result["values"] = [float(d.value) for d in hv.data]
            result["use_initial_stage"] = int(bc["Stage Hydrograph Use Initial Stage"].value) if "Stage Hydrograph Use Initial Stage" in bc else None

        # Stage and Flow Hydrograph（2 items per value: stage, flow）
        elif "Stage and Flow Hydrograph" in bc:
            hv = bc["Stage and Flow Hydrograph"].value
            if hasattr(hv, 'data') and hv.data:
                result["paired_values"] = [float(d.value) for d in hv.data]

        # Rating Curve（2 items per value: stage, flow）
        elif "Rating Curve" in bc:
            hv = bc["Rating Curve"].value
            if hasattr(hv, 'data') and hv.data:
                result["paired_values"] = [float(d.value) for d in hv.data]

        # Friction Slope（逗号分隔的两个值）
        elif "Friction Slope" in bc:
            fv = bc["Friction Slope"].value
            if fv and hasattr(fv, 'value'):
                result["values"] = [float(v.value) for v in fv.value]

        return result

    def find_bc_by_location(
        self,
        river: str = None, reach: str = None, station: str = None,
        storage_area: str = None, bc_line: str = None,
    ) -> BoundaryCondition | None:
        """根据位置信息查找BC块

        河流BC: 传入 river/reach/station（上游或下游由调用方保证语义正确）
        存储区/Perimeter BC: 传入 storage_area/bc_line
        """
        for bc in self.get_blocks_by_type(BoundaryCondition):
            loc = bc["Boundary Location"].value if "Boundary Location" in bc else []
            if not loc:
                continue

            def f(i): return loc[i].value if i < len(loc) and loc[i].value else None

            if river is not None and f(0) == river and f(1) == reach and f(2) == station:
                return bc
            if storage_area is not None and f(5) == storage_area and f(7) == bc_line:
                return bc

        return None

    def add_bc_block(self, bc: BoundaryCondition):
        self._blocks.append(bc)