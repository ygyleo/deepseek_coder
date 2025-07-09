import os
from typing import List, Dict
from tree_sitter import Language, Parser
import graph_gen

# 使用 tree-sitter-cpp 包
CPP_LANGUAGE = Language('../build/my-languages.so', 'cpp')
parser = Parser()
parser.set_language(CPP_LANGUAGE)

CONTROL_FLOW_TYPES = {
    'if_statement', 'while_statement', 'for_statement', 'switch_statement',
    'case_statement', 'return_statement', 'break_statement', 'continue_statement',
    'function_definition'
}

class CppCfgExtractorV2:
    """C++ CFG提取器，基于 tree-sitter 语法树分析"""
    def __init__(self):
        pass
    
    def analyze_cpp_code(self, code_str: str, name: str = "code") -> Dict:
        """处理 C++ 代码"""
        try:
            # CFG分块节点类型
            BLOCK_NODE_TYPES = {
                'if_statement', 'while_statement', 'for_statement', 'switch_statement',
                'case_statement', 'return_statement', 'break_statement', 'continue_statement',
                'compound_statement', 'do_statement', 'else_clause', 'do_while_statement'
            }

            def is_block_node(node):
                return node.type in BLOCK_NODE_TYPES

            def is_meaningful_statement(node):
                # 跳过大括号、空节点、注释、预处理、分号等
                if node.type in (';', '{', '}', 'comment', 'preproc_call', 'preproc_def', 'preproc_if', 'preproc_elif', 'preproc_else', 'preproc_end', 'preproc_include'):
                    return False
                # 跳过空白节点
                if not hasattr(node, 'start_point'):
                    return False
                return True

            def process_compound_statement(node, blocks):
                if node.type != 'compound_statement':
                    return
                children = node.children
                n = len(children)
                i = 0
                while i < n:
                    child = children[i]
                    if child.type == '{' or child.type == '}':
                        i += 1
                        continue
                    if is_block_node(child):
                        blocks.append(child.start_point[0] + 1)
                        for c in child.children:
                            if c.type == 'compound_statement':
                                process_compound_statement(c, blocks)
                            else:
                                process_node_recursively(c, blocks)
                        i += 1
                    else:
                        # 连续顺序语句合并为一个块，只保留首行号
                        seq_start = i
                        while i < n and not is_block_node(children[i]) and is_meaningful_statement(children[i]) and children[i].type not in ('{', '}'):
                            i += 1
                        if seq_start < i:
                            blocks.append(children[seq_start].start_point[0] + 1)
                        if i == seq_start:
                            i += 1

            def process_node_recursively(node, blocks):
                if node.type == 'compound_statement':
                    process_compound_statement(node, blocks)
                elif is_block_node(node):
                    blocks.append(node.start_point[0] + 1)
                    for child in node.children:
                        process_node_recursively(child, blocks)
                elif is_meaningful_statement(node):
                    blocks.append(node.start_point[0] + 1)
                else:
                    for child in node.children:
                        process_node_recursively(child, blocks)

            # 入口：只处理函数体
            tree = parser.parse(bytes(code_str, 'utf8'))
            root = tree.root_node
            result = []
            for node in root.children:
                if node.type == 'function_definition':
                    for child in node.children:
                        if child.type == 'compound_statement':
                            process_compound_statement(child, result)
            unique_lines = sorted(set(result))
            return {
                "name": name,
                "split_lines": unique_lines
            }
        except Exception as e:
            return {
                "name": name,
                "split_lines": [],
                "error": f"tree-sitter analysis failed: {str(e)}"
            }

    def analyze_c_code(self, code_str: str, name: str = "code") -> Dict:
        """处理 C 代码"""
        try:
            # CFG分块节点类型
            BLOCK_NODE_TYPES = {
                'if_statement', 'while_statement', 'for_statement', 'switch_statement',
                'case_statement', 'return_statement', 'break_statement', 'continue_statement',
                'compound_statement', 'do_statement', 'else_clause', 'do_while_statement'
            }

            def is_block_node(node):
                return node.type in BLOCK_NODE_TYPES

            def is_meaningful_statement(node):
                # 跳过大括号、空节点、注释、预处理、分号等
                if node.type in (';', '{', '}', 'comment', 'preproc_call', 'preproc_def', 'preproc_if', 'preproc_elif', 'preproc_else', 'preproc_end', 'preproc_include'):
                    return False
                # 跳过空白节点
                if not hasattr(node, 'start_point'):
                    return False
                return True

            def process_compound_statement(node, blocks):
                if node.type != 'compound_statement':
                    return
                children = node.children
                n = len(children)
                i = 0
                while i < n:
                    child = children[i]
                    if child.type == '{' or child.type == '}':
                        i += 1
                        continue
                    if is_block_node(child):
                        blocks.append(child.start_point[0] + 1)
                        for c in child.children:
                            if c.type == 'compound_statement':
                                process_compound_statement(c, blocks)
                            else:
                                process_node_recursively(c, blocks)
                        i += 1
                    else:
                        # 连续顺序语句合并为一个块，只保留首行号
                        seq_start = i
                        while i < n and not is_block_node(children[i]) and is_meaningful_statement(children[i]) and children[i].type not in ('{', '}'):
                            i += 1
                        if seq_start < i:
                            blocks.append(children[seq_start].start_point[0] + 1)
                        if i == seq_start:
                            i += 1

            def process_node_recursively(node, blocks):
                if node.type == 'compound_statement':
                    process_compound_statement(node, blocks)
                elif is_block_node(node):
                    blocks.append(node.start_point[0] + 1)
                    for child in node.children:
                        process_node_recursively(child, blocks)
                elif is_meaningful_statement(node):
                    blocks.append(node.start_point[0] + 1)
                else:
                    for child in node.children:
                        process_node_recursively(child, blocks)

            # 入口：只处理函数体
            tree = parser.parse(bytes(code_str, 'utf8'))
            root = tree.root_node
            result = []
            for node in root.children:
                if node.type == 'function_definition':
                    for child in node.children:
                        if child.type == 'compound_statement':
                            process_compound_statement(child, result)
            unique_lines = sorted(set(result))
            return {
                "name": name,
                "split_lines": unique_lines
            }
        except Exception as e:
            return {
                "name": name,
                "split_lines": [],
                "error": f"tree-sitter analysis failed: {str(e)}"
            }
    
    def _analyze_as_c_code(self, code_str: str, name: str) -> Dict:
        # 兼容接口，直接用 graph_gen 处理
        try:
            os.makedirs('tmp', exist_ok=True)
            with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
                f.write(code_str)
            from pycparser import parse_file
            ast = parse_file(
                'tmp/c_processfile.c',
                use_cpp=True,
                cpp_path='/usr/bin/cpp',
                cpp_args='-I utils/fake_libc_include'
            )
            graph = graph_gen.Graph(ast, name)
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
    
    def _extract_line_numbers_from_graph(self, graph: graph_gen.Graph) -> List[int]:
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