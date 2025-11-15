"""
安全验证器
提供文件验证、路径验证、文件哈希校验等安全功能
"""

import os
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误异常"""
    pass


class SecurityValidator:
    """
    安全验证器
    
    功能:
    1. 模板路径白名单验证 - 防止路径遍历攻击
    2. 文件类型验证 - MIME类型和扩展名验证
    3. 文件大小限制 - 防止大文件攻击
    4. 文件哈希校验 - 确保文件完整性
    """
    
    # 允许的模板文件扩展名
    ALLOWED_TEMPLATE_EXTENSIONS = {'.html', '.docx', '.xlsx', '.pptx', '.txt', '.md'}
    
    # 允许的上传文件类型 (MIME类型)
    ALLOWED_UPLOAD_TYPES = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'text/html',  # .html
        'text/plain',  # .txt
        'text/markdown',  # .md
        'image/png',  # .png
        'image/jpeg',  # .jpg, .jpeg
        'image/gif',  # .gif
        'image/webp',  # .webp
        'application/pdf',  # .pdf
    }
    
    # 文件扩展名到MIME类型的映射 (处理mimetypes库无法识别的情况)
    EXTENSION_TO_MIME = {
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.html': 'text/html',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
    }
    
    # 最大文件大小 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, template_base_dir: str = "static/templates"):
        """
        初始化安全验证器
        
        Args:
            template_base_dir: 模板文件根目录
        """
        self.template_base_dir = Path(template_base_dir).resolve()
        logger.info(f"SecurityValidator initialized with base dir: {self.template_base_dir}")
    
    def validate_template_path(self, template_path: str) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        验证模板路径（防止路径遍历攻击）
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            (是否有效, 错误信息, 解析后的绝对路径)
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        try:
            # 解析为绝对路径
            abs_path = (self.template_base_dir / template_path).resolve()
            
            # 检查是否在白名单目录内
            if not str(abs_path).startswith(str(self.template_base_dir)):
                error_msg = f"路径遍历攻击：{template_path} 不在允许的目录内"
                logger.warning(f"Path traversal attack detected: {template_path}")
                return False, error_msg, None
            
            # 检查文件是否存在
            if not abs_path.exists():
                error_msg = f"模板文件不存在：{template_path}"
                logger.warning(f"Template file not found: {template_path}")
                return False, error_msg, None
            
            # 检查是否为文件
            if not abs_path.is_file():
                error_msg = f"路径不是文件：{template_path}"
                logger.warning(f"Path is not a file: {template_path}")
                return False, error_msg, None
            
            # 检查文件扩展名
            if abs_path.suffix.lower() not in self.ALLOWED_TEMPLATE_EXTENSIONS:
                error_msg = f"不支持的模板文件类型：{abs_path.suffix}"
                logger.warning(f"Unsupported template extension: {abs_path.suffix}")
                return False, error_msg, None
            
            logger.debug(f"Template path validation passed: {template_path} -> {abs_path}")
            return True, None, abs_path
            
        except Exception as e:
            error_msg = f"路径验证失败：{str(e)}"
            logger.error(f"Path validation error: {str(e)}", exc_info=True)
            return False, error_msg, None
    
    def validate_file_type(
        self,
        file_path: str,
        expected_mime_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
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
        ext_lower = ext.lower()
        
        # 首先尝试通过扩展名映射获取MIME类型
        mime_type = self.EXTENSION_TO_MIME.get(ext_lower)
        
        # 如果映射表中没有，尝试使用mimetypes库
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_path)
        
        # 检查MIME类型是否为None
        if not mime_type:
            error_msg = f"无法识别的文件类型：{ext}"
            logger.warning(f"Unknown file type: {ext}")
            return False, error_msg
        
        # 检查是否在允许列表中
        if mime_type not in self.ALLOWED_UPLOAD_TYPES:
            error_msg = f"不支持的文件类型：{mime_type} ({ext})"
            logger.warning(f"Unsupported file type: {mime_type} ({ext})")
            return False, error_msg
        
        # 如果指定了期望类型，检查是否匹配
        if expected_mime_type and mime_type != expected_mime_type:
            error_msg = f"文件类型不匹配，期望：{expected_mime_type}，实际：{mime_type}"
            logger.warning(f"File type mismatch: expected {expected_mime_type}, got {mime_type}")
            return False, error_msg
        
        logger.debug(f"File type validation passed: {file_path} -> {mime_type}")
        return True, None
    
    def validate_file_size(self, file_path: str, max_size: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        验证文件大小
        
        Args:
            file_path: 文件路径
            max_size: 最大文件大小（字节），None则使用默认值
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            file_size = os.path.getsize(file_path)
            max_allowed = max_size if max_size is not None else self.MAX_FILE_SIZE
            
            if file_size > max_allowed:
                size_mb = file_size / (1024 * 1024)
                max_mb = max_allowed / (1024 * 1024)
                error_msg = f"文件大小超限：{size_mb:.2f}MB（最大{max_mb:.0f}MB）"
                logger.warning(f"File size exceeded: {size_mb:.2f}MB > {max_mb:.0f}MB")
                return False, error_msg
            
            logger.debug(f"File size validation passed: {file_path} ({file_size} bytes)")
            return True, None
            
        except Exception as e:
            error_msg = f"无法获取文件大小：{str(e)}"
            logger.error(f"File size check error: {str(e)}", exc_info=True)
            return False, error_msg
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256）
            
        Returns:
            文件哈希值
            
        Raises:
            ValueError: 不支持的哈希算法
            FileNotFoundError: 文件不存在
        """
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                # 分块读取，避免大文件占用过多内存
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            file_hash = hash_func.hexdigest()
            logger.debug(f"File hash calculated: {file_path} -> {algorithm}:{file_hash}")
            return file_hash
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except ValueError as e:
            logger.error(f"Unsupported hash algorithm: {algorithm}")
            raise ValueError(f"不支持的哈希算法：{algorithm}") from e
        except Exception as e:
            logger.error(f"Hash calculation error: {str(e)}", exc_info=True)
            raise
    
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
            
            if actual_hash.lower() != expected_hash.lower():
                error_msg = f"文件哈希值不匹配，期望：{expected_hash}，实际：{actual_hash}"
                logger.warning(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")
                return False, error_msg
            
            logger.debug(f"File hash validation passed: {file_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"哈希验证失败：{str(e)}"
            logger.error(f"Hash validation error: {str(e)}", exc_info=True)
            return False, error_msg
    
    def validate_file(
        self,
        file_path: str,
        check_size: bool = True,
        check_type: bool = True,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = 'sha256',
        max_size: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        综合验证文件
        
        Args:
            file_path: 文件路径
            check_size: 是否检查文件大小
            check_type: 是否检查文件类型
            expected_hash: 期望的哈希值（可选）
            hash_algorithm: 哈希算法
            max_size: 最大文件大小（字节）
            
        Returns:
            (是否全部通过, 错误信息列表)
        """
        errors = []
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"文件不存在：{file_path}"
            logger.warning(f"File not found: {file_path}")
            return False, [error_msg]
        
        # 检查文件大小
        if check_size:
            valid, error = self.validate_file_size(file_path, max_size)
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
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"File validation passed: {file_path}")
        else:
            logger.warning(f"File validation failed: {file_path}, errors: {errors}")
        
        return is_valid, errors
    
    def validate_upload_file(
        self,
        file_path: str,
        expected_mime_type: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> Dict[str, any]:
        """
        验证上传文件（综合接口）
        
        Args:
            file_path: 文件路径
            expected_mime_type: 期望的MIME类型
            max_size: 最大文件大小（字节）
            
        Returns:
            验证结果字典:
            {
                "valid": bool,
                "errors": List[str],
                "file_info": {
                    "size": int,
                    "mime_type": str,
                    "hash": str
                }
            }
        """
        result = {
            "valid": True,
            "errors": [],
            "file_info": {}
        }
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            result["valid"] = False
            result["errors"].append(f"文件不存在：{file_path}")
            return result
        
        # 获取文件信息
        try:
            file_size = os.path.getsize(file_path)
            result["file_info"]["size"] = file_size
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"无法获取文件大小：{str(e)}")
            return result
        
        # 验证文件大小
        valid, error = self.validate_file_size(file_path, max_size)
        if not valid:
            result["valid"] = False
            result["errors"].append(error)
        
        # 验证文件类型
        valid, error = self.validate_file_type(file_path, expected_mime_type)
        if not valid:
            result["valid"] = False
            result["errors"].append(error)
        else:
            # 获取MIME类型
            ext_lower = os.path.splitext(file_path)[1].lower()
            mime_type = self.EXTENSION_TO_MIME.get(ext_lower) or mimetypes.guess_type(file_path)[0]
            result["file_info"]["mime_type"] = mime_type
        
        # 计算文件哈希
        try:
            file_hash = self.calculate_file_hash(file_path)
            result["file_info"]["hash"] = file_hash
        except Exception as e:
            logger.warning(f"Failed to calculate file hash: {str(e)}")
            # 哈希计算失败不阻止验证通过
        
        if result["valid"]:
            logger.info(f"Upload file validation passed: {file_path}")
        else:
            logger.warning(f"Upload file validation failed: {file_path}, errors: {result['errors']}")
        
        return result


# 全局实例
_security_validator: Optional[SecurityValidator] = None


def get_security_validator() -> SecurityValidator:
    """获取安全验证器全局实例"""
    global _security_validator
    if _security_validator is None:
        _security_validator = SecurityValidator()
    return _security_validator

