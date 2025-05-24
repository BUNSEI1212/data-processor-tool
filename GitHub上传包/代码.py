import tkinter as tk
from tkinter import scrolledtext, Menu, messagebox, simpledialog
import re
import io
import tempfile
import os
import platform
import subprocess

# 尝试导入PIL库，如果没有则提示安装
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 尝试导入matplotlib库，作为图片生成的备选方案
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib import font_manager
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# --------------- 配置与常量 --------------- #
CUSTOM_SORT_ORDER = [
    "+5", "+4.75", "+4.5", "+4.25", "+4", "+3.75", "+3.5", "+3.25", "+3",
    "+2.75", "+2.5", "+2.25", "+2", "+1.75", "+1.5", "+1.25", "+1",
    "+0.75", "+0.5", "+0.25", "0", "0.25", "0.5", "0.75", "1", "1.25",
    "1.5", "1.75", "2", "2.25", "2.5", "2.75", "3", "3.25", "3.5",
    "3.75", "4", "4.25", "4.5", "4.75", "5"
]

# 将排序列表转换为字典以便快速查找索引（用于比较）
SORT_ORDER_MAP = {val: i for i, val in enumerate(CUSTOM_SORT_ORDER)}

DEFAULT_ARROW = " -> "
EQUAL_ARROW_LINE = " -- "

# 颜色（可以根据您的喜好调整）
COLOR_RED = "red"
COLOR_GRAY_BLUE = "steel blue" # 这是一个示例灰蓝色，您可以指定具体的颜色代码


# --------------- 核心处理函数 (占位符/初步实现) --------------- #

def perform_plus_sign_processing(input_text_lines):
    """
    执行"+号处理"。
    基于4个条件的处理规则：
    ①如果左边和右边都没有+则按原样显示为左右两边都没有+
    ②如果左边和右边都有+则显示为左右两边都没有+，如+0.5→+0.75显示为0.5→0.75
    ③如果左边有+而右边没有+，则按原样显示为左边有+，右边没有+，如+0.25→0.75显示为+0.25→0.75
    ④如果左边没有+而右边有+，则显示为左边有+，右边没有+，如0.75→+0.25显示为+0.75→0.25
    """
    print("执行+号处理")
    processed_lines = []
    
    for line in input_text_lines:
        stripped_line = line.strip()
        if not stripped_line:
            processed_lines.append(line)
            continue
            
        # 使用正则表达式解析行格式
        # 匹配格式：(可选括号数字) 数字 箭头 数字
        pattern = re.compile(
            r'^\s*(\(\s*\d+\s*\))?\s*([+-]?\d*\.?\d+)\s*([━➝\-\->]+)\s*([+-]?\d*\.?\d+)\s*$'
        )
        
        match = pattern.match(stripped_line)
        if not match:
            # 如果不匹配标准格式，保持原样
            processed_lines.append(line)
            continue
            
        prefix = match.group(1)  # (数字)
        left_num_str = match.group(2)  # 左侧数字
        arrow = match.group(3)  # 箭头
        right_num_str = match.group(4)  # 右侧数字
        
        # 判断左右数字是否有+号
        left_has_plus = left_num_str.startswith('+')
        right_has_plus = right_num_str.startswith('+')
        
        # 获取数字部分（去掉+号）
        left_num_clean = left_num_str[1:] if left_has_plus else left_num_str
        right_num_clean = right_num_str[1:] if right_has_plus else right_num_str
        
        # 应用4个处理条件
        if not left_has_plus and not right_has_plus:
            # 条件①：左边和右边都没有+ → 按原样显示
            processed_left = left_num_str
            processed_right = right_num_str
        elif left_has_plus and right_has_plus:
            # 条件②：左边和右边都有+ → 显示为左右两边都没有+
            processed_left = left_num_clean
            processed_right = right_num_clean
        elif left_has_plus and not right_has_plus:
            # 条件③：左边有+而右边没有+ → 按原样显示
            processed_left = left_num_str
            processed_right = right_num_str
        else:  # not left_has_plus and right_has_plus
            # 条件④：左边没有+而右边有+ → 左边加+，右边去+
            processed_left = f"+{left_num_clean}"
            processed_right = right_num_clean
        
        # 重建行
        if prefix:
            processed_line = f"{prefix} {processed_left} {arrow} {processed_right}"
        else:
            processed_line = f"{processed_left} {arrow} {processed_right}"
            
        processed_lines.append(processed_line)
    
    return processed_lines


def parse_line_for_formatting(line_str):
    """
    解析单行文本，提取 (前缀), 左数字, 右数字。
    返回一个字典或对象，例如:
    {'prefix': '(9)', 'left_num': '0.5', 'right_num': '0.5', 'raw': line_str}
    或者 None 如果行无效。
    【注意】这是一个初步的解析器，可能需要根据实际数据格式进行强化。
    """
    # 尝试匹配带括号前缀的格式: (数字) 左数字 箭头 右数字
    # 或者不带括号前缀的格式: 左数字 箭头 右数字
    # 箭头可以是 ━━━━━━➝ 或 ------> 等变体
    # 数字可以是整数、小数，可以带正负号
    pattern = re.compile(
        r"^\s*(\(\s*\d+\s*\))?\s*([+-]?\d*\.?\d+)\s*([━➝\-\->]+)\s*([+-]?\d*\.?\d+)\s*$"
    )
    match = pattern.match(line_str)
    if match:
        prefix = match.group(1)
        left_num = match.group(2)
        # arrow = match.group(3) # 箭头本身，暂时不用
        right_num = match.group(4)
        return {
            'prefix': prefix.strip() if prefix else None,
            'left_num': left_num,
            'right_num': right_num,
            'raw': line_str
        }
    # 尝试匹配没有箭头的等值情况，例如 "1.25 ━━━━━━ 1.25" 或 "1.25 ------ 1.25"
    # （这通常是格式化处理的结果，但为了稳健性，解析时也考虑）
    equal_pattern = re.compile(
        r"^\s*(\(\s*\d+\s*\))?\s*([+-]?\d*\.?\d+)\s*([━\-]+)\s*([+-]?\d*\.?\d+)\s*$"
    )
    match_equal = equal_pattern.match(line_str)
    if match_equal:
        prefix = match_equal.group(1)
        left_num = match_equal.group(2)
        right_num = match_equal.group(4)
        # 确保左右数字确实相等，否则格式可能不符合预期
        if left_num == right_num:
             return {
                'prefix': prefix.strip() if prefix else None,
                'left_num': left_num,
                'right_num': right_num, # 存储右数字，即使它与左数字相同
                'raw': line_str,
                'is_equal_line': True # 标记这是个等值行
            }
    print(f"警告: 无法解析行: {line_str}")
    return None


def get_sort_key(num_str):
    """获取数字字符串在自定义排序中的键值"""
    return SORT_ORDER_MAP.get(num_str, float('inf')) # 未在排序表中的数字排在最后


def perform_formatting(input_text_from_box2_lines):
    """
    执行"格式化处理"。
    实现精确的文本对齐和布局，产生客户期望的格式化效果。
    """
    print("执行格式化处理")
    parsed_items = []
    for line in input_text_from_box2_lines:
        if line.strip(): # 跳过空行
            parsed = parse_line_for_formatting(line)
            if parsed:
                parsed_items.append(parsed)

    if not parsed_items:
        return [""] # 没有可处理的内容

    # 1. 按 right_num 分组
    groups = {}
    for item in parsed_items:
        right_val = item['right_num']
        if right_val not in groups:
            groups[right_val] = []
        groups[right_val].append(item)

    # 2. 对每个组内的 left_num 进行排序 (按自定义顺序)
    for right_val in groups:
        groups[right_val].sort(key=lambda x: get_sort_key(x['left_num']))

    # 3. 对这些组进行排序 (主干优先，其他按个数排序)
    # 找出主干（左侧数字个数最多的组）
    max_count = max(len(groups[r_val]) for r_val in groups.keys())
    
    sorted_group_keys = sorted(
        groups.keys(),
        key=lambda r_val: (
            -len(groups[r_val]),  # 个数多的排在前面（负号让大的排前面）
            get_sort_key(groups[r_val][0]['left_num']) if groups[r_val] else float('inf')
        )
    )

    # 4. 创建全局数字位置映射，确保垂直对齐
    all_unique_left_nums = set()
    for items in groups.values():
        for item in items:
            all_unique_left_nums.add(item['left_num'])
    
    # 按自定义顺序排序所有唯一的左侧数字
    sorted_all_left_nums = sorted(all_unique_left_nums, key=get_sort_key)
    
    # 为每个数字分配列位置（每列宽度为8个字符）
    column_positions = {}
    for i, num in enumerate(sorted_all_left_nums):
        column_positions[num] = i * 8

    # 5. 生成格式化后的文本行
    output_lines = []

    for right_val_key in sorted_group_keys:
        items_in_group = groups[right_val_key]
        
        # 获取当前组中的所有左侧数字，按顺序排列
        group_left_nums = [item['left_num'] for item in items_in_group]
        group_left_nums = sorted(set(group_left_nums), key=get_sort_key)
        
        # 计算箭头位置（在最右侧数字之后）
        max_column_pos = max(column_positions[num] for num in group_left_nums)
        arrow_position = max_column_pos + 4  # 减少间距，让布局更紧凑
        
        # 判断箭头类型和长度
        arrow_symbol = DEFAULT_ARROW
        if len(items_in_group) == 1 and items_in_group[0]['left_num'] == items_in_group[0]['right_num']:
            arrow_symbol = EQUAL_ARROW_LINE
        else:
            # 根据数字距离计算箭头长度
            min_left_key = min(get_sort_key(num) for num in group_left_nums)
            max_left_key = max(get_sort_key(num) for num in group_left_nums)
            distance = max_left_key - min_left_key
            # 基础长度3，每增加1个距离单位增加1个实线段，最多6个实线段
            arrow_length = 3 + min(distance // 2, 3)  # 最多6个实线段
            # 创建实线箭头：█████████▶
            solid_line = "━" * arrow_length  # 创建实线部分
            arrow_symbol = solid_line + ">"  # 实线 + 箭头尖
        
        # 构建第一行：左边数字 + 箭头 + 右边数字
        line1 = " " * 100  # 创建足够长的空行
        line1_chars = list(line1)
        
        # 放置左侧数字
        for num in group_left_nums:
            pos = column_positions[num]
            num_str = str(num)
            for i, char in enumerate(num_str):
                if pos + i < len(line1_chars):
                    line1_chars[pos + i] = char
        
        # 放置箭头和右侧数字
        arrow_str = f" {arrow_symbol} {right_val_key}"
        for i, char in enumerate(arrow_str):
            if arrow_position + i < len(line1_chars):
                line1_chars[arrow_position + i] = char
        
        # 转换回字符串并移除尾部空格
        line1_result = ''.join(line1_chars).rstrip()
        output_lines.append(line1_result)

        # 构建第二行：(括号数字)
        prefix_map = {item['left_num']: item['prefix'] for item in items_in_group if item['prefix']}
        
        if prefix_map:
            line2 = " " * 100
            line2_chars = list(line2)
            
            for num in group_left_nums:
                if num in prefix_map:
                    pos = column_positions[num]
                    prefix_str = prefix_map[num]
                    # 将括号数字居中对齐到数字下方
                    center_offset = (len(str(num)) - len(prefix_str)) // 2
                    actual_pos = pos + center_offset
                    for i, char in enumerate(prefix_str):
                        if actual_pos + i < len(line2_chars):
                            line2_chars[actual_pos + i] = char
            
            line2_result = ''.join(line2_chars).rstrip()
            if line2_result.strip():  # 只有在有内容时才添加
                output_lines.append(line2_result)
        
        output_lines.append("")  # 每个组后加一个空行

    # 移除最后的空行
    while output_lines and not output_lines[-1].strip():
        output_lines.pop()

    return output_lines


def set_background_color_and_trigger_key(color_choice):
    """
    设置第三个文本框的背景色并触发F5快捷键
    """
    try:
        if color_choice == COLOR_RED:
            # 设置较深的红色背景
            bg_color = "#ffcccc"  # 较深的红色
        else:  # COLOR_GRAY_BLUE
            # 设置较深的蓝色背景  
            bg_color = "#cce7ff"  # 较深的蓝色
        
        # 设置第三个文本框的背景色
        text_formatted_output.config(bg=bg_color)
        
        # 跨平台触发F5快捷键
        try:
            system = platform.system()
            if system == "Windows":
                # Windows使用PowerShell
                powershell_cmd = '''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.SendKeys]::SendWait("{F5}")
                '''
                subprocess.run(['powershell', '-Command', powershell_cmd], 
                             check=True, capture_output=True, text=True)
            elif system == "Darwin":  # macOS
                # macOS使用AppleScript
                applescript_cmd = '''
                tell application "System Events"
                    key code 96
                end tell
                '''
                subprocess.run(['osascript', '-e', applescript_cmd], 
                             check=True, capture_output=True, text=True)
            elif system == "Linux":
                # Linux使用xdotool（如果可用）
                try:
                    subprocess.run(['xdotool', 'key', 'F5'], 
                                 check=True, capture_output=True, text=True)
                except FileNotFoundError:
                    # 如果xdotool不可用，静默跳过
                    pass
                    
        except Exception as e:
            # 静默处理F5触发失败
            pass
            
    except Exception as e:
        # 静默处理背景色设置失败
        pass


# --------------- UI 事件处理函数 --------------- #

def update_status(message, color="#666666"):
    """更新状态栏信息"""
    status_label.config(text=message, fg=color)
    root.update()

def handle_paste():
    """处理"粘贴"按钮点击事件"""
    try:
        update_status("📋 正在从剪贴板获取文本...", "#2196f3")
        clipboard_text = root.clipboard_get()
        text_input.delete('1.0', tk.END)
        text_input.insert('1.0', clipboard_text)
        
        update_status("⚙️ 正在执行+号处理...", "#ff9800")
        # 自动触发 +号处理
        raw_lines = clipboard_text.splitlines()
        processed_lines = perform_plus_sign_processing(raw_lines)
        text_processed_plus.delete('1.0', tk.END)
        text_processed_plus.insert('1.0', "\n".join(processed_lines))
        
        update_status("✅ 粘贴和+号处理完成！现在可以点击 ⚙️处理 按钮进行格式化", "#4caf50")
        
    except tk.TclError:
        update_status("❌ 剪贴板中没有文本内容", "#f44336")
        messagebox.showerror("粘贴错误", "剪贴板中没有文本内容。")
    except Exception as e:
        update_status("❌ 粘贴处理时发生错误", "#f44336")
        messagebox.showerror("粘贴处理错误", f"发生错误: {str(e)}")

def handle_process_formatting():
    """处理"处理"按钮点击事件"""
    try:
        update_status("⚙️ 正在执行格式化处理...", "#ff9800")
        text_from_box2 = text_processed_plus.get('1.0', tk.END).strip()
        if not text_from_box2:
            update_status("⚠️ 第二个框没有内容，请先粘贴文本", "#ff9800")
            messagebox.showwarning("处理警告", "中间处理框（第二个框）无内容。")
            return
            
        lines_from_box2 = text_from_box2.splitlines()
        formatted_lines = perform_formatting(lines_from_box2)
        
        text_formatted_output.delete('1.0', tk.END)
        text_formatted_output.insert('1.0', "\n".join(formatted_lines))
        
    except Exception as e:
        update_status("❌ 格式化处理时发生错误", "#f44336")
        messagebox.showerror("格式化处理错误", f"发生错误: {str(e)}")
        # 可以在控制台打印更详细的错误堆栈
        import traceback
        traceback.print_exc()


def handle_export():
    """处理"导出"按钮的逻辑（实际导出通过菜单项）"""
    # 这个函数本身可能不需要做什么，因为颜色选择是通过菜单完成的
    # 或者，如果设计成点击按钮后弹出一个颜色选择对话框，则在这里处理
    messagebox.showinfo("导出提示", "请通过导出按钮的下拉选项选择颜色并导出。")


# --------------- 主程序 --------------- #
root = tk.Tk()
root.title("文本处理工具")
root.geometry("800x700") # 设置窗口大小

# --- 创建文本框和对应按钮 ---
frame_text_areas = tk.Frame(root)
frame_text_areas.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# === 第一个文本框和粘贴按钮 ===
frame1 = tk.Frame(frame_text_areas, relief=tk.GROOVE, bd=1)
frame1.pack(fill=tk.BOTH, expand=True, pady=(0,5))

label_frame1 = tk.Frame(frame1, bg="#e3f2fd")
label_frame1.pack(fill=tk.X, padx=2, pady=2)
tk.Label(label_frame1, text="1. 原始输入框 (粘贴于此)", anchor=tk.W, bg="#e3f2fd", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
btn_paste = tk.Button(label_frame1, text="📋 粘贴", command=handle_paste, width=12, bg="#2196f3", fg="white", font=("Arial", 9, "bold"))
btn_paste.pack(side=tk.RIGHT, padx=(10,2))

text_input = scrolledtext.ScrolledText(frame1, wrap=tk.WORD, height=7, font=("Consolas", 10))
text_input.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0,2))

# === 第二个文本框和处理按钮 ===
frame2 = tk.Frame(frame_text_areas, relief=tk.GROOVE, bd=1)
frame2.pack(fill=tk.BOTH, expand=True, pady=(0,5))

label_frame2 = tk.Frame(frame2, bg="#e8f5e8")
label_frame2.pack(fill=tk.X, padx=2, pady=2)
tk.Label(label_frame2, text="2. +号处理结果框 (可编辑)", anchor=tk.W, bg="#e8f5e8", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
btn_process_format = tk.Button(label_frame2, text="⚙️ 处理", command=handle_process_formatting, width=12, bg="#4caf50", fg="white", font=("Arial", 9, "bold"))
btn_process_format.pack(side=tk.RIGHT, padx=(10,2))

text_processed_plus = scrolledtext.ScrolledText(frame2, wrap=tk.WORD, height=7, font=("Consolas", 18, "bold"))
text_processed_plus.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0,2))

# === 第三个文本框和导出按钮 ===
frame3 = tk.Frame(frame_text_areas, relief=tk.GROOVE, bd=1)
frame3.pack(fill=tk.BOTH, expand=True)

label_frame3 = tk.Frame(frame3, bg="#ffe3e3")
label_frame3.pack(fill=tk.X, padx=2, pady=2)
tk.Label(label_frame3, text="3. 格式化处理结果框 (可编辑)", anchor=tk.W, bg="#ffe3e3", font=("Arial", 9, "bold")).pack(side=tk.LEFT)

# 导出按钮使用 Menubutton 实现下拉效果
export_menubutton = tk.Menubutton(label_frame3, text="🎨 背景色 ▼", relief=tk.RAISED, width=12, bg="#f44336", fg="white", font=("Arial", 9, "bold"))
export_menu = Menu(export_menubutton, tearoff=0)
export_menubutton.configure(menu=export_menu)

# 导出选项
export_menu.add_command(label="🔴 设置红色背景", 
                        command=lambda: set_background_color_and_trigger_key(COLOR_RED))
export_menu.add_command(label="🔵 设置蓝色背景", 
                        command=lambda: set_background_color_and_trigger_key(COLOR_GRAY_BLUE))

export_menubutton.pack(side=tk.RIGHT, padx=(10,2))

text_formatted_output = scrolledtext.ScrolledText(frame3, wrap=tk.WORD, height=9, font=("Consolas", 18, "bold"))
text_formatted_output.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0,2))

# === 状态提示区域 ===
status_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1, bg="#f0f0f0")
status_frame.pack(fill=tk.X, padx=10, pady=(0,5))

status_label = tk.Label(status_frame, text="📝 使用说明：1️⃣复制文本 → 📋粘贴 → 2️⃣编辑(可选) → ⚙️处理 → 3️⃣编辑(可选) → 🎨背景色", 
                       bg="#f0f0f0", font=("Arial", 9), anchor=tk.W, fg="#666666")
status_label.pack(side=tk.LEFT, padx=5, pady=3)

# 添加版本信息
version_label = tk.Label(status_frame, text="v2.0 ✨", bg="#f0f0f0", font=("Arial", 8), fg="#999999")
version_label.pack(side=tk.RIGHT, padx=5, pady=3)

# --- 运行主循环 ---
# 设置初始状态
def initialize_app():
    update_status("🎉 文本处理工具已启动！请复制文本内容，然后点击 📋粘贴 开始处理", "#4caf50")

# 延迟执行初始化，确保界面完全加载
root.after(100, initialize_app)

root.mainloop()