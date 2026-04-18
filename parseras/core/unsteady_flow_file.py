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