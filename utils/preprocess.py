import re
import os
import chardet

# 获取文件编码格式
def get_encode(path):
    f = open(path, 'rb')
    data = f.read()
    f.close()
    encode = (chardet.detect(data))['encoding']
    if encode is None:
        return 'utf-8'
    return encode

def detect_return_type(code):
    """
    检测代码中第一个return语句的类型
    返回类型字符串
    """
    # 匹配return语句的正则表达式
    return_pattern = r'return\s+([^;]+);'
    matches = re.findall(return_pattern, code)
    
    if not matches:
        return 'void'  # 没有return语句，返回void
    
    first_return = matches[0].strip()
    
    # 检查是否是数字字面量
    if re.match(r'^-?\d+$', first_return):
        return 'int'
    elif re.match(r'^-?\d+\.\d+[fF]?$', first_return):
        return 'float'
    elif re.match(r'^-?\d+\.\d+[lL]?$', first_return):
        return 'double'
    elif re.match(r'^-?\d+[lL]$', first_return):
        return 'long'
    elif re.match(r'^-?\d+[sS]$', first_return):
        return 'short'
    elif re.match(r'^[\'\"].*[\'\"]$', first_return):
        return 'char'
    elif first_return == 'NULL':
        return 'void*'
    elif first_return in ['true', 'false', '1', '0']:
        return 'int'
    elif re.match(r'^0x[0-9a-fA-F]+$', first_return):
        # 检查是否是十六进制浮点数表示
        try:
            import struct
            hex_val = int(first_return, 16)
            # 尝试解释为float
            float_val = struct.unpack('f', struct.pack('I', hex_val))[0]
            # 如果解释出的浮点数看起来合理（不是NaN或无穷大），则认为是float
            if not (float_val != float_val or float_val == float('inf') or float_val == float('-inf')):
                return 'float'
        except:
            pass
        # 如果无法解释为浮点数，默认为int
        return 'int'
    else:
        # 检查是否是变量名，尝试在函数体内查找声明
        # 匹配常见类型声明
        type_patterns = [
            (r'\bint\s+%s\b', 'int'),
            (r'\bfloat\s+%s\b', 'float'),
            (r'\bdouble\s+%s\b', 'double'),
            (r'\blong\s+%s\b', 'long'),
            (r'\bshort\s+%s\b', 'short'),
            (r'\bchar\s+%s\b', 'char'),
            (r'\bvoid\s*\*\s*%s\b', 'void*'),
        ]
        for pat, typ in type_patterns:
            # 只查找函数体（去掉声明部分）
            func_body_match = re.search(r'\{([\s\S]*)\}', code)
            if func_body_match:
                func_body = func_body_match.group(1)
                # 变量名可能带[]或*
                varname = re.sub(r'\[.*\]|\*', '', first_return).strip()
                if re.search(pat % re.escape(varname), func_body):
                    return typ
        # 如果没找到，默认int
        return 'int'

def make_to_string(data):
    bds0 = '//.*'  # 标准匹配单行注释
    bds1 = '\/\*(?:[^\*]|\*+[^\/\*])*\*+\/'  # 标准匹配多行注释  可匹配跨行注释
    target0 = re.compile(bds0)  # 单行注释
    target = re.compile(bds1)  # 编译正则表达式

    result0 = target0.findall(data)

    result = target.findall(data)

    result += result0
    for i in result:
        data = data.replace(i, '')  # 替换为空字符串

    # 按行分割，然后过滤空行
    lines = data.split('\n')
    # a. 过滤掉完全是空白的行
    # b. 保留有内容的行以及它们的缩进
    non_empty_lines = [line for line in lines if line.strip()]
    mn = "\n".join(non_empty_lines)
    
    # 检测返回类型
    return_type = detect_return_type(mn)
    
    # 查找第一个函数声明并替换其返回类型
    # 匹配函数声明模式：类型 函数名(参数)
    # 支持Ghidra的undefined4等类型格式
    func_pattern = r'(\w+)\s+(\w+\s*\([^)]*\)\s*\{)'
    match = re.search(func_pattern, mn)
    
    if match:
        # 替换函数声明的返回类型
        mn = re.sub(func_pattern, return_type + r' \2', mn, count=1)
    else:
        # 如果没有找到函数声明，报错
        raise ValueError("未找到函数声明，无法处理代码")
    
    return mn

if __name__ == '__main__':
    # 测试不同类型的return语句
    test_path = 'test_return_types.c'
    with open(test_path, 'r', encoding='utf-8') as f:
        test_data = f.read()
    
    print("测试不同类型的return语句:")
    print("=" * 50)
    
    # 分割函数并测试每个函数
    functions = re.split(r'(\w+\s+\w+\s*\([^)]*\)\s*\{)', test_data)
    
    for i in range(1, len(functions), 2):
        if i + 1 < len(functions):
            func_decl = functions[i]
            func_body = functions[i + 1]
            full_func = func_decl + func_body
            
            # 检测返回类型
            detected_type = detect_return_type(full_func)
            print(f"函数: {func_decl.strip()}")
            print(f"检测到的返回类型: {detected_type}")
            print("-" * 30)
    
    print("\n" + "=" * 50)
    print("原始文件处理:")
    
    in_path = '../evaluation/original_func0.c'  # 输入文件路径
    with open(in_path, 'r', encoding='utf-8') as f:
        data = f.read()
    # out_path = 'output.c'  # 输出文件路径
    result = make_to_string(data)
    print("处理后的代码:")
    print(result)
    # print(f"Processed file saved to {out_path}")