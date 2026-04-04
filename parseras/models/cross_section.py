from typing import List, Dict, Tuple, Optional
import json
from parseras.core.file import GeometryFile
from parseras.core.structures import CrossSection


class CrossSectionModel:
    def __init__(self, geometry_file: GeometryFile):
        self.geometry_file = geometry_file
        self.cross_sections = geometry_file.get_blocks_by_type(CrossSection)

    def get_all_cross_section_lines(self) -> str:
        """返回所有断面的折线点数值，也就是XS GIS Cut Line对应的点

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": [[x1, y1], [x2, y2], ...],
                "station2": [[x1, y1], [x2, y2], ...],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R" in xs and "XS GIS Cut Line" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R"].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取折线点
                        cut_line = xs["XS GIS Cut Line"].value
                        points = []
                        data = cut_line.data
                        for i in range(0, len(data), 2):
                            if i + 1 < len(data):
                                x = data[i].value
                                y = data[i + 1].value
                                points.append([x, y])
                        result[station] = points
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_station_elev_table(self, station: float) -> str:
        """返回特定断面的Station/Elev表

        返回格式：
        {
            "status": "success",
            "data": {
                "stations": [station1, station2, ...],
                "elevations": [elevation1, elevation2, ...]
            },
            "message": ""
        }
        """
        try:
            for xs in self.cross_sections:
                if "Type RM Length L Ch R" in xs and "#Sta/Elev" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R"].value
                    if len(type_rm) >= 2:
                        xs_station = float(type_rm[1].value)
                        if xs_station == station:
                            # 提取Sta/Elev表
                            sta_elev = xs["#Sta/Elev"].value
                            stations = []
                            elevations = []
                            data = sta_elev.data
                            for i in range(0, len(data), 2):
                                if i + 1 < len(data):
                                    sta = data[i].value
                                    elev = data[i + 1].value
                                    stations.append(sta)
                                    elevations.append(elev)
                            # 转置格式，Station一个表，elevation一个表
                            result = {"stations": stations, "elevations": elevations}
                            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
            return json.dumps(
                {"status": "success", "data": {"stations": [], "elevations": []}, "message": ""}, indent=2
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "data": {"stations": [], "elevations": []}, "message": str(e)}, indent=2
            )

    def get_all_mann_values(self) -> str:
        """返回所有断面的曼宁值，也就是Mann

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": [[sta1, left1, right1], [sta2, left2, right2], ...],
                "station2": [[sta1, left1, right1], [sta2, left2, right2], ...],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R" in xs and "#Mann" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R"].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取曼宁值
                        mann = xs["#Mann"].value
                        values = []
                        data = mann.data
                        for i in range(0, len(data), 3):
                            if i + 2 < len(data):
                                sta = data[i].value
                                left = data[i + 1].value
                                right = data[i + 2].value
                                values.append([sta, left, right])
                        result[station] = values
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)

    def get_all_bank_stations(self) -> str:
        """返回所有断面的Bank Sta值

        返回格式：
        {
            "status": "success",
            "data": {
                "station1": [bank_sta1, bank_sta2],
                "station2": [bank_sta1, bank_sta2],
                ...
            },
            "message": ""
        }
        """
        try:
            result = {}
            for xs in self.cross_sections:
                if "Type RM Length L Ch R" in xs and "Bank Sta" in xs:
                    # 提取断面在河流上的Station
                    type_rm = xs["Type RM Length L Ch R"].value
                    if len(type_rm) >= 2:
                        station = float(type_rm[1].value)
                        # 提取Bank Sta值
                        bank_sta = xs["Bank Sta"].value
                        values = [float(item.value) for item in bank_sta if item.value]
                        # 确保只返回前两个值，分别对应左岸和右岸
                        if len(values) > 2:
                            values = values[:2]
                        # 如果不足两个值，用None填充
                        elif len(values) < 2:
                            values.extend([None] * (2 - len(values)))
                        result[station] = values
            return json.dumps({"status": "success", "data": result, "message": ""}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "data": {}, "message": str(e)}, indent=2)
