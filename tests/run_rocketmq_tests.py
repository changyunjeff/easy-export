#!/usr/bin/env python3
"""
RocketMQ测试运行脚本

提供便捷的方式运行RocketMQ相关的所有测试，包括：
- 单元测试
- 集成测试
- API测试
- 可选的实际服务器测试
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败 (返回码: {e.returncode})")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RocketMQ测试运行器")
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="运行单元测试"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="运行集成测试"
    )
    parser.add_argument(
        "--api", 
        action="store_true", 
        help="运行API测试"
    )
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="运行实际服务器测试（需要RocketMQ服务器运行）"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="运行所有测试（除了服务器测试）"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="详细输出"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="生成覆盖率报告"
    )
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 构建基础pytest命令
    base_cmd = ["python", "-m", "pytest"]
    if args.verbose:
        base_cmd.append("-v")
    
    # 如果启用覆盖率
    if args.coverage:
        base_cmd.extend([
            "--cov=core.rocketmq",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    success_count = 0
    total_count = 0
    
    # 运行单元测试
    if args.unit or args.all:
        unit_tests = [
            "tests/test_rocketmq_connection_simple.py",
            "tests/test_rocketmq_producer_simple.py",
            "tests/test_rocketmq_consumer_simple.py",
            "tests/test_rocketmq_monitor_simple.py",
            "tests/test_rocketmq_manager.py",
            "tests/test_memory_queue.py",
            "tests/test_rocketmq_fallback.py"
        ]
        
        for test_file in unit_tests:
            total_count += 1
            if run_command(base_cmd + [test_file], f"单元测试: {test_file}"):
                success_count += 1
    
    # 运行API测试
    if args.api or args.all:
        total_count += 1
        if run_command(base_cmd + ["tests/test_rocketmq_api_minimal.py"], "API测试"):
            success_count += 1
    
    # 运行集成测试
    if args.integration or args.all:
        total_count += 1
        cmd = base_cmd + ["tests/test_rocketmq_integration_simple.py"]
        if args.server:
            cmd.append("--rocketmq-server")
        if run_command(cmd, "集成测试"):
            success_count += 1
    
    # 运行实际服务器测试
    if args.server and not (args.integration or args.all):
        total_count += 1
        cmd = base_cmd + ["tests/test_rocketmq_integration.py", "--rocketmq-server"]
        if run_command(cmd, "实际服务器测试"):
            success_count += 1
    
    # 如果没有指定任何测试类型，默认运行所有单元测试
    if not any([args.unit, args.integration, args.api, args.server, args.all]):
        print("未指定测试类型，运行所有单元测试...")
        args.unit = True
        
        unit_tests = [
            "tests/test_rocketmq_connection_simple.py",
            "tests/test_rocketmq_producer_simple.py",
            "tests/test_rocketmq_consumer_simple.py",
            "tests/test_rocketmq_monitor_simple.py",
            "tests/test_rocketmq_manager.py",
            "tests/test_memory_queue.py",
            "tests/test_rocketmq_fallback.py"
        ]
        
        for test_file in unit_tests:
            total_count += 1
            if run_command(base_cmd + [test_file], f"单元测试: {test_file}"):
                success_count += 1
    
    # 输出总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"总测试文件数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    
    if success_count == total_count:
        print("🎉 所有测试都通过了！")
        sys.exit(0)
    else:
        print("❌ 有测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
