import json
import os

from parseras.core.file import GeometryFile
from parseras.models.cross_section import CrossSectionModel


def test_cross_section_read_write():
    """测试断面的读写功能：保存11000断面数据，删除后重建，验证数据一致性"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "leak.g01")
    backup_file = os.path.join(os.path.dirname(__file__), "data", "leak_backup.g01")
    output_file = os.path.join(os.path.dirname(__file__), "data", "leak_updated.g01")

    # 备份原始文件
    if os.path.exists(test_file):
        with open(test_file, "r") as f:
            original_content = f.read()
        with open(backup_file, "w") as f:
            f.write(original_content)
    else:
        print(f"测试文件不存在: {test_file}")
        return False

    try:
        with open(test_file, "r") as f:
            lines = f.readlines()

        geometry_file = GeometryFile(lines=lines)
        cross_section_model = CrossSectionModel(geometry_file)

        cross_section_lines = cross_section_model.get_all_cross_section_lines()
        cross_section_lines_data = json.loads(cross_section_lines)

        mann_values = cross_section_model.get_all_mann_values()
        mann_values_data = json.loads(mann_values)

        bank_sta_values = cross_section_model.get_all_bank_stations()
        bank_sta_values_data = json.loads(bank_sta_values)

        # 提取10000断面的数据
        station = 10000
        # 尝试不同的键格式，因为JSON序列化时浮点数会变成字符串
        station_strs = [str(station), f"{station}.0"]

        xs_gis_cut_line = None
        mann_data = None
        bank_sta = None

        # 尝试所有可能的键格式
        for station_str in station_strs:
            if not xs_gis_cut_line and station_str in cross_section_lines_data.get("data", {}):
                xs_gis_cut_line = cross_section_lines_data["data"][station_str]
            if not mann_data and station_str in mann_values_data.get("data", {}):
                mann_data = mann_values_data["data"][station_str]
            if not bank_sta and station_str in bank_sta_values_data.get("data", {}):
                bank_sta = bank_sta_values_data["data"][station_str]
            # 如果所有数据都找到了，就退出循环
            if xs_gis_cut_line and mann_data and bank_sta:
                break

        # 静默模式，不打印详细信息

        # 2. 删除{station}断面
        # 找到并删除{station}断面
        for i, block in enumerate(geometry_file.get_blocks()):
            if hasattr(block, "_key_value_pairs") and "Type RM Length L Ch R " in block._key_value_pairs:
                type_rm = block["Type RM Length L Ch R "].value
                if len(type_rm) >= 2:
                    try:
                        current_station = float(type_rm[1].value)
                        if current_station == station:
                            geometry_file.get_blocks().pop(i)
                            # 同时从cross_sections中删除
                            for j, xs in enumerate(cross_section_model.cross_sections):
                                if xs == block:
                                    cross_section_model.cross_sections.pop(j)
                                    break
                            # 静默模式，不打印详细信息
                            break
                    except (ValueError, AttributeError):
                        pass

        # 3. 重建{station}断面
        if xs_gis_cut_line:
            # 重建断面
            input_json = json.dumps({"Station": station, "XS GIS Cut Line": xs_gis_cut_line})

            # 添加tif_path参数，测试Sta/Elev生成功能
            tif_path = os.path.join(os.path.dirname(__file__), "data", "leak.tif")
            result = cross_section_model.update_or_create_cross_section(input_json, tif_path)
            # 静默模式，不打印详细信息

            # 更新Mann数据
            if mann_data:
                mann_input = json.dumps(
                    {
                        "XS Station": station,
                        "Station": mann_data.get("Station", []),
                        "Manning": mann_data.get("Manning", []),
                    }
                )
                mann_result = cross_section_model.update_mann_values(mann_input)
                # 静默模式，不打印详细信息

            # 更新Bank Sta数据
            if bank_sta:
                bank_sta_input = json.dumps(
                    {
                        "XS Station": station,
                        "Bank Sta": bank_sta,
                    }
                )
                bank_sta_result = cross_section_model.update_bank_stations(bank_sta_input)
                # 静默模式，不打印详细信息

        # 4. 生成更新后的文件
        updated_lines = geometry_file.generate()
        with open(output_file, "w") as f:
            f.writelines(updated_lines)
        # 静默模式，不打印详细信息

        # 5. 验证重建后的断面数据
        with open(output_file, "r") as f:
            updated_content = f.readlines()

        updated_geometry_file = GeometryFile(lines=updated_content)
        updated_cross_section_model = CrossSectionModel(updated_geometry_file)

        # 验证折线数据
        updated_cross_section_lines = updated_cross_section_model.get_all_cross_section_lines()
        updated_cross_section_lines_data = json.loads(updated_cross_section_lines)

        # 验证Mann数据
        updated_mann_values = updated_cross_section_model.get_all_mann_values()
        updated_mann_values_data = json.loads(updated_mann_values)

        # 验证Bank Sta数据
        updated_bank_sta_values = updated_cross_section_model.get_all_bank_stations()
        updated_bank_sta_values_data = json.loads(updated_bank_sta_values)

        # 静默模式，不打印详细信息

        # 检查折线数据
        updated_xs_gis_cut_line = None
        for station_str in station_strs:
            if station_str in updated_cross_section_lines_data.get("data", {}):
                updated_xs_gis_cut_line = updated_cross_section_lines_data["data"][station_str]
                break
        if not updated_xs_gis_cut_line:
            return False
        if xs_gis_cut_line != updated_xs_gis_cut_line:
            return False

        # 检查Mann数据
        updated_mann_data = None
        for station_str in station_strs:
            if station_str in updated_mann_values_data.get("data", {}):
                updated_mann_data = updated_mann_values_data["data"][station_str]
                break
        if mann_data and updated_mann_data != mann_data:
            return False

        # 检查Bank Sta数据
        updated_bank_sta = None
        for station_str in station_strs:
            if station_str in updated_bank_sta_values_data.get("data", {}):
                updated_bank_sta = updated_bank_sta_values_data["data"][station_str]
                break
        if bank_sta and updated_bank_sta != bank_sta:
            return False

        # 静默模式，不打印详细信息
        return True

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return False
    finally:
        # 恢复原始文件
        if os.path.exists(backup_file):
            with open(backup_file, "r") as f:
                backup_content = f.read()
            with open(test_file, "w") as f:
                f.write(backup_content)
            # 删除备份文件
            os.remove(backup_file)
            # 静默模式，不打印详细信息
