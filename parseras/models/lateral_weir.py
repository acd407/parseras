"""
LateralWeirModel 类 - 提供侧堰的业务逻辑封装
"""

import json
from typing import Optional
from parseras.core.file import GeometryFile
from parseras.core.structures import LateralWeir
from parseras.core.values import (
    CommaSeparatedValue,
    DataBlockValue,
    DataValue,
    FloatValue,
    StringValue,
)
from parseras.utils import generate_se_from_centerline


class LateralWeirModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.lateral_weirs = geometry_file.get_blocks_by_type(LateralWeir)

    def get_all_lateral_weir_centerlines(self) -> str:
        """返回所有侧堰的中心线点

        返回格式：
        {
            "status": "success",
            "data": {
                "node_name1": [[x1, y1], [x2, y2], ...],
                "node_name2": [[x1, y1], [x2, y2], ...],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for lw in self.lateral_weirs:
                if "Node Name" in lw and "Lateral Weir Centerline" in lw:
                    node_name = lw["Node Name"].value
                    centerline = lw["Lateral Weir Centerline"].value
                    points = []
                    data = centerline.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                    result[node_name] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_lateral_weir_info(self, node_name: str) -> str:
        """返回特定侧堰的所有属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Type RM Length L Ch R": ["6", "8926", "", "", ""],
                "Node Name": "bank",
                "Lateral Weir End": ["", "", "", "Perimeter 1"],
                "Lateral Weir Distance": 0.0,
                "Lateral Weir WD": 100.0,
                "Lateral Weir SE": [[0.0, 937.5], [24.5, 937.5], ...],
                "Lateral Weir Centerline": [[405847.800625798, 1802488.50152492], ...],
                // 其他可选属性
                "Node Last Edited Time": "...",
                "Lateral Weir Pos": 0,
                ...
            },
            "message": ""
        }
        """
        try:
            target_lw = None
            for lw in self.lateral_weirs:
                if "Node Name" in lw and lw["Node Name"].value == node_name:
                    target_lw = lw
                    break

            if not target_lw:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Lateral weir with node name '{node_name}' not found"},
                    indent=2,
                )

            # 提取所有属性
            result = {}

            # 必需键
            if "Type RM Length L Ch R " in target_lw:
                type_rm = target_lw["Type RM Length L Ch R "].value
                result["Type RM Length L Ch R"] = [item.value for item in type_rm]

            if "Node Name" in target_lw:
                result["Node Name"] = target_lw["Node Name"].value

            if "Lateral Weir End" in target_lw:
                lw_end = target_lw["Lateral Weir End"].value
                result["Lateral Weir End"] = [item.value for item in lw_end]

            if "Lateral Weir Distance" in target_lw:
                result["Lateral Weir Distance"] = target_lw["Lateral Weir Distance"].value

            if "Lateral Weir WD" in target_lw:
                result["Lateral Weir WD"] = target_lw["Lateral Weir WD"].value

            # SE表
            if "Lateral Weir SE" in target_lw:
                se = target_lw["Lateral Weir SE"].value
                se_data = []
                data = se.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        dist = data[i].value
                        elev = data[i + 1].value
                        se_data.append([dist, elev])
                result["Lateral Weir SE"] = se_data

            # 中心线
            if "Lateral Weir Centerline" in target_lw:
                centerline = target_lw["Lateral Weir Centerline"].value
                centerline_data = []
                data = centerline.data
                for i in range(0, len(data), 2):
                    if i + 1 < len(data):
                        x = data[i].value
                        y = data[i + 1].value
                        centerline_data.append([x, y])
                result["Lateral Weir Centerline"] = centerline_data

            # 可选键
            optional_keys = [
                "Node Last Edited Time",
                "Lateral Weir Pos",
                "Lateral Weir TW Multiple XS",
                "Lateral Weir Coef",
                "LW OverFlow Method 2D",
                "LW OverFlow Use Velocity Into 2D",
                "Lateral Weir WSCriteria",
                "Lateral Weir Flap Gates",
                "Lateral Weir Hagers EQN",
                "Lateral Weir SS",
                "Lateral Weir Type",
                "Lateral Weir Connection Pos and Dist",
                "LW Div RC",
            ]

            for key in optional_keys:
                if key in target_lw:
                    value = target_lw[key]
                    if isinstance(value.value, tuple):
                        result[key] = [item.value for item in value.value]
                    else:
                        result[key] = value.value

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_lateral_weir(self, input_json: str, tif_path: Optional[str] = None) -> str:
        """更新或创建侧堰

        输入格式：
        {
            "Node Name": "bank",           // 必需，用于定位
            "Station": 8926,               // 可选，用于Type RM
            "Lateral Weir End Parameter": "Perimeter 1",  // 可选，用于Lateral Weir End
            "Lateral Weir Distance": 0,    // 可选
            "Lateral Weir WD": 100,        // 可选
            "Lateral Weir Centerline": [[x1, y1], [x2, y2], ...]  // 可选
        }

        参数：
        - input_json: 包含侧堰信息的JSON字符串
        - tif_path: 可选，DEM数据文件路径，用于生成Lateral Weir SE

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Lateral weir updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            node_name = input_data.get("Node Name")

            if not node_name:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Missing required field 'Node Name'"},
                    indent=2,
                )

            station = input_data.get("Station")
            lw_end_param = input_data.get("Lateral Weir End Parameter")
            lw_distance = input_data.get("Lateral Weir Distance")
            lw_wd = input_data.get("Lateral Weir WD")
            lw_centerline = input_data.get("Lateral Weir Centerline")

            old_lw_index = None
            old_lw = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, LateralWeir) and "Node Name" in block:
                    if block["Node Name"].value == node_name:
                        old_lw_index = i
                        old_lw = block
                        break

            if old_lw_index is not None:
                del self.geometry_file._blocks[old_lw_index]
                self.lateral_weirs = self.geometry_file.get_blocks_by_type(LateralWeir)

            target_lw = LateralWeir([])
            self.lateral_weirs.append(target_lw)
            self.geometry_file._blocks.append(target_lw)

            if station is not None:
                type_rm_str = f"6,{station},,,"
                target_lw["Type RM Length L Ch R "] = CommaSeparatedValue(type_rm_str, element_type=StringValue)
                if station > 0:
                    target_lw.order = 30 + 1 / station

            if node_name is not None:
                target_lw["Node Name"] = StringValue(node_name)

            if lw_end_param is not None:
                lw_end_str = f",,,{lw_end_param}"
                target_lw["Lateral Weir End"] = CommaSeparatedValue(lw_end_str, element_type=StringValue)

            if lw_distance is not None:
                target_lw["Lateral Weir Distance"] = FloatValue(str(lw_distance))

            if lw_wd is not None:
                target_lw["Lateral Weir WD"] = FloatValue(str(lw_wd))

            if lw_centerline:
                centerline_data = []
                for point in lw_centerline:
                    centerline_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])

                count = len(lw_centerline)
                centerline_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
                centerline_value = DataValue(tuple(centerline_data), 16, 4, 2, (str(count),), count)
                centerline_block.value = centerline_value
                target_lw["Lateral Weir Centerline"] = centerline_block

                se_table = generate_se_from_centerline(lw_centerline, tif_path)
                se_data = []
                for dist, elev in se_table:
                    se_data.extend([FloatValue(str(dist)), FloatValue(str(elev))])

                count = len(se_table)
                se_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                se_value = DataValue(tuple(se_data), 8, 10, 2, (str(count),), count)
                se_block.value = se_value
                target_lw["Lateral Weir SE"] = se_block

            message = "Lateral weir created successfully" if old_lw is None else "Lateral weir updated successfully"
            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)

        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)
