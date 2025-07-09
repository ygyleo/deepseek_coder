import re

class SimpleCppParser:
    """简单的C++代码解析器，用于提取行号信息"""
    
    def __init__(self):
        pass
    
    def analyze_cpp_code(self, code_str, name="code"):
        """分析C++代码，返回行号信息"""
        try:
            # 提取函数定义的行号
            function_lines = self.extract_function_lines(code_str)
            
            # 如果没有找到函数定义，返回所有非空行
            if not function_lines:
                lines = code_str.split('\n')
                line_numbers = []
                
                for i, line in enumerate(lines, 1):
                    # 跳过空行和只包含空白字符的行
                    if line.strip():
                        line_numbers.append(i)
                
                return {
                    "name": name,
                    "split_lines": line_numbers
                }
            else:
                return {
                    "name": name,
                    "split_lines": function_lines
                }
        except Exception as e:
            return {
                "name": name,
                "split_lines": [],
                "error": f"C++ parsing failed: {str(e)}"
            }
    
    def extract_function_lines(self, code_str):
        """提取函数定义的行号范围"""
        lines = code_str.split('\n')
        function_lines = []
        
        for i, line in enumerate(lines, 1):
            # 检测函数定义（简化版本）
            if re.search(r'\w+\s+\w+\s*\([^)]*\)\s*\{', line):
                # 找到函数开始
                start_line = i
                # 寻找对应的结束大括号
                brace_count = 0
                end_line = start_line
                
                for j in range(i-1, len(lines)):
                    current_line = lines[j]
                    brace_count += current_line.count('{')
                    brace_count -= current_line.count('}')
                    
                    if brace_count == 0:
                        end_line = j + 1
                        break
                
                # 添加函数的所有行号
                for line_num in range(start_line, end_line + 1):
                    if line_num not in function_lines:
                        function_lines.append(line_num)
        
        return sorted(function_lines) 