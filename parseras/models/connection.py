"""
ConnectionModel 类 - 提供连接线的业务逻辑封装
"""

import json
from typing import List, Tuple
from parseras.core.file import GeometryFile
from parseras.core.structures import Connection
from parseras.core.values import (
    CommaSeparatedValue,
    DataBlockValue,
    DataValue,
    FloatValue,
    IntValue,
    StringValue,
)


class ConnectionModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.connections = geometry_file.get_blocks_by_type(Connection)

    def _get_connection_name(self, conn: Connection) -> str:
        if "Connection" in conn:
            conn_value = conn["Connection"].value
            if conn_value and len(conn_value) > 0:
                return conn_value[0].value
        return ""

    def _parse_conn_weir_se(self, conn: Connection) -> List[Tuple[float, float]]:
        if "Conn Weir SE" not in conn:
            return []
        se_value = conn["Conn Weir SE"].value
        result = []
        if hasattr(se_value, 'data'):
            data = se_value.data
            for i in range(0, len(data), 2):
                if i + 1 < len(data):
                    station = data[i].value
                    elev = data[i + 1].value
                    result.append((station, elev))
        return result

    def _parse_connection_line(self, conn: Connection) -> List[Tuple[float, float]]:
        if "Connection Line" not in conn:
            return []
        line_value = conn["Connection Line"].value
        result = []
        if hasattr(line_value, 'data'):
            data = line_value.data
            for i in range(0, len(data), 2):
                if i + 1 < len(data):
                    x = data[i].value
                    y = data[i + 1].value
                    result.append((x, y))
        return result

    def get_all_connections(self) -> str:
        """返回所有连接的摘要信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Connection1": {
                    "up_sa": "Storage Area 1",
                    "dn_sa": "Storage Area 2",
                    "weir_width": 200
                }
            },
            "message": ""
        }
        """
        try:
            result = {}
            for conn in self.connections:
                name = self._get_connection_name(conn)
                if not name:
                    continue

                conn_info = {}
                if "Connection Up SA" in conn:
                    conn_info["up_sa"] = conn["Connection Up SA"].value
                if "Connection Dn SA" in conn:
                    conn_info["dn_sa"] = conn["Connection Dn SA"].value
                if "Conn Weir WD" in conn:
                    conn_info["weir_width"] = conn["Conn Weir WD"].value

                result[name] = conn_info

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_connection_info(self, name: str) -> str:
        """返回特定连接的完整属性信息

        返回格式：
        {
            "status": "success",
            "data": {
                "Connection Name": "Connection1",
                "Parameters": ["Storage Area 1 T", "0", "0"],
                "Connection Line": [[x1, y1], [x2, y2], ...],
                "Connection Up SA": "Storage Area 1",
                "Connection Dn SA": "Storage Area 2",
                "Conn Weir WD": 200,
                "Conn Weir SE": [[station1, elev1], [station2, elev2], ...]
            },
            "message": ""
        }
        """
        try:
            target_conn = None
            for conn in self.connections:
                if self._get_connection_name(conn) == name:
                    target_conn = conn
                    break

            if not target_conn:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Connection with name '{name}' not found"},
                    indent=2,
                )

            result = {}
            result["Connection Name"] = self._get_connection_name(target_conn)

            if "Connection" in target_conn:
                params = target_conn["Connection"].value
                result["Parameters"] = [p.value if hasattr(p, 'value') else p for p in params]

            if "Connection Line" in target_conn:
                line_points = self._parse_connection_line(target_conn)
                result["Connection Line"] = [[p[0], p[1]] for p in line_points]

            if "Connection Up SA" in target_conn:
                result["Connection Up SA"] = target_conn["Connection Up SA"].value

            if "Connection Dn SA" in target_conn:
                result["Connection Dn SA"] = target_conn["Connection Dn SA"].value

            if "Conn Weir WD" in target_conn:
                result["Conn Weir WD"] = target_conn["Conn Weir WD"].value

            if "Conn Weir SE" in target_conn:
                se_data = self._parse_conn_weir_se(target_conn)
                result["Conn Weir SE"] = [[s, e] for s, e in se_data]

            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def update_or_create_connection(self, input_json: str, tif_path: str | None = None) -> str:
        """更新或创建连接

        输入格式：
        {
            "Connection Name": "Connection1",
            "Parameters": ["Storage Area 1 T", "0", "0"],  // optional
            "Connection Line": [[x1, y1], [x2, y2], ...],
            "Connection Up SA": "Storage Area 1",
            "Connection Dn SA": "Storage Area 2",
            "Conn Weir WD": 200
        }

        create时必需：Connection Line, Connection Up SA, Connection Dn SA, Conn Weir WD

        注意：Conn Weir SE 通过 tif_path 自动更新，不通过输入设置

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Connection updated/created successfully"
        }
        """
        try:
            input_data = json.loads(input_json)
            name = input_data.get("Connection Name")

            if not name:
                return json.dumps(
                    {"status": "error", "data": {}, "message": "Connection Name is required"},
                    indent=2,
                )

            target_conn = None
            for conn in self.connections:
                if self._get_connection_name(conn) == name:
                    target_conn = conn
                    break

            if target_conn is None:
                conn_line = input_data.get("Connection Line")
                up_sa = input_data.get("Connection Up SA")
                dn_sa = input_data.get("Connection Dn SA")
                weir_wd = input_data.get("Conn Weir WD")

                missing_fields = []
                if not conn_line:
                    missing_fields.append("Connection Line")
                if not up_sa:
                    missing_fields.append("Connection Up SA")
                if not dn_sa:
                    missing_fields.append("Connection Dn SA")
                if weir_wd is None:
                    missing_fields.append("Conn Weir WD")

                if missing_fields:
                    return json.dumps(
                        {"status": "error", "data": {}, "message": f"Missing required fields for creation: {', '.join(missing_fields)}"},
                        indent=2,
                    )

                target_conn = Connection([])
                self.connections.append(target_conn)
                self.geometry_file._blocks.append(target_conn)
                message = "Connection created successfully"
            else:
                conn_line = input_data.get("Connection Line")
                message = "Connection updated successfully"

            if "Parameters" in input_data:
                params = input_data["Parameters"]
                params_str = ",".join(str(p) for p in params)
                target_conn["Connection"] = CommaSeparatedValue(params_str, element_type=StringValue)

            if conn_line:
                cl_data = []
                for point in conn_line:
                    cl_data.extend([FloatValue(str(point[0])), FloatValue(str(point[1]))])
                count = len(conn_line)
                cl_block = DataBlockValue(value_width=16, values_per_line=4, items_per_value=2)
                cl_value = DataValue(tuple(cl_data), 16, 4, 2, (str(count),), count)
                cl_block.value = cl_value
                target_conn["Connection Line"] = cl_block

            if "Connection Up SA" in input_data:
                target_conn["Connection Up SA"] = StringValue(input_data["Connection Up SA"])

            if "Connection Dn SA" in input_data:
                target_conn["Connection Dn SA"] = StringValue(input_data["Connection Dn SA"])

            if "Conn Weir WD" in input_data:
                target_conn["Conn Weir WD"] = IntValue(str(input_data["Conn Weir WD"]))

            if tif_path and conn_line:
                from parseras.utils.gis import calculate_total_length, get_point_at_distance, get_elevation_from_tif
                points = [(p[0], p[1]) for p in conn_line]
                total_length = calculate_total_length(points)
                num_points = 101
                stations = []
                sample_points = []

                for i in range(num_points):
                    current_distance = (i / (num_points - 1)) * total_length
                    point = get_point_at_distance(points, current_distance)
                    stations.append(current_distance)
                    sample_points.append(point)

                xs = [p[0] for p in sample_points]
                ys = [p[1] for p in sample_points]
                elevations = get_elevation_from_tif(xs, ys, tif_path)

                se_data = []
                for s, e in zip(stations, elevations):
                    se_data.extend([FloatValue(str(s)), FloatValue(str(e))])

                count = len(stations)
                se_block = DataBlockValue(value_width=8, values_per_line=10, items_per_value=2)
                se_value = DataValue(tuple(se_data), 8, 10, 2, (str(count),), count)
                se_block.value = se_value
                target_conn["Conn Weir SE"] = se_block

            return json.dumps({"status": "success", "data": {}, "message": message}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def delete_connection(self, name: str) -> str:
        """删除连接

        返回格式：
        {
            "status": "success",
            "data": {},
            "message": "Connection deleted successfully"
        }
        """
        try:
            target_index = None
            for i, conn in enumerate(self.connections):
                if self._get_connection_name(conn) == name:
                    target_index = i
                    break

            if target_index is None:
                return json.dumps(
                    {"status": "error", "data": {}, "message": f"Connection with name '{name}' not found"},
                    indent=2,
                )

            self.connections.pop(target_index)

            block_index = None
            for i, block in enumerate(self.geometry_file._blocks):
                if isinstance(block, Connection) and self._get_connection_name(block) == name:
                    block_index = i
                    break

            if block_index is not None:
                self.geometry_file._blocks.pop(block_index)

            return json.dumps({"status": "success", "data": {}, "message": "Connection deleted successfully"}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)