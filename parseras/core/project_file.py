"""
ProjectFile 类 - 用于解析和生成 HEC-RAS 项目文件 (.prj)
"""

from typing import Dict, List, Optional


class ProjectFile:
    """HEC-RAS 项目文件解析器

    prj 文件是纯 key=value 格式，无需 block 分割。
    某些 key 可以有多个值（如 Geom File, Flow File, Plan File）。
    """

    def __init__(self, file_path: str | None = None, lines: List[str] | None = None):
        self._key_values: Dict[str, str] = {}  # {key: value}
        self._key_order: List[str] = []  # 保持 key 的原始顺序
        self._multi_keys: Dict[str, List[str]] = {
            'Geom File': [],
            'Flow File': [],
            'Plan File': [],
        }  # 支持多个值的 key

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

                if key in self._multi_keys:
                    self._multi_keys[key].append(value)
                    if key not in self._key_order:
                        self._key_order.append(key)
                else:
                    self._key_values[key] = value
                    if key not in self._key_order:
                        self._key_order.append(key)
            else:
                # 没有 = 号的行，可能是裸值（如 "English Units"）
                stripped = line.strip()
                if stripped and stripped not in self._key_values:
                    self._key_values[stripped] = ""
                    self._key_order.append(stripped)

    def get(self, key: str) -> Optional[str]:
        """获取字段值（单值 key）"""
        return self._key_values.get(key)

    def get_multi(self, key: str) -> List[str]:
        """获取字段值（多值 key，如 Geom File）"""
        return self._multi_keys.get(key, []).copy()

    def set(self, key: str, value: str):
        """设置字段值（单值 key）"""
        self._key_values[key] = value
        if key not in self._key_order:
            self._key_order.append(key)

    def add_geom_file(self, filename: str):
        """添加几何文件"""
        if 'Geom File' not in self._key_order:
            self._key_order.append('Geom File')
        self._multi_keys['Geom File'].append(filename)

    def add_flow_file(self, filename: str):
        """添加流量文件"""
        if 'Flow File' not in self._key_order:
            self._key_order.append('Flow File')
        self._multi_keys['Flow File'].append(filename)

    def add_plan_file(self, filename: str):
        """添加计划文件"""
        if 'Plan File' not in self._key_order:
            self._key_order.append('Plan File')
        self._multi_keys['Plan File'].append(filename)

    def keys(self) -> List[str]:
        """获取所有 key（按原始顺序）"""
        return self._key_order.copy()

    def items(self) -> Dict[str, str]:
        """获取所有单值键值对"""
        return self._key_values.copy()

    @property
    def project_title(self) -> Optional[str]:
        """获取项目标题"""
        return self.get("Proj Title")

    @property
    def current_plan(self) -> Optional[str]:
        """获取当前计划"""
        return self.get("Current Plan")

    @property
    def geom_files(self) -> List[str]:
        """获取所有几何文件"""
        return self.get_multi('Geom File')

    @property
    def flow_files(self) -> List[str]:
        """获取所有流量文件"""
        return self.get_multi('Flow File')

    @property
    def plan_files(self) -> List[str]:
        """获取所有计划文件"""
        return self.get_multi('Plan File')

    def generate(self) -> List[str]:
        """重新生成 prj 文件内容"""
        result = []

        for key in self._key_order:
            if key in self._multi_keys:
                # 多值 key
                for value in self._multi_keys[key]:
                    result.append(f"{key}={value}")
            elif key in self._key_values:
                # 单值 key
                value = self._key_values[key]
                if value:
                    result.append(f"{key}={value}")
                else:
                    result.append(key)

        return result
