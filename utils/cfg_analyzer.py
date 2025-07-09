import re
from typing import List, Dict, Set, Optional

class CfgNode:
    """CFG节点，复用AstNode的核心属性"""
    
    def __init__(self, node_id: int, code: List[str] = None, 
                 connect_to: List[int] = None, children: List['CfgNode'] = None,
                 is_start: bool = False, is_end: bool = False, 
                 line_numbers: List[int] = None):
        self.id = node_id
        self.code = code if code is not None else []
        self.connect_to = connect_to if connect_to is not None else []
        self.children = children if children is not None else []
        self.is_start = is_start
        self.is_end = is_end
        self.line_numbers = line_numbers if line_numbers is not None else []
    
    def add_line_number(self, line_num: int):
        """添加行号"""
        if line_num not in self.line_numbers:
            self.line_numbers.append(line_num)
    
    def get_all_line_numbers(self) -> List[int]:
        """获取所有行号（包括子节点）"""
        all_lines = set(self.line_numbers)
        
        def collect_lines(node):
            all_lines.update(node.line_numbers)
            for child in node.children:
                collect_lines(child)
        
        for child in self.children:
            collect_lines(child)
        
        return sorted(list(all_lines))

class CfgAnalyzer:
    """CFG分析器，复用graph_gen.py的核心逻辑"""
    
    def __init__(self):
        self.node_counter = 0
        self.nodes: List[CfgNode] = []
    
    def create_node(self, code: List[str] = None, line_numbers: List[int] = None) -> CfgNode:
        """创建新节点"""
        node = CfgNode(self.node_counter, code, line_numbers=line_numbers)
        self.node_counter += 1
        return node
    
    def extract_control_flow(self, code_lines: List[str]) -> CfgNode:
        """提取控制流图（简化版本）"""
        if not code_lines:
            return self.create_node()
        
        # 创建根节点
        root = self.create_node()
        self.nodes.append(root)
        
        # 分析控制流结构
        current_node = root
        i = 0
        
        while i < len(code_lines):
            line = code_lines[i].strip()
            
            # 检测控制流语句
            if self._is_if_statement(line):
                if_node = self._process_if_statement(code_lines, i)
                current_node.children.append(if_node)
                current_node.connect_to.append(if_node.id)
                i = self._find_block_end(code_lines, i)
                
            elif self._is_while_statement(line):
                while_node = self._process_while_statement(code_lines, i)
                current_node.children.append(while_node)
                current_node.connect_to.append(while_node.id)
                i = self._find_block_end(code_lines, i)
                
            elif self._is_for_statement(line):
                for_node = self._process_for_statement(code_lines, i)
                current_node.children.append(for_node)
                current_node.connect_to.append(for_node.id)
                i = self._find_block_end(code_lines, i)
                
            else:
                # 普通语句
                current_node.code.append(line)
                if i < len(code_lines):
                    current_node.add_line_number(i + 1)
            
            i += 1
        
        return root
    
    def _is_if_statement(self, line: str) -> bool:
        """检测if语句"""
        return re.match(r'^\s*if\s*\(', line) is not None
    
    def _is_while_statement(self, line: str) -> bool:
        """检测while语句"""
        return re.match(r'^\s*while\s*\(', line) is not None
    
    def _is_for_statement(self, line: str) -> bool:
        """检测for语句"""
        return re.match(r'^\s*for\s*\(', line) is not None
    
    def _process_if_statement(self, code_lines: List[str], start_idx: int) -> CfgNode:
        """处理if语句"""
        if_node = self.create_node()
        self.nodes.append(if_node)
        
        # 提取条件
        condition_line = code_lines[start_idx]
        if_node.code.append(condition_line)
        if_node.add_line_number(start_idx + 1)
        
        # 查找if块和else块
        if_start = start_idx + 1
        if_end = self._find_block_end(code_lines, if_start)
        
        # 处理if块
        if if_end > if_start:
            if_block = self.extract_control_flow(code_lines[if_start:if_end])
            if_node.children.append(if_block)
        
        # 检查是否有else块
        if if_end < len(code_lines) and 'else' in code_lines[if_end]:
            else_start = if_end + 1
            else_end = self._find_block_end(code_lines, else_start)
            
            if else_end > else_start:
                else_block = self.extract_control_flow(code_lines[else_start:else_end])
                if_node.children.append(else_block)
        
        return if_node
    
    def _process_while_statement(self, code_lines: List[str], start_idx: int) -> CfgNode:
        """处理while语句"""
        while_node = self.create_node()
        self.nodes.append(while_node)
        
        # 提取条件
        condition_line = code_lines[start_idx]
        while_node.code.append(condition_line)
        while_node.add_line_number(start_idx + 1)
        
        # 处理循环体
        body_start = start_idx + 1
        body_end = self._find_block_end(code_lines, body_start)
        
        if body_end > body_start:
            body_block = self.extract_control_flow(code_lines[body_start:body_end])
            while_node.children.append(body_block)
        
        return while_node
    
    def _process_for_statement(self, code_lines: List[str], start_idx: int) -> CfgNode:
        """处理for语句"""
        for_node = self.create_node()
        self.nodes.append(for_node)
        
        # 提取for语句
        for_line = code_lines[start_idx]
        for_node.code.append(for_line)
        for_node.add_line_number(start_idx + 1)
        
        # 处理循环体
        body_start = start_idx + 1
        body_end = self._find_block_end(code_lines, body_start)
        
        if body_end > body_start:
            body_block = self.extract_control_flow(code_lines[body_start:body_end])
            for_node.children.append(body_block)
        
        return for_node
    
    def _find_block_end(self, code_lines: List[str], start_idx: int) -> int:
        """查找代码块的结束位置"""
        brace_count = 0
        i = start_idx
        
        while i < len(code_lines):
            line = code_lines[i]
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0:
                return i + 1
            
            i += 1
        
        return len(code_lines)
    
    def collect_all_line_numbers(self, root_node: CfgNode) -> List[int]:
        """收集所有节点的行号"""
        all_lines = set()
        
        def collect_from_node(node):
            all_lines.update(node.line_numbers)
            for child in node.children:
                collect_from_node(child)
        
        collect_from_node(root_node)
        return sorted(list(all_lines))
    
    def assign_line_numbers_recursive(self, node: CfgNode):
        """递归为节点分配行号（复用graph_gen的逻辑）"""
        if not node.line_numbers:
            child_lines = []
            for child in node.children:
                self.assign_line_numbers_recursive(child)
                child_lines.extend(child.line_numbers)
            
            if child_lines:
                node.line_numbers = [min(child_lines)]
        
        return node.line_numbers 