from typing import List, Type

from parseras.core.structures import RASStructure, Head, River, BreakLine, StorageArea, Foot, LateralWeir, CrossSection


class GeometryFile:
    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):

        self._blocks: List[RASStructure] = []

        if file_path:
            with open(file_path, "r") as f:
                lines = f.readlines()
            self._parse_lines(lines)
        elif lines is not None:
            self._parse_lines(lines)


    def _split_into_blocks(self, lines: List[str]) -> List[List[str]]:
        blocks = []
        current_block = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_block:
                    blocks.append(current_block)
                    current_block = []
            else:
                current_block.append(line)

        if current_block:
            blocks.append(current_block)

        return blocks

    def _determine_block_type(self, block: List[str]) -> Type[RASStructure]:
        if not block:
            raise ValueError("Empty block")

        first_line = block[0].strip()
        if "=" not in first_line:
            raise ValueError(f"Invalid block line: {first_line}")

        key = first_line.split("=", 1)[0].strip()

        block_type_map = {
            "Geom Title": Head,
            "River Reach": River,
            "BreakLine Name": BreakLine,
            "Storage Area": StorageArea,
            "Use User Specified Reach Order": Foot,
            "Geom Raster": Foot,
            "GIS Ratio Cuts To Invert": Foot,
        }

        if key in block_type_map:
            return block_type_map[key]

        if key == "Type RM Length L Ch R":
            for line in block[1:]:
                line = line.strip()
                if line.startswith("Node Name") or line.startswith("Lateral Weir"):
                    return LateralWeir
                elif line.startswith("XS GIS Cut Line"):
                    return CrossSection

        raise ValueError(f"Unknown block type for key: {key}")

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
                result.append("\n")
        return result

    def get_blocks(self) -> List[RASStructure]:
        return self._blocks

    def get_blocks_by_type(self, block_type: Type[RASStructure]) -> List[RASStructure]:
        return [block for block in self._blocks if isinstance(block, block_type)]

