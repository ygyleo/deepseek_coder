import os
import traceback
import graph_gen
from pycparser import parse_file
import json
from cpp_cfg_extractor_v2 import CppCfgExtractorV2

CPP_EXTS = {'.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.c++', '.h++'}

def analyze_c_code_str(code_str, name="code"):
    # 预处理C代码字符串
    txt_list = code_str.splitlines()
    txt = ''
    for each in txt_list:
        if each.find('using') == 0:
            continue
        elif each.find('//') != -1:
            txt += each[:each.find('//')] + '\n'
        else:
            txt += each + '\n'  # 保留换行符
    
    # 检查是否为C++代码
    is_cpp = '::' in txt or 'class' in txt or 'namespace' in txt
    
    if is_cpp:
        # 使用新的C++ CFG提取器
        try:
            cpp_extractor = CppCfgExtractorV2()
            return cpp_extractor.analyze_cpp_code(txt, name)
        except Exception as e:
            return {"name": name, "split_lines": [], "error": f"C++ parsing failed: {str(e)}"}
    with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
        f.write(txt)
    try:
        ast = parse_file(
            'tmp/c_processfile.c',
            use_cpp=True,
            cpp_path=r'/usr/bin/cpp',
            cpp_args='-I utils/fake_libc_include'
        )
        graph = graph_gen.Graph(ast, name)
        all_nodes = []
        def collect_all(node):
            all_nodes.append(node)
            for child in node.child:
                collect_all(child)
        if graph.g is None:
            return {"name": name, "split_lines": [], "error": "empty graph"}
        for node in graph.g:
            collect_all(node)
        all_linenos = []
        seen = set()
        for n in all_nodes:
            if n.id not in seen:
                seen.add(n.id)
                if n.linenos:
                    all_linenos.extend(n.linenos)
        unique_linenos = sorted(list(set(all_linenos)))
        return {
            "name": name,
            "split_lines": unique_linenos
        }
    except Exception as e:
        return {"name": name, "split_lines": [], "error": str(e)}

def analyze_c_file(c_path, output_path):
    # 预处理C文件，生成临时文件
    with open(c_path, encoding='utf-8') as f:
        txt_list = f.readlines()
        txt = ''
        for each in txt_list:
            if each.find('using') == 0:
                continue
            elif each.find('//') != -1:
                txt += each[:each.find('//')] + '\n'
            else:
                txt += each
    with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
        f.write(txt)
    # 解析并生成CFG
    ast = parse_file('tmp/c_processfile.c', use_cpp=True, cpp_path=r'/usr/bin/cpp', cpp_args='-I utils/fake_libc_include')
    graph = graph_gen.Graph(ast, os.path.splitext(os.path.basename(c_path))[0])
    # 输出所有节点信息到txt
    with open(output_path, 'w', encoding='utf-8') as f:
        all_nodes = []
        def collect_all(node):
            all_nodes.append(node)
            for child in node.child:
                collect_all(child)
        if graph.g is None:
            # 如果图为空，输出空的split_lines
            output_data = {
                "file_name": os.path.basename(c_path),
                "split_lines": []
            }
            f.write(json.dumps(output_data, indent=4))
            return
        for node in graph.g:
            collect_all(node)
        
        # 收集所有行号
        all_linenos = []
        seen = set()
        for n in all_nodes:
            if n.id not in seen:
                seen.add(n.id)
                if n.linenos:
                    all_linenos.extend(n.linenos)
        
        # 去重并排序
        unique_linenos = sorted(list(set(all_linenos)))
        
        # 输出JSON格式
        output_data = {
            "file_name": os.path.basename(c_path),
            "split_lines": unique_linenos
        }
        f.write(json.dumps(output_data, indent=4))

def analyze_code_by_filetype(code_str, name, file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in CPP_EXTS:
        # C++ 代码，走tree-sitter方案
        cpp_extractor = CppCfgExtractorV2()
        return cpp_extractor.analyze_cpp_code(code_str, name)
    else:
        # C代码，走graph_gen方案
        try:
            # 预处理：移除所有 #include 语句，并添加必要的函数声明
            lines = code_str.split('\n')
            filtered_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped.startswith('#include'):
                    filtered_lines.append(line)
            
            # 添加必要的函数声明
            function_declarations = """
// 添加必要的函数声明
void* malloc(size_t size);
void free(void* ptr);
void* realloc(void* ptr, size_t size);
size_t strlen(const char* str);
char* strcpy(char* dest, const char* src);
char* strcat(char* dest, const char* src);
int strcmp(const char* str1, const char* str2);
char* strchr(const char* str, int c);
void* memcpy(void* dest, const void* src, size_t n);
int printf(const char* format, ...);
int scanf(const char* format, ...);
int isspace(int c);
int isalpha(int c);
"""
            
            processed_code = function_declarations + '\n'.join(filtered_lines)
            
            os.makedirs('tmp', exist_ok=True)
            with open('tmp/c_processfile.c', 'w', encoding='utf-8') as f:
                f.write(processed_code)
            ast = parse_file(
                'tmp/c_processfile.c',
                use_cpp=True,
                cpp_path='/usr/bin/cpp',
                cpp_args='-I utils/fake_libc_include'
            )
            graph = graph_gen.Graph(ast, name)
            all_nodes = []
            def collect_all(node):
                all_nodes.append(node)
                for child in node.child:
                    collect_all(child)
            if graph.g is None:
                return {"name": name, "split_lines": [], "error": "empty graph"}
            for node in graph.g:
                collect_all(node)
            all_linenos = []
            seen = set()
            for n in all_nodes:
                if n.id not in seen:
                    seen.add(n.id)
                    if n.linenos:
                        all_linenos.extend(n.linenos)
            unique_linenos = sorted(list(set(all_linenos)))
            return {
                "name": name,
                "split_lines": unique_linenos
            }
        except Exception as e:
            return {"name": name, "split_lines": [], "error": str(e)}

def main():
    input_dir = '../datasets/ghidra_output'
    output_path = 'all_blocks.json'
    results = []
    exts = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx', '.c++', '.h++'}
    for file in os.listdir(input_dir):
        ext = os.path.splitext(file)[1].lower()
        if ext in exts:
            file_path = os.path.join(input_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as fin:
                    code = fin.read()
                name = file
                block_info = analyze_code_by_filetype(code, name, file_path)
                # 只保留成功解析的结果（有 split_lines 且不为空，或者没有 error 字段）
                if block_info.get('split_lines') or 'error' not in block_info:
                    results.append(block_info)
                else:
                    print(f"跳过解析失败的文件: {file}")
            except Exception:
                print(f"处理 {file} 时出错：")
                traceback.print_exc()
                continue
    with open(output_path, 'w', encoding='utf-8') as fout:
        json.dump(results, fout, ensure_ascii=False, indent=2)

def main_single(c_path):
    output_path = (os.path.basename(c_path)).split(".")[0] + '.json'
    try:
        analyze_c_file(c_path, output_path)
        # print(f"已处理: {c_path} -> {output_path}")
    except Exception:
        print(f"处理 {c_path} 时出错：")
        traceback.print_exc()
        pass

def main_jsonl(jsonl_path, output_path):
    results = []
    with open(jsonl_path, 'r', encoding='utf-8') as fin:
        for idx, line in enumerate(fin):
            try:
                # 清理换行符
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                code = item.get('code', '')
                name = item.get('name', f'code_{idx}')
                file_path = item.get('file', '')
                block_info = analyze_code_by_filetype(code, name, file_path)
                results.append(block_info)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误，第{idx+1}行: {e}")
                continue
    with open(output_path, 'w', encoding='utf-8') as fout:
        json.dump(results, fout, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # main_single("./test_hex_float.c")
    
    # main()

    # main_jsonl('view.jsonl', 'all_blocks.json')
    main_jsonl('view.jsonl', 'all_blocks.json')