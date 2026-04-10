# -*- coding: utf-8 -*-
"""
软件著作权申请 - 源代码文档生成器
生成软著申请所需的源代码文档（前30页+后30页）
"""
import os
import glob

# 项目根目录
PROJECT_ROOT = r"F:\A-User\cliff\allin\all"
OUTPUT_FILE = r"F:\A-User\cliff\allin\软著申请材料\源代码文档.txt"

# 需要包含的源代码文件列表（按优先级排序）
SOURCE_FILES = [
    # 主入口
    "main.py",
    "config.py",

    # 核心模块
    r"核心模块\数据采集\data_generator.py",
    r"核心模块\数据存储\redis_database.py",
    r"核心模块\数据同步\sync_to_mongo.py",

    # 仪表盘模块
    r"仪表盘\main.py",
    r"仪表盘\ui_main_window.py",
    r"仪表盘\ui_sensor_collection.py",
    r"仪表盘\ui_sensor_dock.py",
    r"仪表盘\ui_docks.py",
    r"仪表盘\core_theme_manager.py",
    r"仪表盘\core_data_simulator.py",
    r"仪表盘\ui_chart_widget.py",
    r"仪表盘\ui_custom_widgets.py",
    r"仪表盘\ui_motion_capture.py",

    # 风场设置模块
    r"风场设置\main.py",
    r"风场设置\main_control\config.py",
    r"风场设置\main_control\canvas_widget.py",
    r"风场设置\main_control\commands.py",
    r"风场设置\main_control\function_3d_view.py",
    r"风场设置\main_control\properties_panel.py",
    r"风场设置\main_control\template_library.py",
    r"风场设置\main_control\timeline_widget.py",
    r"风场设置\main_control\utils.py",

    # 硬件控制模块
    r"硬件控制\hardware\fan_control\config.py",
    r"硬件控制\hardware\fan_control\modbus_fan.py",
    r"硬件控制\hardware\fan_control\batch_control.py",
    r"硬件控制\hardware\fan_control\pwm_csv_recorder.py",

    # 风场编辑器
    r"wind_field_editor_code\core.py",
    r"wind_field_editor_code\functions.py",
    r"wind_field_editor_code\analyzer.py",
    r"wind_field_editor_code\tools.py",
    r"wind_field_editor_code\utils.py",

    # 前处理模块
    r"前处理\CFD_module\pre_processor_config.py",
    r"前处理\CFD_module\scene_generator.py",
    r"前处理\CFD_module\grid_utils.py",
    r"前处理\CFD_module\file_handler.py",
    r"前处理\CFD_module\pre_processor_window.py",

    # 测试模块
    r"tests\test_utils.py",
]

# 排除的文件（测试、调试、示例文件）
EXCLUDE_PATTERNS = [
    "test_",
    "demo_",
    "example_",
    "debug",
    "old_",
    "backup",
    "temp",
    ".pyc",
    "__pycache__",
]

# 页面配置
LINES_PER_PAGE = 50
TOTAL_PAGES = 60  # 前30页 + 后30页


def read_file_safely(file_path):
    """安全读取文件，处理编码问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()
        except:
            return None
    except Exception:
        return None


def generate_header(title):
    """生成文档头部"""
    return f"""
{'=' * 80}
{title.center(80)}
{'=' * 80}

软件名称：微小型无人机智能风场测试评估系统
版本号：V2.0.0
文档类型：源代码文档
生成日期：2026年01月

{'=' * 80}
"""


def generate_file_header(filename, page_num):
    """生成文件头部"""
    return f"""
{'-' * 80}
文件：{filename}
{'-' * 80}
[第 {page_num} 页]

"""


def collect_source_code():
    """收集所有源代码"""
    all_code = []
    file_list = []

    for relative_path in SOURCE_FILES:
        full_path = os.path.join(PROJECT_ROOT, relative_path)

        if os.path.exists(full_path):
            content = read_file_safely(full_path)
            if content:
                lines = content.split('\n')
                file_list.append((relative_path, lines))
            else:
                print(f"警告: 无法读取文件 {relative_path}")
        else:
            print(f"警告: 文件不存在 {relative_path}")

    return file_list


def generate_source_document():
    """生成源代码文档"""
    print("正在生成源代码文档...")

    # 创建输出目录
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        # 写入文档头部
        out.write(generate_header("微小型无人机智能风场测试评估系统 - 源代码文档"))

        # 收集源代码
        file_list = collect_source_code()

        if not file_list:
            out.write("错误: 没有找到任何源代码文件！\n")
            return

        # 计算总代码行数
        total_lines = sum(len(lines) for _, lines in file_list)
        print(f"总共收集到 {total_lines} 行源代码，来自 {len(file_list)} 个文件")

        # 前30页：从头开始
        out.write("\n")
        out.write("=" * 80)
        out.write("\n")
        out.write("前30页源代码".center(80))
        out.write("\n")
        out.write("=" * 80)
        out.write("\n\n")

        current_page = 1
        lines_on_page = 0

        for file_path, lines in file_list:
            out.write(generate_file_header(file_path, current_page))

            for i, line in enumerate(lines, 1):
                # 添加行号
                out.write(f"{i:4d}\t{line}\n")
                lines_on_page += 1

                # 检查是否需要换页
                if lines_on_page >= LINES_PER_PAGE:
                    current_page += 1
                    lines_on_page = 0

                    if current_page > 30:
                        break
                    out.write("\n")
                    out.write(generate_file_header(file_path, current_page))

            if current_page > 30:
                break

        # 后30页：从末尾开始
        out.write("\n\n")
        out.write("=" * 80)
        out.write("\n")
        out.write("后30页源代码".center(80))
        out.write("\n")
        out.write("=" * 80)
        out.write("\n\n")

        current_page = 31
        lines_on_page = 0

        # 反向遍历文件
        for file_path, lines in reversed(file_list):
            out.write(generate_file_header(file_path, current_page))

            # 反向遍历行
            for i, line in enumerate(reversed(lines), 1):
                # 计算原始行号
                original_line_num = len(lines) - i + 1
                out.write(f"{original_line_num:4d}\t{line}\n")
                lines_on_page += 1

                if lines_on_page >= LINES_PER_PAGE:
                    current_page += 1
                    lines_on_page = 0

                    if current_page > 60:
                        break
                    out.write("\n")
                    out.write(generate_file_header(file_path, current_page))

            if current_page > 60:
                break

        # 写入文档尾部
        out.write("\n\n")
        out.write("=" * 80)
        out.write("\n")
        out.write("源代码文档结束".center(80))
        out.write("\n")
        out.write("=" * 80)
        out.write(f"\n\n总页数：60页（前30页 + 后30页）")
        out.write(f"\n生成时间：2026年01月")
        out.write("\n\n")

    print(f"源代码文档已生成：{OUTPUT_FILE}")
    print(f"文档包含 {len(file_list)} 个源代码文件")


if __name__ == "__main__":
    generate_source_document()
