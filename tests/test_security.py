"""
安全功能测试
测试SecurityValidator和DataMasker功能
"""

import os
import tempfile
import hashlib
import pytest
from pathlib import Path

from core.security.validator import SecurityValidator, get_security_validator, ValidationError
from core.security.masking import DataMasker, get_data_masker, mask_sensitive_data


class TestSecurityValidator:
    """测试SecurityValidator"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时测试目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def validator(self, temp_dir):
        """创建SecurityValidator实例"""
        return SecurityValidator(template_base_dir=temp_dir)
    
    @pytest.fixture
    def test_file(self, temp_dir):
        """创建测试文件"""
        file_path = Path(temp_dir) / "test.html"
        file_path.write_text("<h1>Test</h1>")
        return str(file_path.relative_to(temp_dir))
    
    def test_validate_template_path_valid(self, validator, temp_dir, test_file):
        """测试有效的模板路径"""
        valid, error, abs_path = validator.validate_template_path(test_file)
        
        assert valid is True
        assert error is None
        assert abs_path is not None
        assert abs_path.exists()
    
    def test_validate_template_path_traversal_attack(self, validator):
        """测试路径遍历攻击"""
        valid, error, abs_path = validator.validate_template_path("../../../etc/passwd")
        
        assert valid is False
        assert "路径遍历攻击" in error or "不在允许的目录内" in error
        assert abs_path is None
    
    def test_validate_template_path_not_exist(self, validator):
        """测试不存在的文件"""
        valid, error, abs_path = validator.validate_template_path("nonexistent.html")
        
        assert valid is False
        assert "不存在" in error
        assert abs_path is None
    
    def test_validate_template_path_invalid_extension(self, validator, temp_dir):
        """测试不支持的文件扩展名"""
        # 创建不支持的文件类型
        invalid_file = Path(temp_dir) / "test.exe"
        invalid_file.write_text("exe content")
        
        valid, error, abs_path = validator.validate_template_path("test.exe")
        
        assert valid is False
        assert "不支持的模板文件类型" in error
        assert abs_path is None
    
    def test_validate_file_type_html(self, temp_dir):
        """测试HTML文件类型验证"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.html"
        file_path.write_text("<html></html>")
        
        valid, error = validator.validate_file_type(str(file_path))
        
        assert valid is True
        assert error is None
    
    def test_validate_file_type_docx(self, temp_dir):
        """测试DOCX文件类型验证"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.docx"
        file_path.write_bytes(b"fake docx content")
        
        valid, error = validator.validate_file_type(str(file_path))
        
        assert valid is True
        assert error is None
    
    def test_validate_file_type_invalid(self, temp_dir):
        """测试无效文件类型"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.xyz"
        file_path.write_text("unknown type")
        
        valid, error = validator.validate_file_type(str(file_path))
        
        assert valid is False
        assert "无法识别" in error or "不支持" in error
    
    def test_validate_file_size_valid(self, temp_dir):
        """测试有效的文件大小"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("small file")
        
        valid, error = validator.validate_file_size(str(file_path))
        
        assert valid is True
        assert error is None
    
    def test_validate_file_size_exceeded(self, temp_dir):
        """测试文件大小超限"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.txt"
        
        # 创建一个小文件，但设置很小的最大大小
        file_path.write_text("test content")
        
        valid, error = validator.validate_file_size(str(file_path), max_size=5)
        
        assert valid is False
        assert "大小超限" in error
    
    def test_calculate_file_hash(self, temp_dir):
        """测试计算文件哈希"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.txt"
        content = b"test content for hashing"
        file_path.write_bytes(content)
        
        # 计算文件哈希
        file_hash = validator.calculate_file_hash(str(file_path), algorithm='sha256')
        
        # 验证哈希值
        expected_hash = hashlib.sha256(content).hexdigest()
        assert file_hash == expected_hash
    
    def test_validate_file_hash_valid(self, temp_dir):
        """测试有效的文件哈希"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.txt"
        content = b"test content"
        file_path.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        valid, error = validator.validate_file_hash(str(file_path), expected_hash)
        
        assert valid is True
        assert error is None
    
    def test_validate_file_hash_mismatch(self, temp_dir):
        """测试文件哈希不匹配"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.txt"
        file_path.write_text("test content")
        
        wrong_hash = "0" * 64
        
        valid, error = validator.validate_file_hash(str(file_path), wrong_hash)
        
        assert valid is False
        assert "哈希值不匹配" in error
    
    def test_validate_file_comprehensive(self, temp_dir):
        """测试综合文件验证"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "test.html"
        content = "<html><body>Test</body></html>"
        file_path.write_text(content)
        
        # 计算期望的哈希值
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        
        valid, errors = validator.validate_file(
            str(file_path),
            check_size=True,
            check_type=True,
            expected_hash=expected_hash
        )
        
        assert valid is True
        assert len(errors) == 0
    
    def test_validate_upload_file(self, temp_dir):
        """测试上传文件验证"""
        validator = SecurityValidator()
        file_path = Path(temp_dir) / "upload.docx"
        file_path.write_bytes(b"fake docx content")
        
        result = validator.validate_upload_file(str(file_path))
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "file_info" in result
        assert "size" in result["file_info"]
        assert "hash" in result["file_info"]
    
    def test_validate_upload_file_not_exist(self):
        """测试上传不存在的文件"""
        validator = SecurityValidator()
        
        result = validator.validate_upload_file("nonexistent.txt")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "不存在" in result["errors"][0]
    
    def test_get_security_validator_singleton(self):
        """测试获取SecurityValidator单例"""
        validator1 = get_security_validator()
        validator2 = get_security_validator()
        
        assert validator1 is validator2


class TestDataMasker:
    """测试DataMasker"""
    
    @pytest.fixture
    def masker(self):
        """创建DataMasker实例"""
        return DataMasker()
    
    def test_is_sensitive_key(self, masker):
        """测试敏感键名识别"""
        assert masker.is_sensitive_key("password") is True
        assert masker.is_sensitive_key("api_key") is True
        assert masker.is_sensitive_key("access_token") is True
        assert masker.is_sensitive_key("username") is False
        assert masker.is_sensitive_key("email") is False
    
    def test_is_sensitive_value_jwt(self, masker):
        """测试JWT Token识别"""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        
        assert masker.is_sensitive_value(jwt_token) is True
        assert masker.is_sensitive_value("normal text") is False
    
    def test_is_sensitive_value_api_key(self, masker):
        """测试API Key识别"""
        api_key = "sk_live_1234567890abcdefghijklmnopqrstuvwxyz"
        
        assert masker.is_sensitive_value(api_key) is True
    
    def test_mask_string(self, masker):
        """测试字符串脱敏"""
        masked = masker.mask_string("secretpassword123", keep_length=2)
        
        assert masked.startswith("se")
        assert masked.endswith("23")
        assert "*" in masked
        assert len(masked) == len("secretpassword123")
    
    def test_mask_string_short(self, masker):
        """测试短字符串脱敏"""
        masked = masker.mask_string("pwd")
        
        assert masked == "***"
    
    def test_mask_email(self, masker):
        """测试邮箱脱敏"""
        masked = masker.mask_email("john.doe@example.com")
        
        assert masked.startswith("j")
        assert masked.endswith("e@example.com")
        assert "*" in masked
        assert "@" in masked
    
    def test_mask_phone(self, masker):
        """测试手机号脱敏"""
        masked = masker.mask_phone("13812345678")
        
        assert masked.startswith("138")
        assert masked.endswith("5678")
        assert "*" in masked
    
    def test_mask_id_card(self, masker):
        """测试身份证号脱敏"""
        masked = masker.mask_id_card("123456789012345678")
        
        assert masked.startswith("1234")
        assert masked.endswith("5678")
        assert "*" in masked
    
    def test_mask_value_email_field(self, masker):
        """测试根据字段名脱敏邮箱"""
        masked = masker.mask_value("john@example.com", "user_email")
        
        assert "@" in masked
        assert "*" in masked
    
    def test_mask_value_phone_field(self, masker):
        """测试根据字段名脱敏手机号"""
        masked = masker.mask_value("13812345678", "phone_number")
        
        assert masked.startswith("138")
        assert "*" in masked
    
    def test_mask_dict_simple(self, masker):
        """测试简单字典脱敏"""
        data = {
            "username": "john_doe",
            "password": "secretpassword123",
            "api_key": "sk_live_abcdefghijk1234567890",
        }
        
        masked = masker.mask_dict(data)
        
        assert masked["username"] == "john_doe"
        assert masked["password"] != "secretpassword123"
        assert "*" in masked["password"]
        assert masked["api_key"] != "sk_live_abcdefghijk1234567890"
        assert "*" in masked["api_key"]
    
    def test_mask_dict_nested(self, masker):
        """测试嵌套字典脱敏"""
        data = {
            "user": {
                "name": "John Doe",
                "password": "secret123",
                "profile": {
                    "access_token": "token_123456",
                }
            }
        }
        
        masked = masker.mask_dict(data)
        
        assert masked["user"]["name"] == "John Doe"
        assert "*" in masked["user"]["password"]
        assert "*" in masked["user"]["profile"]["access_token"]
    
    def test_mask_list(self, masker):
        """测试列表脱敏"""
        data = [
            {"name": "User 1", "password": "pass1"},
            {"name": "User 2", "token": "token_xyz"},
        ]
        
        masked = masker.mask_list(data)
        
        assert masked[0]["name"] == "User 1"
        assert "*" in masked[0]["password"]
        assert masked[1]["name"] == "User 2"
        assert "*" in masked[1]["token"]
    
    def test_mask_data_dict(self, masker):
        """测试mask_data处理字典"""
        data = {
            "username": "john",
            "password": "secret",
        }
        
        masked = masker.mask_data(data)
        
        assert isinstance(masked, dict)
        assert "*" in masked["password"]
    
    def test_mask_data_list(self, masker):
        """测试mask_data处理列表"""
        data = [
            {"password": "secret1"},
            {"password": "secret2"},
        ]
        
        masked = masker.mask_data(data)
        
        assert isinstance(masked, list)
        assert "*" in masked[0]["password"]
    
    def test_mask_log_message(self, masker):
        """测试日志消息脱敏"""
        message = "User login with token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        
        masked = masker.mask_log_message(message)
        
        assert "token:" in masked
        assert "*" in masked
        # JWT Token应该被脱敏
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked or "*" in masked
    
    def test_get_data_masker_singleton(self):
        """测试获取DataMasker单例"""
        masker1 = get_data_masker()
        masker2 = get_data_masker()
        
        assert masker1 is masker2
    
    def test_mask_sensitive_data_function(self):
        """测试mask_sensitive_data便捷函数"""
        data = {
            "username": "john",
            "password": "secret123",
        }
        
        masked = mask_sensitive_data(data)
        
        assert masked["username"] == "john"
        assert "*" in masked["password"]
    
    def test_custom_keywords(self):
        """测试自定义敏感关键词"""
        masker = DataMasker(custom_keywords={"ssn", "credit_card"})
        
        data = {
            "name": "John",
            "ssn": "123-45-6789",
            "credit_card": "1234-5678-9012-3456",
        }
        
        masked = masker.mask_dict(data)
        
        assert masked["name"] == "John"
        assert "*" in masked["ssn"]
        assert "*" in masked["credit_card"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

