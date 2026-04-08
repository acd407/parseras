"""
LateralWeirModel 类 - 提供侧堰的业务逻辑封装
"""

import json
from typing import List, Optional, Dict, Any
from parseras.core.file import GeometryFile
from parseras.core.structures import LateralWeir
from parseras.core.values import (
    CommaSeparatedValue,
    DataBlockValue,
    DataValue,
    FloatValue,
    StringValue,
    IntValue,
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
            "Node Name": "bank",
            "Station": 8926,                       // 用于Type RM的第二个值
            "Lateral Weir End Parameter": "Perimeter 1",  // 用于Lateral Weir End的第四个值
            "Lateral Weir Distance": 0,
            "Lateral Weir WD": 100,
            "Lateral Weir Centerline": [[x1, y1], [x2, y2], ...]
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
            # 解析输入JSON
            input_data = json.loads(input_json)
            node_name = input_data.get("Node Name")
            station = input_data.get("Station")
            lw_end_param = input_data.get("Lateral Weir End Parameter")
            lw_distance = input_data.get("Lateral Weir Distance")
            lw_wd = input_data.get("Lateral Weir WD")
            lw_centerline = input_data.get("Lateral Weir Centerline", [])

            # 验证必需参数
            required_fields = {
                "Node Name": node_name,
                "Station": station,
                "Lateral Weir End Parameter": lw_end_param,
                "Lateral Weir Distance": lw_distance,
                "Lateral Weir WD": lw_wd,
                "Lateral Weir Centerline": lw_centerline,
            }

            missing_fields = [field for field, value in required_fields.items() if value is None]
            if missing_fields:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Missing required fields: {missing_fields}"},
                    indent=2,
                )

            if not lw_centerline:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Lateral Weir Centerline cannot be empty"}, indent=2
                )

            # 查找现有的侧堰
            target_lw = None
            for lw in self.lateral_weirs:
                if "Node Name" in lw and lw["Node Name"].value == node_name:
                    target_lw = lw
                    break

            # 判断是创建还是更新
            is_create = False
            if target_lw is None:
                # 创建新的侧堰
                target_lw = LateralWeir([])
                self.lateral_weirs.append(target_lw)
                self.geometry_file._blocks.append(target_lw)
                is_create = True
                message = "Lateral weir created successfully"
            else:
                # 检查是否更新了Station（意味着创建新的而不是更新）
                if "Type RM Length L Ch R " in target_lw:
                    type_rm = target_lw["Type RM Length L Ch R "].value
                    if len(type_rm) >= 2:
                        existing_station = float(type_rm[1].value)
                        if existing_station != station:
                            # Station改变，视为创建新的
                            # 删除旧的，创建新的
                            self.lateral_weirs.remove(target_lw)
                            self.geometry_file._blocks.remove(target_lw)
                            target_lw = LateralWeir([])
                            self.lateral_weirs.append(target_lw)
                            self.geometry_file._blocks.append(target_lw)
                            is_create = True
                            message = "Lateral weir created successfully (station changed)"
                        else:
                            message = "Lateral weir updated successfully"
                else:
                    message = "Lateral weir updated successfully"

            # 如果是创建，需要设置所有必需键
            # 如果是更新，只更新提供的键

            # 1. 更新Type RM Length L Ch R
            if is_create or "Type RM Length L Ch R " not in target_lw or input_data.get("Station") is not None:
                # 第一个值固定为6，第二个值是station，后面三个值暂时留空
                type_rm_str = f"6,{station},,,"
                type_rm_value = CommaSeparatedValue(type_rm_str, element_type=StringValue)
                target_lw["Type RM Length L Ch R "] = type_rm_value

            # 2. 更新Node Name
            if is_create or "Node Name" not in target_lw or input_data.get("Node Name") is not None:
                target_lw["Node Name"] = StringValue(node_name)

            # 3. 更新Lateral Weir End
            if is_create or "Lateral Weir End" not in target_lw or input_data.get("Lateral Weir End Parameter") is not None:
                lw_end_str = f",,,{lw_end_param}"
                lw_end_value = CommaSeparatedValue(lw_end_str, element_type=StringValue)
                target_lw["Lateral Weir End"] = lw_end_value

            # 4. 更新Lateral Weir Distance
            if is_create or "Lateral Weir Distance" not in target_lw or input_data.get("Lateral Weir Distance") is not None:
                target_lw["Lateral Weir Distance"] = FloatValue(str(lw_distance))

            # 5. 更新Lateral Weir WD
            if is_create or "Lateral Weir WD" not in target_lw or input_data.get("Lateral Weir WD") is not None:
                target_lw["Lateral Weir WD"] = FloatValue(str(lw_wd))

            # 6. 更新Lateral Weir Centerline
            if is_create or "Lateral Weir Centerline" not in target_lw or input_data.get("Lateral Weir Centerline") is not None:
                centerline_data = []
                for point in lw_centerline:
                    centerline_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])

                count = len(lw_centerline)
                centerline_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
                centerline_value = DataValue(tuple(centerline_data), 16, 4, 2, (str(count),), count)
                centerline_block.value = centerline_value
                target_lw["Lateral Weir Centerline"] = centerline_block

                # 如果更新了Centerline，需要重新生成SE表
                if tif_path or (is_create and tif_path is None):
                    # 生成SE表
                    se_table = generate_se_from_centerline(lw_centerline, tif_path)

                    se_data = []
                    for dist, elev in se_table:
                        se_data.extend([FloatValue(str(dist)), FloatValue(str(elev))])

                    count = len(se_table)
                    se_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                    se_value = DataValue(tuple(se_data), 8, 10, 2, (str(count),), count)
                    se_block.value = se_value
                    target_lw["Lateral Weir SE"] = se_block
                elif is_create and tif_path is None:
                    # 创建时没有tif，生成全0高程的SE表
                    se_table = generate_se_from_centerline(lw_centerline, None)

                    se_data = []
                    for dist, elev in se_table:
                        se_data.extend([FloatValue(str(dist)), FloatValue(str(elev))])

                    count = len(se_table)
                    se_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                    se_value = DataValue(tuple(se_data), 8, 10, 2, (str(count),), count)
                    se_block.value = se_value
                    target_lw["Lateral Weir SE"] = se_block

            # 7. 更新order属性（基于station）
            try:
                if station > 0:
                    target_lw.order = 30 + 1 / station
            except (ValueError, AttributeError):
                pass

            # 8. 设置可选键的默认值（如果是创建）
            if is_create:
                # 设置一些合理的默认值
                target_lw["Node Last Edited Time"] = StringValue("")
                target_lw["Lateral Weir Pos"] = IntValue("0")
                target_lw["Lateral Weir TW Multiple XS"] = IntValue("0")
                target_lw["Lateral Weir Coef"] = FloatValue("0")
                target_lw["LW OverFlow Method 2D"] = IntValue("0")
                target_lw["LW OverFlow Use Velocity Into 2D"] = IntValue("0")
                target_lw["Lateral Weir WSCriteria"] = IntValue("0")
                target_lw["Lateral Weir Flap Gates"] = IntValue("0")
                target_lw["Lateral Weir Hagers EQN"] = CommaSeparatedValue("", element_type=StringValue)
                target_lw["Lateral Weir SS"] = CommaSeparatedValue("", element_type=StringValue)
                target_lw["Lateral Weir Type"] = IntValue("0")
                target_lw["Lateral Weir Connection Pos and Dist"] = CommaSeparatedValue("", element_type=StringValue)
                target_lw["LW Div RC"] = CommaSeparatedValue("", element_type=StringValue)

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)

        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)