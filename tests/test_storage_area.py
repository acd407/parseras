import json
import os

from parseras import GeometryFile, StorageAreaModel


def test_storage_area_read_write():
    """测试StorageArea的读写功能"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "storage_area.g01")
    output_file = os.path.join(os.path.dirname(__file__), "data", "storage_area.model.output.g01")

    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    geometry_file = GeometryFile(file_path=test_file)
    storage_model = StorageAreaModel(geometry_file)

    all_areas = storage_model.get_all_storage_areas()
    all_areas_data = json.loads(all_areas)

    if all_areas_data.get("status") != "success":
        print(f"获取存储区列表失败")
        return False

    area_name = "Perimeter 1"
    area_info = storage_model.get_storage_area_info(area_name)
    area_info_data = json.loads(area_info)

    if area_info_data.get("status") != "success":
        print(f"获取存储区信息失败")
        return False

    generated_lines = geometry_file.generate()
    with open(output_file, "w") as f:
        f.writelines(generated_lines)

    with open(output_file, "r") as f:
        updated_content = f.readlines()

    updated_geometry_file = GeometryFile(lines=updated_content)
    updated_storage_model = StorageAreaModel(updated_geometry_file)

    updated_all_areas = updated_storage_model.get_all_storage_areas()
    updated_all_areas_data = json.loads(updated_all_areas)

    if all_areas_data["data"] != updated_all_areas_data["data"]:
        print("存储区列表不匹配")
        return False

    updated_area_info = updated_storage_model.get_storage_area_info(area_name)
    updated_area_info_data = json.loads(updated_area_info)

    if area_info_data["data"] != updated_area_info_data["data"]:
        print("存储区信息不匹配")
        return False

    return True


def test_storage_area_create_validation():
    """测试StorageArea创建时的验证"""
    geometry_file = GeometryFile()
    storage_model = StorageAreaModel(geometry_file)

    input_missing_surface_line = json.dumps({
        "Storage Area Name": "Test Area",
        "Is2D": 0,
        "Vol Elev": [[100, 1000], [110, 2000]]
    })
    result = json.loads(storage_model.update_or_create_storage_area(input_missing_surface_line))
    if result["status"] != "error" or "Surface Line" not in result["message"]:
        print("应该检测到缺少Surface Line")
        return False

    input_missing_vol_elev = json.dumps({
        "Storage Area Name": "Test Area",
        "Is2D": 0,
        "Surface Line": [[0, 0], [100, 100]]
    })
    result = json.loads(storage_model.update_or_create_storage_area(input_missing_vol_elev))
    if result["status"] != "error" or "Vol Elev" not in result["message"]:
        print("应该检测到缺少Vol Elev")
        return False

    input_missing_pg_data = json.dumps({
        "Storage Area Name": "Test Area 2D",
        "Is2D": -1,
        "Surface Line": [[0, 0], [100, 100]]
    })
    result = json.loads(storage_model.update_or_create_storage_area(input_missing_pg_data))
    if result["status"] != "error" or "Point Generation Data" not in result["message"]:
        print("应该检测到缺少Point Generation Data")
        return False

    return True


def test_storage_area_update():
    """测试StorageArea的更新"""
    test_file = os.path.join(os.path.dirname(__file__), "data", "storage_area1.g01")
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False

    geometry_file = GeometryFile(file_path=test_file)
    storage_model = StorageAreaModel(geometry_file)

    original_info = storage_model.get_storage_area_info("Storage Area 1")
    original_data = json.loads(original_info)

    if original_data["data"].get("Mannings") != 0.06:
        print("原始Mannings值不正确")
        return False

    update_input = json.dumps({
        "Storage Area Name": "Storage Area 1",
        "Mannings": 0.03
    })
    result = json.loads(storage_model.update_or_create_storage_area(update_input))
    if result["status"] != "success":
        print(f"更新失败: {result['message']}")
        return False

    updated_info = storage_model.get_storage_area_info("Storage Area 1")
    updated_data = json.loads(updated_info)

    if updated_data["data"].get("Mannings") != 0.03:
        print("更新后的Mannings值不正确")
        return False

    return True


def run_storage_area_tests():
    results = {
        "test_storage_area_read_write": test_storage_area_read_write(),
        "test_storage_area_create_validation": test_storage_area_create_validation(),
        "test_storage_area_update": test_storage_area_update(),
    }
    return results