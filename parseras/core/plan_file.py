"""
PlanFile 类 - 用于解析和生成 HEC-RAS 计划文件 (p01)
"""

from typing import Dict, List, Optional


class PlanFile:
    """HEC-RAS 计划文件解析器

    p01 文件是纯 key=value 格式，无需 block 分割。
    字段按顺序存储以保持原始格式。
    """

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._key_values: Dict[str, str] = {}  # {key: value}
        self._key_order: List[str] = []  # 保持 key 的原始顺序

        if file_path:
            with open(file_path, "r", encoding='utf-8') as f:
                lines = f.readlines()
            self._parse_lines(lines)
        elif lines is not None:
            self._parse_lines(lines)

    def _parse_lines(self, lines: List[str]):
        """解析文件内容"""
        for line in lines:
            line = line.rstrip('\n')
            if not line.strip():
                continue

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                self._key_values[key] = value
                if key not in self._key_order:
                    self._key_order.append(key)
            else:
                # 没有 = 号的行，可能是裸值（如 "Subcritical Flow"）
                stripped = line.strip()
                if stripped and stripped not in self._key_values:
                    # 裸值存储为空字符串 key
                    self._key_values[stripped] = ""
                    self._key_order.append(stripped)

    def generate(self) -> List[str]:
        """重新生成 plan 文件内容"""
        result = []
        for key in self._key_order:
            value = self._key_values.get(key, "")
            if value:
                result.append(f"{key}={value}")
            else:
                result.append(key)
        return result

    def get(self, key: str) -> Optional[str]:
        """获取字段值"""
        return self._key_values.get(key)

    def set(self, key: str, value: str):
        """设置字段值"""
        self._key_values[key] = value
        if key not in self._key_order:
            self._key_order.append(key)

    def keys(self) -> List[str]:
        """获取所有 key（按原始顺序）"""
        return self._key_order.copy()

    def items(self) -> Dict[str, str]:
        """获取所有键值对"""
        return self._key_values.copy()

    @property
    def geom_file(self) -> Optional[str]:
        """获取几何文件名"""
        return self.get("Geom File")

    @property
    def flow_file(self) -> Optional[str]:
        """获取流量文件名"""
        return self.get("Flow File")

    @property
    def plan_title(self) -> Optional[str]:
        """获取计划标题"""
        return self.get("Plan Title")

    @property
    def program_version(self) -> Optional[str]:
        """获取程序版本"""
        return self.get("Program Version")
