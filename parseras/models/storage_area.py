"""
StorageAreaModel 类 - 提供存储区的业务逻辑封装
"""

import json
from typing import List
from parseras.core.file import GeometryFile
from parseras.core.structures import StorageArea
from parseras.core.values import (
    CommaSeparatedValue,
    DataBlockValue,
    DataValue,
    FloatValue,
    IntValue,
    StringValue,
)


class StorageAreaModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.storage_areas = geometry_file.get_blocks_by_type(StorageArea)

    def _get_area_name(self, sa: StorageArea) -> str:
        if "Storage Area" in sa:
            storage_area_value = sa["Storage Area"].value
            if storage_area_value and len(storage_area_value) > 0:
                return storage_area_value[0].value
        return ""

    def _get_area_type(self, sa: StorageArea) -> str:
        if "Storage Area Is2D" in sa:
            is_2d = sa["Storage Area Is2D"].value
            if is_2d == 0:
                return "StorageArea"
            elif is_2d == -1:
                return "2D Flow Area"
        return "Unknown"

    def get_all_storage_areas(self) -> str:
        """返回所有存储区的摘要信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Storage Area 1": {
                    "type": "StorageArea",
                    "area": 1234.5
                },
                "Perimeter 1": {
                    "type": "2D Flow Area"
                }
            },
            "message": ""
        }
        """
        try:
            result = {}
            for sa in self.storage_areas:
                name = self._get_area_name(sa)
                if not name:
                    continue

                area_type = self._get_area_type(sa)
                area_info = {"type": area_type}

                if "Storage Area Surface Line" in sa:
                    surface_line = sa["Storage Area Surface Line"].value
                    if hasattr(surface_line, 'data') and len(surface_line.data) > 0:
                        point_count = len(surface_line.data) // 2
                        area_info["point_count"] = point_count

                result[name] = area_info

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_storage_area_info(self, name: str) -> str:
        """返回特定存储区的完整属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Storage Area Name": "Storage Area 1",
                "type": "StorageArea",
                "Is2D": 0,
                "Mannings": 0.06,
                "Surface Line": [[x1, y1], [x2, y2], ...],
                "Vol Elev": [[elev1, vol1], [elev2, vol2], ...],
                "Point Generation Data": ["", "", "100", "100"]
            },
            "message": ""
        }
        """
        try:
            target_sa = None
            for sa in self.storage_areas:
                if self._get_area_name(sa) == name:
                    target_sa = sa
                    break

            if not target_sa:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Storage area with name '{name}' not found"},
                    indent=2,
                )

            result = {}
            result["Storage Area Name"] = self._get_area_name(target_sa)
            result["type"] = self._get_area_type(target_sa)

            if "Storage Area Is2D" in target_sa:
                result["Is2D"] = target_sa["Storage Area Is2D"].value

            if "Storage Area Mannings" in target_sa:
                result["Mannings"] = target_sa["Storage Area Mannings"].value

            if "Storage Area Surface Line" in target_sa:
                surface_line = target_sa["Storage Area Surface Line"].value
                points = []
                if hasattr(surface_line, 'data'):
                    data = surface_line.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                result["Surface Line"] = points

            if "Storage Area Vol Elev" in target_sa:
                vol_elev = target_sa["Storage Area Vol Elev"].value
                pairs = []
                if hasattr(vol_elev, 'data'):
                    data = vol_elev.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            elev = data[i].value
                            vol = data[i + 1].value
                            pairs.append([elev, vol])
                result["Vol Elev"] = pairs

            if "Storage Area Point Generation Data" in target_sa:
                pg_data = target_sa["Storage Area Point Generation Data"].value
                if hasattr(pg_data, '__iter__'):
                    result["Point Generation Data"] = [item.value if hasattr(item, 'value') else item for item in pg_data]

            if "Storage Area 2D Points" in target_sa:
                points_2d = target_sa["Storage Area 2D Points"].value
                points = []
                if hasattr(points_2d, 'data'):
                    data = points_2d.data
                    for i in range(0, len(data), 2):
                        if i + 1 < len(data):
                            x = data[i].value
                            y = data[i + 1].value
                            points.append([x, y])
                result["2D Points"] = points

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_storage_area(self, input_json: str) -> str:
        """更新或创建存储区

        输入格式：
        {
            "Storage Area Name": "Storage Area 1",
            "Is2D": 0,
            "Mannings": 0.06,  // optional
            "Surface Line": [[x1, y1], [x2, y2], ...],
            "Vol Elev": [[elev1, vol1], ...],  // Is2D=0时必需
            "Point Generation Data": ["", "", "100", "100"]  // Is2D=-1时必需
        }

        create时严格检查必需属性：
        - Is2D=0: Name, Surface Line, Vol Elev
        - Is2D=-1: Name, Surface Line, Point Generation Data

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Storage area updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            name = input_data.get("Storage Area Name")

            if not name:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Storage Area Name is required"},
                    indent=2,
                )

            target_sa = None
            for sa in self.storage_areas:
                if self._get_area_name(sa) == name:
                    target_sa = sa
                    break

            if target_sa is None:
                is_2d = input_data.get("Is2D")
                surface_line = input_data.get("Surface Line")
                vol_elev = input_data.get("Vol Elev")
                pg_data = input_data.get("Point Generation Data")

                missing_fields = []
                if not surface_line:
                    missing_fields.append("Surface Line")
                if is_2d == 0:
                    if not vol_elev:
                        missing_fields.append("Vol Elev")
                elif is_2d == -1:
                    if not pg_data:
                        missing_fields.append("Point Generation Data")
                else:
                    missing_fields.append("Is2D (must be 0 or -1)")

                if missing_fields:
                    return json.dumps(
                        {"status": "error", "data": {}, "message": f"Missing required fields for creation: {', '.join(missing_fields)}"},
                        indent=2,
                    )

                target_sa = StorageArea([])
                self.storage_areas.append(target_sa)
                self.geometry_file._blocks.append(target_sa)
                message = "Storage area created successfully"
            else:
                surface_line = input_data.get("Surface Line")
                message = "Storage area updated successfully"

            storage_area_value = CommaSeparatedValue(f"{name},,", element_type=StringValue)
            target_sa["Storage Area"] = storage_area_value

            if "Is2D" in input_data:
                target_sa["Storage Area Is2D"] = IntValue(str(input_data["Is2D"]))

            if "Mannings" in input_data:
                target_sa["Storage Area Mannings"] = FloatValue(str(input_data["Mannings"]))

            if surface_line:
                sl_data = []
                for point in surface_line:
                    sl_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])
                count = len(surface_line)
                sl_block = DataBlockValue(value_width=16, values_per_line=2, items_per_value=2)
                sl_value = DataValue(tuple(sl_data), 16, 2, 2, (str(count),), count)
                sl_block.value = sl_value
                target_sa["Storage Area Surface Line"] = sl_block

            if "Vol Elev" in input_data:
                ve_data = []
                for pair in input_data["Vol Elev"]:
                    ve_data.extend([FloatValue(str(pair[0])), FloatValue(str(pair[1]))])
                count = len(input_data["Vol Elev"])
                ve_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                ve_value = DataValue(tuple(ve_data), 8, 10, 2, (str(count),), count)
                ve_block.value = ve_value
                target_sa["Storage Area Vol Elev"] = ve_block

            if "Point Generation Data" in input_data:
                pg_value = CommaSeparatedValue(
                    ",".join(str(x) for x in input_data["Point Generation Data"]),
                    element_type=StringValue
                )
                target_sa["Storage Area Point Generation Data"] = pg_value

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def delete_storage_area(self, name: str) -> str:
        """删除存储区

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Storage area deleted successfully"
        }
        """
        try:
            target_index = None
            for i, sa in enumerate(self.storage_areas):
                if self._get_area_name(sa) == name:
                    target_index = i
                    break

            if target_index is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Storage area with name '{name}' not found"},
                    indent=2,
                )

            self.storage_areas.pop(target_index)

            block_index = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, StorageArea) and self._get_area_name(block) == name:
                    block_index = i
                    break

            if block_index is not None:
                self.geometry_file._blocks.pop(block_index)

            return json.dumps({"status": "success", "data": {}, "message": "Storage area deleted successfully"}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)