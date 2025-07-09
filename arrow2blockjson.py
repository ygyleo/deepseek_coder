#!/usr/bin/env python3
"""
脚本功能：处理datasets目录下的所有.arrow文件
直接读取现有的split_lines结果，进行遮挡处理生成example.jsonl文件
输出格式：包含asm code、split lines，并随机遮挡约40%的block
"""

import os
import json
import sys
import tempfile
import random
from pathlib import Path
from tqdm import tqdm

# 添加utils目录到Python路径
sys.path.append('utils')

def arrow_to_jsonl(arrow_path: str, jsonl_path: str):
    """
    将 .arrow 文件转换为 .jsonl
    使用现有的arrow2json.py逻辑
    """
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
        
        if os.path.exists(jsonl_path):
            os.remove(jsonl_path)  # 若目标文件已存在先删除，避免追加造成重复

        batches = 0
        rows = 0

        with pa.OSFile(arrow_path, 'rb') as source, \
             ipc.RecordBatchStreamReader(source) as reader, \
             open(jsonl_path, 'a', encoding='utf-8') as sink:

            for batch in reader:
                # 将本批次 Arrow RecordBatch 转成 pandas.DataFrame
                df = batch.to_pandas()

                # orient='records' → List[dict]; lines=True → 每条记录结尾带 '\n'
                json_str = df.to_json(orient='records', lines=True, force_ascii=False)
                sink.write(json_str)  # 直接写入文件

                batches += 1
                rows += len(df)

        print(f'  转换完成: {rows} 条记录（{batches} 个 batch）')
        return True
    except Exception as e:
        print(f'  转换失败: {e}')
        return False

def extract_masked_blocks(code_lines, split_lines, blocks_to_mask):
    """
    提取被遮挡的代码块
    
    Args:
        code_lines: 代码行列表
        split_lines: 分块行号列表
        blocks_to_mask: 被遮挡的block起始行号集合
    
    Returns:
        masked_blocks: 被遮挡的代码块列表
    """
    if not split_lines or not blocks_to_mask:
        return []
    
    masked_blocks = []
    current_block_start = None
    
    for i, line in enumerate(code_lines, 1):
        if i in split_lines:
            # 新block开始
            if current_block_start is not None:
                # 处理前一个block
                if current_block_start in blocks_to_mask:
                    # 提取被遮挡的block
                    block_lines = code_lines[current_block_start-1:i-1]
                    masked_blocks.append('\n'.join(block_lines))
            current_block_start = i
    
    # 处理最后一个block
    if current_block_start is not None and current_block_start in blocks_to_mask:
        block_lines = code_lines[current_block_start-1:]
        masked_blocks.append('\n'.join(block_lines))
    
    return masked_blocks

def mask_code_by_split_lines(code_lines, split_lines, mask_ratio=0.4):
    """
    根据split_lines随机遮挡约40%的block
    
    Args:
        code_lines: 代码行列表
        split_lines: 分块行号列表
        mask_ratio: 遮挡比例，默认0.4
    
    Returns:
        masked_code_lines: 遮挡后的代码行列表
        blocks_to_mask: 被遮挡的block起始行号集合
    """
    if not split_lines:
        return code_lines, set()
    
    # 如果只有一个block，全部遮挡
    if len(split_lines) == 1:
        return ['<MASK>'] * len(code_lines), set(split_lines)
    
    # 计算要遮挡的block数量
    num_blocks = len(split_lines)
    num_to_mask = max(1, int(num_blocks * mask_ratio))
    
    # 随机选择要遮挡的block
    blocks_to_mask = set(random.sample(split_lines, num_to_mask))
    
    # 创建遮挡后的代码行
    masked_lines = []
    current_block_start = None
    
    for i, line in enumerate(code_lines, 1):
        if i in split_lines:
            # 新block开始
            if current_block_start is not None:
                # 处理前一个block
                if current_block_start in blocks_to_mask:
                    # 遮挡整个block
                    masked_lines.extend(['<MASK>'] * (i - current_block_start))
                else:
                    # 保持原样
                    masked_lines.extend(code_lines[current_block_start-1:i-1])
            current_block_start = i
    
    # 处理最后一个block
    if current_block_start is not None:
        if current_block_start in blocks_to_mask:
            masked_lines.extend(['<MASK>'] * (len(code_lines) - current_block_start + 1))
        else:
            masked_lines.extend(code_lines[current_block_start-1:])
    
    return masked_lines, blocks_to_mask

def load_split_lines_results(results_file):
    """
    加载现有的split_lines结果文件
    
    Args:
        results_file: 包含split_lines结果的文件路径
    
    Returns:
        dict: 以name为key，split_lines为value的字典
    """
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 构建name到split_lines的映射
        split_lines_map = {}
        for item in results:
            name = item.get('name', '')
            split_lines = item.get('split_lines', [])
            if name:
                split_lines_map[name] = split_lines
        
        print(f"  加载了 {len(split_lines_map)} 条split_lines结果")
        return split_lines_map
    except Exception as e:
        print(f"  加载split_lines结果失败: {e}")
        return {}

def main():
    """主函数"""
    # 设置路径
    datasets_dir = "datasets"
    all_blocks_dir = "/home/featurize/data/all_blocks_jsons"  # 包含split_lines结果的目录
    output_dir = "/home/featurize/data/instructs"  # 输出目录
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有.arrow文件
    arrow_files = []
    for root, dirs, files in os.walk(datasets_dir):
        for file in files:
            if file.endswith('.arrow'):
                arrow_files.append(os.path.join(root, file))
    
    if not arrow_files:
        print("未找到任何.arrow文件")
        return
    
    print(f"找到 {len(arrow_files)} 个.arrow文件:")
    for arrow_file in arrow_files:
        print(f"  {arrow_file}")
    
    print("\n开始处理...")
    
    # 总体进度条
    total_processed = 0
    total_records = 0
    
    # 处理每个.arrow文件
    for file_idx, arrow_file in enumerate(tqdm(arrow_files, desc="处理文件", unit="file")):
        # 生成对应的split_lines结果文件路径
        arrow_name = Path(arrow_file).stem  # 去掉.arrow后缀
        split_lines_file = os.path.join(all_blocks_dir, f"{arrow_name}_all_blocks.json")
        
        if not os.path.exists(split_lines_file):
            print(f"\n跳过 {arrow_file}: 未找到对应的split_lines文件 {split_lines_file}")
            continue
        
        print(f"\n[{file_idx+1}/{len(arrow_files)}] 处理文件: {arrow_name}")
        print(f"  加载split_lines结果文件: {split_lines_file}")
        split_lines_map = load_split_lines_results(split_lines_file)
        
        if not split_lines_map:
            print(f"  跳过 {arrow_file}: split_lines结果为空")
            continue
        
        # 处理单个文件
        file_records = process_arrow_file(arrow_file, output_dir, split_lines_map)
        total_records += file_records
        total_processed += 1
        
        # 显示实时统计
        print(f"  文件处理完成，记录数: {file_records}")
        print(f"  累计处理: {total_processed}/{len(arrow_files)} 文件, {total_records} 条记录")
    
    print(f"\n所有文件处理完成！")
    print(f"总计处理: {total_processed}/{len(arrow_files)} 文件")
    print(f"总计生成: {total_records} 条训练记录")
    print(f"输出目录: {output_dir}")

def process_arrow_file(arrow_file_path, output_dir, split_lines_map):
    """
    处理单个.arrow文件
    
    Args:
        arrow_file_path: .arrow文件路径
        output_dir: 输出目录
        split_lines_map: split_lines结果映射
    
    Returns:
        int: 处理的记录数
    """
    # 生成输出文件名
    arrow_name = Path(arrow_file_path).stem  # 去掉.arrow后缀
    output_file = os.path.join(output_dir, f"{arrow_name}_example.jsonl")
    
    try:
        # 创建临时jsonl文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as tmp_file:
            temp_jsonl_path = tmp_file.name
        
        # 将.arrow文件转换为.jsonl
        if not arrow_to_jsonl(arrow_file_path, temp_jsonl_path):
            return 0
        
        # 读取.jsonl文件
        results = []
        with open(temp_jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    results.append(item)
                except json.JSONDecodeError as e:
                    print(f"    警告: 第{line_num}行JSON解析错误: {e}")
                    continue
        
        print(f"  读取到 {len(results)} 条记录")
        
        # 流式写入example.jsonl文件
        processed_count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, item in enumerate(tqdm(results, desc=f"  处理记录", unit="record", leave=False)):
                try:
                    code = item.get('code', '')
                    name = item.get('name', f'code_{idx}')
                    file_path = item.get('file', '')
                    
                    if not code:
                        print(f"    警告: 第{idx+1}条记录缺少code字段")
                        continue
                    
                    # 从split_lines_map中获取split_lines
                    split_lines = split_lines_map.get(name, [])
                    
                    # 将代码按行分割
                    code_lines = code.split('\n')
                    
                    # 根据split_lines遮挡代码
                    masked_code_lines, blocks_to_mask = mask_code_by_split_lines(code_lines, split_lines)
                    masked_code = '\n'.join(masked_code_lines)
                    
                    # 提取被遮挡的代码块
                    masked_blocks = extract_masked_blocks(code_lines, split_lines, blocks_to_mask)
                    
                    # 获取汇编语言信息
                    asm = item.get('asm', '')
                    
                    # 构建input内容，包含split_lines、汇编语言和遮挡后的代码
                    input_content = f"Split lines: {split_lines}\n\nAssembly language: {asm}\n\nMasked code:\n{masked_code}"
                    
                    # 构建输出记录
                    output_record = {
                        'instruction': 'Please output the masked code blocks in the given assembly code. The code has been split into blocks based on control flow analysis, and some blocks have been masked with <MASK>. You need to reconstruct the original code by filling in the masked blocks.',
                        'input': input_content,  # 包含split_lines、汇编语言和遮挡后的代码
                        'output': '\n\n'.join(masked_blocks)  # 被遮挡的代码块作为输出
                    }
                    
                    # 实时写入jsonl文件
                    f.write(json.dumps(output_record, ensure_ascii=False) + '\n')
                    f.flush()  # 确保立即写入磁盘
                    
                    processed_count += 1
                    
                    # 每处理100条记录显示一次进度
                    if processed_count % 100 == 0:
                        print(f"    已处理: {processed_count}/{len(results)} 条记录")
                    
                except Exception as e:
                    print(f"    错误: 处理第{idx+1}条记录时出错: {e}")
                    continue
        
        print(f"  文件处理完成，成功处理 {processed_count}/{len(results)} 条记录")
        print(f"  结果已保存到: {output_file}")
        
        # 清理临时文件
        os.unlink(temp_jsonl_path)
        
        return processed_count
        
    except Exception as e:
        print(f"  错误: 处理文件 {arrow_file_path} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    main()
