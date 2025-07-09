#!/usr/bin/env python3
import json
from cpp_cfg_extractor_v2 import CppCfgExtractorV2

# 第二个函数的代码
second_function_code = """ssize_t TcpSocket::read_n(void* msg, size_t buf_len)
{
    assert(msg != NULL);
    ssize_t recv_size = 0;
    ssize_t a_recv_size;
    while ((a_recv_size = ::read(fd_, (char*) msg + recv_size, buf_len - recv_size)) > 0) {
        recv_size += a_recv_size;
        if ( recv_size == buf_len )
            break;
    }
    return recv_size;
}"""

def test_second_function():
    extractor = CppCfgExtractorV2()
    result = extractor.analyze_cpp_code(second_function_code, "net::TcpSocket::read_n(void*, unsigned long)")
    
    print("函数名称:", result["name"])
    print("提取的行号:", result["split_lines"])
    print("期望的行号: [3, 4, 7, 9, 10, 12]")  # 函数定义+3=3, 其他+1
    
    expected_lines = [3, 4, 7, 9, 10, 12]
    actual_lines = result["split_lines"]
    
    if actual_lines == expected_lines:
        print("✅ 测试通过！行号提取正确")
    else:
        print("❌ 测试失败！")
        print("缺少的行号:", set(expected_lines) - set(actual_lines))
        print("多余的行号:", set(actual_lines) - set(expected_lines))

if __name__ == "__main__":
    test_second_function() 