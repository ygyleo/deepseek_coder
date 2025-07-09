import re
import os

class CppPreprocessor:
    """C++代码预处理模块"""
    
    def __init__(self):
        self.function_patterns = [
            # 成员函数模式：TcpSocket::read_n
            r'(\w+(?:::\w+)*)\s*\([^)]*\)\s*\{',
            # 普通函数模式：int func()
            r'(\w+\s+\w+)\s*\([^)]*\)\s*\{',
            # 构造函数模式：TcpSocket()
            r'(\w+)\s*\([^)]*\)\s*\{',
        ]
    
    def extract_functions(self, code_str):
        """提取代码中的所有函数体"""
        functions = []
        lines = code_str.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.function_patterns:
                match = re.search(pattern, line)
                if match:
                    # 找到函数开始
                    start_line = i + 1
                    func_start = i
                    
                    # 寻找对应的结束大括号
                    brace_count = 0
                    end_line = start_line
                    
                    for j in range(i, len(lines)):
                        current_line = lines[j]
                        brace_count += current_line.count('{')
                        brace_count -= current_line.count('}')
                        
                        if brace_count == 0:
                            end_line = j + 1
                            break
                    
                    # 提取函数体（包括函数体内容）
                    func_body = '\n'.join(lines[func_start:end_line])
                    
                    # 提取函数体内部（去掉函数签名）
                    body_start = func_start + 1  # 从函数体开始
                    body_content = '\n'.join(lines[body_start:end_line])
                    
                    functions.append({
                        'name': match.group(1),
                        'body': func_body,
                        'body_content': body_content,  # 只包含函数体内容
                        'start_line': start_line,
                        'end_line': end_line,
                        'original_start': func_start + 1,
                        'body_start_line': body_start + 1  # 函数体内容的起始行号
                    })
                    break
        
        return functions
    
    def cpp_to_c_conversion(self, cpp_code):
        """将C++代码转换为C代码（简化版本）"""
        c_code = cpp_code
        
        # 1. 移除类作用域解析符 ::
        c_code = re.sub(r'(\w+)::(\w+)', r'\2', c_code)
        
        # 2. 移除引用符号 &（在参数中）
        c_code = re.sub(r'(\w+)\s*&\s*(\w+)', r'\1 *\2', c_code)
        
        # 3. 移除模板语法 <...>
        c_code = re.sub(r'<[^>]*>', '', c_code)
        
        # 4. 移除 namespace 声明
        c_code = re.sub(r'namespace\s+\w+\s*\{[^}]*\}', '', c_code)
        
        # 5. 移除 class 声明
        c_code = re.sub(r'class\s+\w+\s*\{[^}]*\}', '', c_code)
        
        # 6. 移除 using 声明
        c_code = re.sub(r'using\s+namespace\s+\w+;', '', c_code)
        c_code = re.sub(r'using\s+\w+::\w+;', '', c_code)
        
        # 7. 移除 C++ 特有类型
        c_code = re.sub(r'\bstring\b', 'char*', c_code)
        c_code = re.sub(r'\bvector\b', 'void*', c_code)
        c_code = re.sub(r'\bmap\b', 'void*', c_code)
        
        # 8. 移除 this 指针
        c_code = re.sub(r'\bthis->', '', c_code)
        
        return c_code
    
    def create_c_wrapper(self, func_body, func_name):
        """为函数体创建C语言包装"""
        # 提取函数签名
        signature_match = re.match(r'([^{]+)\{', func_body)
        if signature_match:
            signature = signature_match.group(1).strip()
            # 清理签名
            signature = re.sub(r'(\w+)::(\w+)', r'\2', signature)  # 移除类作用域
            signature = re.sub(r'(\w+)\s*&\s*(\w+)', r'\1 *\2', signature)  # 引用转指针
            
            # 创建C函数
            c_function = f"""
{signature}
{{
{func_body.split('{', 1)[1]}
"""
            return c_function
        
        return func_body
    
    def is_cpp_code(self, code_str):
        """判断是否为C++代码"""
        cpp_indicators = [
            '::', 'class', 'namespace', 'template', 'this->',
            'string', 'vector', 'map', 'using namespace'
        ]
        
        for indicator in cpp_indicators:
            if indicator in code_str:
                return True
        return False 