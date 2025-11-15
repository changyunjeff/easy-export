"""
安全验证功能MVP
演示：模板路径白名单、文件类型验证、文件内容校验

功能：
1. 模板路径白名单 - 防止路径遍历攻击
2. 文件类型验证 - MIME类型和扩展名验证
3. 文件大小限制 - 防止大文件攻击
4. 文件哈希校验 - 确保文件完整性
5. 数据脱敏 - 日志敏感信息处理
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Tuple


class SecurityValidator:
    """安全验证器"""
    
    # 允许的模板文件扩展名
    ALLOWED_TEMPLATE_EXTENSIONS = {'.html', '.docx', '.xlsx', '.pptx', '.txt'}
    
    # 允许的上传文件类型
    ALLOWED_UPLOAD_TYPES = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'text/html',  # .html
        'text/plain',  # .txt
        'image/png',  # .png
        'image/jpeg',  # .jpg, .jpeg
    }
    
    # 最大文件大小 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # 敏感字段列表
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'access_token',
        'refresh_token', 'private_key', 'credential', 'auth'
    }
    
    def __init__(self, template_base_dir: str):
        """
        初始化安全验证器
        
        Args:
            template_base_dir: 模板文件根目录
        """
        self.template_base_dir = Path(template_base_dir).resolve()
    
    def validate_template_path(self, template_path: str) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        验证模板路径（防止路径遍历攻击）
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            (是否有效, 错误信息, 解析后的绝对路径)
        """
        try:
            # 解析为绝对路径
            abs_path = (self.template_base_dir / template_path).resolve()
            
            # 检查是否在白名单目录内
            if not str(abs_path).startswith(str(self.template_base_dir)):
                return False, f"路径遍历攻击：{template_path} 不在允许的目录内", None
            
            # 检查文件是否存在
            if not abs_path.exists():
                return False, f"模板文件不存在：{template_path}", None
            
            # 检查是否为文件
            if not abs_path.is_file():
                return False, f"路径不是文件：{template_path}", None
            
            # 检查文件扩展名
            if abs_path.suffix.lower() not in self.ALLOWED_TEMPLATE_EXTENSIONS:
                return False, f"不支持的模板文件类型：{abs_path.suffix}", None
            
            return True, None, abs_path
            
        except Exception as e:
            return False, f"路径验证失败：{str(e)}", None
    
    def validate_file_type(self, file_path: str, expected_mime_type: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        验证文件类型
        
        Args:
            file_path: 文件路径
            expected_mime_type: 期望的MIME类型（可选）
            
        Returns:
            (是否有效, 错误信息)
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        
        # 猜测MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # 检查是否在允许列表中
        if mime_type not in self.ALLOWED_UPLOAD_TYPES:
            return False, f"不支持的文件类型：{mime_type} ({ext})"
        
        # 如果指定了期望类型，检查是否匹配
        if expected_mime_type and mime_type != expected_mime_type:
            return False, f"文件类型不匹配，期望：{expected_mime_type}，实际：{mime_type}"
        
        return True, None
    
    def validate_file_size(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > self.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"文件大小超限：{size_mb:.2f}MB（最大{max_mb:.0f}MB）"
            
            return True, None
            
        except Exception as e:
            return False, f"无法获取文件大小：{str(e)}"
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256）
            
        Returns:
            文件哈希值
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # 分块读取，避免大文件占用过多内存
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def validate_file_hash(
        self,
        file_path: str,
        expected_hash: str,
        algorithm: str = 'sha256'
    ) -> Tuple[bool, Optional[str]]:
        """
        验证文件哈希值
        
        Args:
            file_path: 文件路径
            expected_hash: 期望的哈希值
            algorithm: 哈希算法
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            actual_hash = self.calculate_file_hash(file_path, algorithm)
            
            if actual_hash != expected_hash:
                return False, f"文件哈希值不匹配，期望：{expected_hash}，实际：{actual_hash}"
            
            return True, None
            
        except Exception as e:
            return False, f"哈希验证失败：{str(e)}"
    
    def validate_file(
        self,
        file_path: str,
        check_size: bool = True,
        check_type: bool = True,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = 'sha256'
    ) -> Tuple[bool, List[str]]:
        """
        综合验证文件
        
        Args:
            file_path: 文件路径
            check_size: 是否检查文件大小
            check_type: 是否检查文件类型
            expected_hash: 期望的哈希值（可选）
            hash_algorithm: 哈希算法
            
        Returns:
            (是否全部通过, 错误信息列表)
        """
        errors = []
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, [f"文件不存在：{file_path}"]
        
        # 检查文件大小
        if check_size:
            valid, error = self.validate_file_size(file_path)
            if not valid:
                errors.append(error)
        
        # 检查文件类型
        if check_type:
            valid, error = self.validate_file_type(file_path)
            if not valid:
                errors.append(error)
        
        # 检查文件哈希
        if expected_hash:
            valid, error = self.validate_file_hash(file_path, expected_hash, hash_algorithm)
            if not valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def mask_sensitive_data(data: dict) -> dict:
        """
        脱敏处理敏感数据
        
        Args:
            data: 原始数据字典
            
        Returns:
            脱敏后的数据字典
        """
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # 检查是否为敏感字段
            is_sensitive = any(sensitive in key_lower for sensitive in SecurityValidator.SENSITIVE_FIELDS)
            
            if is_sensitive:
                # 脱敏处理
                if isinstance(value, str) and len(value) > 4:
                    masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_data[key] = '***'
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                masked_data[key] = SecurityValidator.mask_sensitive_data(value)
            elif isinstance(value, list):
                # 处理列表
                masked_data[key] = [
                    SecurityValidator.mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data


def demo_template_path_validation():
    """演示模板路径验证"""
    print("=" * 60)
    print("演示1: 模板路径白名单验证")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = Path("test_templates")
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文件
    test_file = test_dir / "report.html"
    test_file.write_text("<h1>Test Template</h1>")
    
    validator = SecurityValidator(template_base_dir="test_templates")
    
    # 测试用例1: 正常路径
    print("\n测试1: 正常模板路径")
    valid, error, path = validator.validate_template_path("report.html")
    print(f"  路径: report.html")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    if error:
        print(f"  错误: {error}")
    if path:
        print(f"  解析路径: {path}")
    
    # 测试用例2: 路径遍历攻击
    print("\n测试2: 路径遍历攻击")
    valid, error, path = validator.validate_template_path("../../../etc/passwd")
    print(f"  路径: ../../../etc/passwd")
    print(f"  结果: {'✓ 通过' if valid else '✗ 阻止'}")
    if error:
        print(f"  错误: {error}")
    
    # 测试用例3: 不存在的文件
    print("\n测试3: 不存在的文件")
    valid, error, path = validator.validate_template_path("nonexistent.html")
    print(f"  路径: nonexistent.html")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    if error:
        print(f"  错误: {error}")
    
    # 清理测试文件
    test_file.unlink()
    test_dir.rmdir()


def demo_file_validation():
    """演示文件验证"""
    print("\n" + "=" * 60)
    print("演示2: 文件类型和大小验证")
    print("=" * 60)
    
    # 创建测试文件
    test_file = Path("test_document.html")
    test_content = "<html><body><h1>Test Document</h1></body></html>"
    test_file.write_text(test_content)
    
    validator = SecurityValidator(template_base_dir=".")
    
    # 测试用例1: 文件类型验证
    print("\n测试1: 文件类型验证")
    valid, error = validator.validate_file_type(str(test_file))
    print(f"  文件: {test_file}")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    if error:
        print(f"  错误: {error}")
    
    # 测试用例2: 文件大小验证
    print("\n测试2: 文件大小验证")
    valid, error = validator.validate_file_size(str(test_file))
    print(f"  文件: {test_file}")
    print(f"  大小: {len(test_content)} bytes")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    if error:
        print(f"  错误: {error}")
    
    # 测试用例3: 综合验证
    print("\n测试3: 综合验证")
    valid, errors = validator.validate_file(str(test_file))
    print(f"  文件: {test_file}")
    print(f"  结果: {'✓ 全部通过' if valid else '✗ 存在问题'}")
    if errors:
        for err in errors:
            print(f"  - {err}")
    
    # 清理测试文件
    test_file.unlink()


def demo_hash_validation():
    """演示文件哈希校验"""
    print("\n" + "=" * 60)
    print("演示3: 文件哈希校验")
    print("=" * 60)
    
    # 创建测试文件
    test_file = Path("test_hash.txt")
    test_content = "This is a test file for hash validation."
    test_file.write_text(test_content)
    
    validator = SecurityValidator(template_base_dir=".")
    
    # 计算文件哈希
    file_hash = validator.calculate_file_hash(str(test_file))
    print(f"\n文件: {test_file}")
    print(f"内容: {test_content}")
    print(f"SHA256: {file_hash}")
    
    # 测试用例1: 正确的哈希值
    print("\n测试1: 正确的哈希值")
    valid, error = validator.validate_file_hash(str(test_file), file_hash)
    print(f"  期望哈希: {file_hash}")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    
    # 测试用例2: 错误的哈希值
    print("\n测试2: 错误的哈希值")
    wrong_hash = "0" * 64
    valid, error = validator.validate_file_hash(str(test_file), wrong_hash)
    print(f"  期望哈希: {wrong_hash}")
    print(f"  结果: {'✓ 通过' if valid else '✗ 失败'}")
    if error:
        print(f"  错误: {error}")
    
    # 清理测试文件
    test_file.unlink()


def demo_data_masking():
    """演示数据脱敏"""
    print("\n" + "=" * 60)
    print("演示4: 敏感数据脱敏")
    print("=" * 60)
    
    # 测试数据
    test_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secretpassword123",
        "api_key": "sk_live_1234567890abcdef",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "profile": {
            "name": "John Doe",
            "access_token": "at_1234567890",
            "refresh_token": "rt_0987654321"
        },
        "settings": {
            "theme": "dark",
            "language": "en"
        }
    }
    
    print("\n原始数据:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    # 脱敏处理
    masked_data = SecurityValidator.mask_sensitive_data(test_data)
    
    print("\n脱敏后数据:")
    for key, value in masked_data.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("\n🔒 安全验证功能演示\n")
    
    # 演示1: 模板路径验证
    demo_template_path_validation()
    
    # 演示2: 文件验证
    demo_file_validation()
    
    # 演示3: 哈希校验
    demo_hash_validation()
    
    # 演示4: 数据脱敏
    demo_data_masking()
    
    print("\n" + "=" * 60)
    print("✓ 所有演示完成")
    print("=" * 60)

