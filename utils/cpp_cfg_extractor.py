import os
import re
from typing import List, Dict, Optional
from pycparser import parse_file
import graph_gen
from cpp_preprocessor import CppPreprocessor
from cfg_analyzer import CfgAnalyzer

class CppCfgExtractor:
    """完整的C++代码CFG提取器"""
    
    def __init__(self):
        self.cpp_preprocessor = CppPreprocessor()
        self.cfg_analyzer = CfgAnalyzer()
    
    def analyze_cpp_code(self, code_str: str, name: str = "code") -> Dict:
        """分析C++代码，返回行号切分信息"""
        try:
            # 1. 检查是否为C++代码
            if not self.cpp_preprocessor.is_cpp_code(code_str):
                # 如果不是C++代码，尝试直接用C解析器
                return self._analyze_as_c_code(code_str, name)
            
            # 2. 提取函数体
            functions = self.cpp_preprocessor.extract_functions(code_str)
            
            if not functions:
                # 如果没有找到函数，使用简单行号提取
                return self._simple_line_extraction(code_str, name)
            
            # 3. 处理每个函数
            all_line_numbers = []
            
            for func in functions:
                func_lines = self._process_single_function(func)
                all_line_numbers.extend(func_lines)
            
            # 去重并排序
            unique_lines = sorted(list(set(all_line_numbers)))
            
            return {
                "name": name,
                "split_lines": unique_lines
            }
            
        except Exception as e:
            return {
                "name": name,
                "split_lines": [],
                "error": f"C++ analysis failed: {str(e)}"
            }
    
    def _process_single_function(self, func: Dict) -> List[int]:
        """处理单个函数"""
        func_body = func['body']
        body_content = func['body_content']  # 只包含函数体内容
        body_start_line = func['body_start_line']  # 函数体内容的起始行号
        
        # 尝试转换为C代码并用pycparser解析
        try:
            c_code = self.cpp_preprocessor.cpp_to_c_conversion(body_content)
            c_wrapper = self.cpp_preprocessor.create_c_wrapper(c_code, func['name'])
            
            # 写入临时文件
            temp_file = f'tmp/cpp_func_{func["name"].replace("::", "_")}.c'
            os.makedirs('tmp', exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(c_wrapper)
            
            # 尝试用pycparser解析
            try:
                ast = parse_file(
                    temp_file,
                    use_cpp=True,
                    cpp_path='/usr/bin/cpp',
                    cpp_args='-I utils/fake_libc_include'
                )
                
                # 使用graph_gen解析
                graph = graph_gen.Graph(ast, func['name'])
                
                # 提取行号
                line_numbers = self._extract_line_numbers_from_graph(graph)
                
                # 调整行号偏移 - 使用函数体内容的起始行号
                adjusted_lines = [line + body_start_line - 1 for line in line_numbers]
                
                # 添加函数开始行号
                adjusted_lines.append(func['original_start'])
                
                return adjusted_lines
                
            except Exception as parse_error:
                # pycparser解析失败，使用CFG分析器
                return self._analyze_with_cfg_analyzer(body_content, body_start_line, func['original_start'])
                
        except Exception as e:
            # 转换失败，使用CFG分析器
            return self._analyze_with_cfg_analyzer(body_content, body_start_line, func['original_start'])
    
    def _analyze_with_cfg_analyzer(self, func_body: str, body_start_line: int, func_start_line: int) -> List[int]:
        """使用CFG分析器分析函数"""
        lines = func_body.split('\n')
        
        # 创建CFG
        root_node = self.cfg_analyzer.extract_control_flow(lines)
        
        # 分配行号
        self.cfg_analyzer.assign_line_numbers_recursive(root_node)
        
        # 收集行号
        line_numbers = self.cfg_analyzer.collect_all_line_numbers(root_node)
        
        # 调整行号偏移 - 使用函数体内容的起始行号
        adjusted_lines = [line + body_start_line - 1 for line in line_numbers]
        
        # 添加函数开始行号
        adjusted_lines.append(func_start_line)
        
        return adjusted_lines
    
    def _extract_line_numbers_from_graph(self, graph: graph_gen.Graph) -> List[int]:
        """从graph_gen.Graph中提取行号"""
        all_nodes = []
        
        def collect_all(node):
            all_nodes.append(node)
            for child in node.child:
                collect_all(child)
        
        if graph.g is None:
            return []
        
        for node in graph.g:
            collect_all(node)
        
        all_linenos = []
        seen = set()
        
        for n in all_nodes:
            if n.id not in seen:
                seen.add(n.id)
                if n.linenos:
                    all_linenos.extend(n.linenos)
        
        return sorted(list(set(all_linenos)))
    
    def _analyze_as_c_code(self, code_str: str, name: str) -> Dict:
        """作为C代码分析"""
        try:
            # 写入临时文件
            os.makedirs('tmp', exist_ok=True)
            with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
                f.write(code_str)
            
            # 使用pycparser解析
            ast = parse_file(
                'tmp/c_processfile.c',
                use_cpp=True,
                cpp_path='/usr/bin/cpp',
                cpp_args='-I utils/fake_libc_include'
            )
            
            # 使用graph_gen解析
            graph = graph_gen.Graph(ast, name)
            
            # 提取行号
            line_numbers = self._extract_line_numbers_from_graph(graph)
            
            return {
                "name": name,
                "split_lines": line_numbers
            }
            
        except Exception as e:
            return {
                "name": name,
                "split_lines": [],
                "error": f"C analysis failed: {str(e)}"
            }
    
    def _simple_line_extraction(self, code_str: str, name: str) -> Dict:
        """简单行号提取（降级方案）"""
        lines = code_str.split('\n')
        line_numbers = []
        
        for i, line in enumerate(lines, 1):
            if line.strip():  # 非空行
                line_numbers.append(i)
        
        return {
            "name": name,
            "split_lines": line_numbers
        } 