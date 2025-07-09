import pyarrow as pa
import pyarrow.ipc as ipc
import json
import os

def arrow_to_jsonl(arrow_path: str, jsonl_path: str):
    """
    将 .arrow 或 .arrowstream 文件转换为 .jsonl
    每一行是一条记录（dict → JSON 字符串）
    """
    if os.path.exists(jsonl_path):
        os.remove(jsonl_path)          # 若目标文件已存在先删除，避免追加造成重复

    batches = 0
    rows    = 0

    with pa.OSFile(arrow_path, 'rb') as source, \
         ipc.RecordBatchStreamReader(source) as reader, \
         open(jsonl_path, 'a', encoding='utf-8') as sink:

        for batch in reader:
            # 将本批次 Arrow RecordBatch 转成 pandas.DataFrame
            df = batch.to_pandas()

            # orient='records' → List[dict]; lines=True → 每条记录结尾带 '\n'
            json_str = df.to_json(orient='records', lines=True, force_ascii=False)
            sink.write(json_str)       # 直接写入文件

            batches += 1
            rows    += len(df)

    print(f'✅ 已写出 {rows} 条记录（{batches} 个 batch）到 {jsonl_path}')

# 示例调用
arrow_file = "data-00000-of-00017.arrow"
jsonl_file = "data-00000-of-00017.jsonl"
arrow_to_jsonl(arrow_file, jsonl_file)