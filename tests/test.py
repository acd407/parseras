import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 导入各个测试模块
from tests.test_geometry import test_geometry, GEOMETRY_TESTS
from tests.test_block import run_block_tests
from tests.test_full_file import run_full_file_tests
from tests.test_river_modification import test_river_modification
from tests.test_cross_section import test_cross_section_read_write


def main():
    # 运行几何测试
    geometry_results = {}
    for test_config in GEOMETRY_TESTS:
        geometry_results[test_config["test_name"]] = test_geometry(test_config)

    # 运行数据块测试
    block_results = run_block_tests()

    # 运行完整文件测试
    full_file_results = run_full_file_tests()

    # 运行河流修改测试
    river_modification_result = test_river_modification()

    # 运行断面修改测试
    cross_section_modification_result = test_cross_section_read_write()

    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    all_passed = True

    # 打印几何测试结果
    for test_name, passed in geometry_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 60)

    # 打印数据块测试结果
    for test_name, passed in block_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 60)

    # 打印完整文件测试结果
    for test_name, passed in full_file_results.items():
        print(f"{'✅' if passed else '❌'} {test_name} test: {'PASSED' if passed else 'FAILED'}")
        all_passed = all_passed and passed

    print("=" * 60)

    # 打印河流修改测试结果
    print(
        f"{'✅' if river_modification_result else '❌'} River Modification test: {'PASSED' if river_modification_result else 'FAILED'}"
    )
    all_passed = all_passed and river_modification_result

    print("=" * 60)

    # 打印断面修改测试结果
    print(
        f"{'✅' if cross_section_modification_result else '❌'} Cross Section Modification test: {'PASSED' if cross_section_modification_result else 'FAILED'}"
    )
    all_passed = all_passed and cross_section_modification_result

    print("=" * 80)

    if all_passed:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
