"""
FlowFile 类 - 用于解析和生成 HEC-RAS 流量结果文件 (f01/f02)
"""

from typing import List, Type

from parseras.core.structures import RASStructure
from parseras.core.flow_structures import (
    FlowHead,
    FlowProfile,
    ObservedWS,
    DSSImport,
)


class FlowFile:
    """HEC-RAS 流量结果文件解析器

    支持解析 f01, f02 等流量文件格式。
    Flow 文件没有空行分隔，block 类型由 key 决定。
    """

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._blocks: List[RASStructure] = []

        if file_path:
            with open(file_path, "r", encoding='utf-8') as f:
                lines = f.readlines()
            self._parse_lines(lines)
        elif lines is not None:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        """解析文件内容到各个 block

        Flow 文件按 key 类型分割 block：
        - FlowHead: 从 Flow Title 到 River Rch & RM
        - FlowProfile: 每个 Boundary for River Rch & Prof# 及其后面的 Up Type/Dn Type/Dn Known WS
        - ObservedWS: 每行一个 Observed WS
        - DSSImport: 从 DSS Import StartDate 到 DSS Import FillOption
        """
        current_block = []
        current_type = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            line = stripped

            # 判断这行属于哪个 block 类型
            if line.startswith("Flow Title"):
                block_type = "FlowHead"
            elif line.startswith("Program Version"):
                block_type = "FlowHead"
            elif line.startswith("Number of Profiles"):
                block_type = "FlowHead"
            elif line.startswith("Profile Names"):
                block_type = "FlowHead"
            elif line.startswith("River Rch & RM"):
                block_type = "FlowHead"
            elif line.startswith("Boundary for River Rch & Prof#"):
                # 每个新的 Profile 都会以 Boundary for River Rch & Prof# 开始
                # 如果当前有 FlowProfile block，先保存
                if current_type == "FlowProfile" and current_block:
                    self._create_block(current_type, current_block)
                    current_block = []
                block_type = "FlowProfile"
            elif line.startswith("Up Type"):
                block_type = "FlowProfile"
            elif line.startswith("Dn Type"):
                block_type = "FlowProfile"
            elif line.startswith("Dn Known WS"):
                block_type = "FlowProfile"
            elif line.startswith("Observed WS"):
                block_type = "ObservedWS"
            elif line.startswith("DSS Import"):
                block_type = "DSSImport"
            else:
                # 未知类型，跳过
                continue

            # 如果 block 类型变了，保存当前的 block 并开始新的
            if current_type is not None and block_type != current_type:
                if current_block:
                    self._create_block(current_type, current_block)
                    current_block = []

            current_type = block_type
            current_block.append(line)

        # 保存最后一个 block
        if current_block and current_type is not None:
            self._create_block(current_type, current_block)

    def _create_block(self, block_type: str, lines: List[str]):
        """根据 block 类型创建对应的结构实例"""
        if block_type == "FlowHead":
            block = FlowHead(lines)
        elif block_type == "FlowProfile":
            block = FlowProfile(lines)
        elif block_type == "ObservedWS":
            # ObservedWS 每行一个 block
            for line in lines:
                block = ObservedWS([line])
                self._blocks.append(block)
            return
        elif block_type == "DSSImport":
            block = DSSImport(lines)
        else:
            return

        self._blocks.append(block)

    def generate(self) -> List[str]:
        """重新生成 flow 文件内容"""
        result = []
        sorted_blocks = sorted(self._blocks, key=lambda block: getattr(block, "order", 100.0))

        for i, block in enumerate(sorted_blocks):
            block_lines = block.generate()
            result.extend(block_lines)
            if i < len(sorted_blocks) - 1:
                result.append("")

        return result

    def get_blocks(self) -> List[RASStructure]:
        """获取所有解析的 block"""
        return self._blocks

    def get_blocks_by_type(self, block_type: Type[RASStructure]) -> List[RASStructure]:
        """获取指定类型的所有 block"""
        return [block for block in self._blocks if isinstance(block, block_type)]
