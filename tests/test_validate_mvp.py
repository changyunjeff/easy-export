"""
测试文档校验MVP功能
"""

import json
import pytest
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from mvp.validate_document import DocumentValidator, ValidationResult


class TestDocumentValidator:
    """测试DocumentValidator类"""
    
    @pytest.fixture
    def validator(self):
        """创建validator实例"""
        return DocumentValidator()
    
    @pytest.fixture
    def sample_html_file(self, tmp_path):
        """创建示例HTML文件"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试文档</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .content { font-family: Arial, sans-serif; }
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
            <a href="https://www.example.com">查看详情</a>
        </body>
        </html>
        """
        file_path = tmp_path / "test.html"
        file_path.write_text(html_content, encoding='utf-8')
        return str(file_path)
    
    @pytest.fixture
    def sample_rules(self):
        """创建示例校验规则"""
        return {
            "required_fields": ["张三", "订单号", "2024"],
            "expected_table_rows": 3,
            "check_links": False,
            "check_style": True
        }
    
    def test_validate_html_success(self, validator, sample_html_file, sample_rules):
        """测试HTML文档校验成功"""
        result = validator.validate(sample_html_file, sample_rules)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert len(result.errors) == 0
        assert result.summary['failed_checks'] == 0
    
    def test_validate_missing_required_field(self, validator, sample_html_file):
        """测试必填字段缺失"""
        rules = {
            "required_fields": ["张三", "订单号", "李四"],  # 李四不存在
            "check_links": False,
            "check_style": False
        }
        
        result = validator.validate(sample_html_file, rules)
        
        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0]['type'] == "missing_required_field"
        assert result.errors[0]['field'] == "李四"
    
    def test_validate_table_row_mismatch(self, validator, sample_html_file):
        """测试表格行数不匹配"""
        rules = {
            "expected_table_rows": 5,  # 实际只有3行
            "check_links": False,
            "check_style": False
        }
        
        result = validator.validate(sample_html_file, rules)
        
        assert len(result.warnings) > 0
        # 找到表格行数不匹配的警告
        table_warnings = [w for w in result.warnings if w['type'] == 'table_row_mismatch']
        assert len(table_warnings) == 1
        assert table_warnings[0]['detail']['expected'] == 5
        assert table_warnings[0]['detail']['actual'] == 3
    
    def test_validate_file_not_found(self, validator):
        """测试文件不存在"""
        rules = {"required_fields": []}
        result = validator.validate("nonexistent.html", rules)
        
        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0]['type'] == "file_not_found"
    
    def test_validate_unsupported_format(self, validator, tmp_path):
        """测试不支持的文件格式"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        rules = {"required_fields": []}
        result = validator.validate(str(file_path), rules)
        
        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0]['type'] == "unsupported_format"
    
    def test_validate_style_consistency(self, validator, tmp_path):
        """测试样式一致性检查"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <p style="font-family: Arial">Text 1</p>
            <p style="font-family: Times New Roman">Text 2</p>
            <p style="font-family: Courier">Text 3</p>
            <p style="font-family: Verdana">Text 4</p>
        </body>
        </html>
        """
        file_path = tmp_path / "test_styles.html"
        file_path.write_text(html_content, encoding='utf-8')
        
        rules = {
            "required_fields": [],
            "check_style": True
        }
        
        result = validator.validate(str(file_path), rules)
        
        # 应该有警告，因为使用了超过3种字体
        style_warnings = [w for w in result.warnings if w['type'] == 'inconsistent_fonts']
        assert len(style_warnings) == 1
    
    def test_validate_no_table(self, validator, tmp_path):
        """测试没有表格的文档"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <body>
            <p>没有表格的文档</p>
        </body>
        </html>
        """
        file_path = tmp_path / "no_table.html"
        file_path.write_text(html_content, encoding='utf-8')
        
        rules = {
            "expected_table_rows": 5,
            "check_links": False
        }
        
        result = validator.validate(str(file_path), rules)
        
        # 没有表格，所以不会有表格相关的警告
        table_warnings = [w for w in result.warnings if w['type'] == 'table_row_mismatch']
        assert len(table_warnings) == 0
    
    def test_validate_multiple_errors(self, validator, tmp_path):
        """测试多个错误"""
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
            "required_fields": ["字段1", "字段2", "字段3"],  # 这些都不存在
            "check_links": False
        }
        
        result = validator.validate(str(file_path), rules)
        
        assert result.passed is False
        assert len(result.errors) == 3  # 3个缺失字段
        assert result.summary['failed_checks'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

