"""
测试ValidateService服务层功能
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.service.validate_service import (
    ValidateService,
    ValidationError,
    ValidationWarning,
    ValidationResult
)


class TestValidationError:
    """测试ValidationError类"""
    
    def test_create_error_with_field(self):
        """测试创建带字段的错误"""
        error = ValidationError(
            type="missing_field",
            message="字段缺失",
            field="user_name"
        )
        
        assert error.type == "missing_field"
        assert error.message == "字段缺失"
        assert error.field == "user_name"
        assert error.detail == {}
    
    def test_create_error_with_detail(self):
        """测试创建带详情的错误"""
        error = ValidationError(
            type="validation_error",
            message="校验失败",
            detail={"expected": 10, "actual": 5}
        )
        
        assert error.type == "validation_error"
        assert error.message == "校验失败"
        assert error.detail == {"expected": 10, "actual": 5}
    
    def test_to_dict(self):
        """测试转换为字典"""
        error = ValidationError(
            type="test_error",
            message="测试错误",
            field="test_field",
            detail={"key": "value"}
        )
        
        result = error.to_dict()
        
        assert result["type"] == "test_error"
        assert result["message"] == "测试错误"
        assert result["field"] == "test_field"
        assert result["detail"] == {"key": "value"}


class TestValidationWarning:
    """测试ValidationWarning类"""
    
    def test_create_warning(self):
        """测试创建警告"""
        warning = ValidationWarning(
            type="style_warning",
            message="样式不一致"
        )
        
        assert warning.type == "style_warning"
        assert warning.message == "样式不一致"
        assert warning.detail == {}
    
    def test_to_dict(self):
        """测试转换为字典"""
        warning = ValidationWarning(
            type="test_warning",
            message="测试警告",
            detail={"info": "test"}
        )
        
        result = warning.to_dict()
        
        assert result["type"] == "test_warning"
        assert result["message"] == "测试警告"
        assert result["detail"] == {"info": "test"}


class TestValidationResult:
    """测试ValidationResult类"""
    
    def test_create_passed_result(self):
        """测试创建通过的结果"""
        result = ValidationResult(passed=True)
        
        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_create_failed_result(self):
        """测试创建失败的结果"""
        error = ValidationError(type="error", message="错误")
        result = ValidationResult(passed=False, errors=[error])
        
        assert result.passed is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 0
    
    def test_to_dict(self):
        """测试转换为字典"""
        error = ValidationError(type="error", message="错误")
        warning = ValidationWarning(type="warning", message="警告")
        result = ValidationResult(
            passed=False,
            errors=[error],
            warnings=[warning]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["passed"] is False
        assert len(result_dict["errors"]) == 1
        assert len(result_dict["warnings"]) == 1
        assert result_dict["summary"]["total_checks"] == 2
        assert result_dict["summary"]["failed_checks"] == 1
        assert result_dict["summary"]["warning_checks"] == 1


class TestValidateService:
    """测试ValidateService类"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return ValidateService()
    
    @pytest.fixture
    def sample_html_file(self, tmp_path):
        """创建示例HTML文件"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>订单确认</title>
            <style>
                body { font-family: Arial, sans-serif; }
            </style>
        </head>
        <body>
            <h1>订单确认</h1>
            <p>客户姓名: 张三</p>
            <p>订单号: ORD-2024-001</p>
            <p>日期: 2024-01-01</p>
            <table>
                <tr><th>产品</th><th>数量</th><th>价格</th></tr>
                <tr><td>产品A</td><td>1</td><td>100</td></tr>
                <tr><td>产品B</td><td>2</td><td>200</td></tr>
                <tr><td>产品C</td><td>3</td><td>300</td></tr>
            </table>
        </body>
        </html>
        """
        file_path = tmp_path / "test.html"
        file_path.write_text(html_content, encoding='utf-8')
        return str(file_path)
    
    def test_validate_document_success(self, service, sample_html_file):
        """测试文档校验成功"""
        rules = {
            "required_fields": ["张三", "订单号", "2024"],
            "expected_table_rows": 3
        }
        
        result = service.validate_document(sample_html_file, rules)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert len(result.errors) == 0
    
    def test_validate_document_missing_required_field(self, service, sample_html_file):
        """测试必填字段缺失"""
        rules = {
            "required_fields": ["张三", "李四", "王五"]
        }
        
        result = service.validate_document(sample_html_file, rules)
        
        assert result.passed is False
        assert len(result.errors) == 2  # 李四和王五不存在
        
        error_fields = [e.field for e in result.errors]
        assert "李四" in error_fields
        assert "王五" in error_fields
    
    def test_validate_document_table_row_mismatch(self, service, sample_html_file):
        """测试表格行数不匹配"""
        rules = {
            "expected_table_rows": 10
        }
        
        result = service.validate_document(sample_html_file, rules)
        
        # 表格行数不匹配是警告，不是错误
        assert result.passed is True
        assert len(result.warnings) > 0
        
        # 检查警告类型
        warning_types = [w.type for w in result.warnings]
        assert "table_row_mismatch" in warning_types
    
    def test_validate_document_file_not_found(self, service):
        """测试文件不存在"""
        rules = {"required_fields": []}
        
        with pytest.raises(FileNotFoundError):
            service.validate_document("nonexistent.html", rules)
    
    def test_validate_document_unsupported_format(self, service, tmp_path):
        """测试不支持的文件格式"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        rules = {"required_fields": []}
        
        with pytest.raises(ValueError):
            service.validate_document(str(file_path), rules)
    
    def test_check_data_alignment(self, service):
        """测试数据对齐检查"""
        content = "张三 订单号 2024"
        data = {
            "required_fields": ["张三", "李四"],
            "expected_table_rows": 3
        }
        
        errors = service.check_data_alignment(content, data)
        
        # 应该有1个错误（李四不存在）
        assert len(errors) == 1
        assert errors[0].field == "李四"
    
    def test_check_style_consistency(self, service):
        """测试样式一致性检查"""
        # HTML内容使用了4种不同的字体
        content = """
        <p style="font-family: Arial">Text 1</p>
        <p style="font-family: Times New Roman">Text 2</p>
        <p style="font-family: Courier">Text 3</p>
        <p style="font-family: Verdana">Text 4</p>
        """
        
        warnings = service.check_style_consistency(content)
        
        # 应该有警告，因为使用了超过3种字体
        assert len(warnings) > 0
        assert warnings[0].type == "inconsistent_fonts"
    
    def test_check_style_consistency_no_warning(self, service):
        """测试样式一致性检查 - 无警告"""
        # HTML内容使用了相同的字体
        content = """
        <p style="font-family: Arial">Text 1</p>
        <p style="font-family: Arial">Text 2</p>
        """
        
        warnings = service.check_style_consistency(content)
        
        # 不应该有警告
        assert len(warnings) == 0
    
    def test_validate_document_with_style_check(self, service, tmp_path):
        """测试带样式检查的文档校验"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <p style="font-family: Arial">Text 1</p>
            <p style="font-family: Times">Text 2</p>
            <p style="font-family: Courier">Text 3</p>
            <p style="font-family: Verdana">Text 4</p>
        </body>
        </html>
        """
        file_path = tmp_path / "test_style.html"
        file_path.write_text(html_content, encoding='utf-8')
        
        rules = {
            "check_style": True
        }
        
        result = service.validate_document(str(file_path), rules)
        
        # 应该有样式警告
        style_warnings = [w for w in result.warnings if w.type == "inconsistent_fonts"]
        assert len(style_warnings) > 0
    
    def test_validate_document_empty_rules(self, service, sample_html_file):
        """测试空规则的文档校验"""
        rules = {}
        
        result = service.validate_document(sample_html_file, rules)
        
        # 没有规则，应该直接通过
        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_validate_document_multiple_checks(self, service, tmp_path):
        """测试多项检查"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <p>只有这一句话</p>
        </body>
        </html>
        """
        file_path = tmp_path / "minimal.html"
        file_path.write_text(html_content, encoding='utf-8')
        
        rules = {
            "required_fields": ["字段1", "字段2", "字段3"],
            "expected_table_rows": 5,
            "check_style": True
        }
        
        result = service.validate_document(str(file_path), rules)
        
        # 应该有3个错误（3个缺失字段）
        assert result.passed is False
        assert len(result.errors) == 3
        
        # 表格不存在，所以没有表格相关的警告
        table_warnings = [w for w in result.warnings if w.type == "table_row_mismatch"]
        assert len(table_warnings) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

