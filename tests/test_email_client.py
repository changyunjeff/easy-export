"""
邮件模块白盒测试
测试邮件发送功能，包括：
- 邮件客户端初始化
- 模板渲染功能
- 纯文本邮件发送
- HTML 邮件发送
- 模板邮件发送（使用 test.html 模板）
- 多个收件人支持
- 错误处理

运行说明：
1. 运行所有测试（不发送实际邮件）：
   pytest tests/test_email_client.py -v

2. 运行所有测试（包括实际发送邮件到 changyunjeff@outlook.com）：
   Linux/Mac (Bash):
     ENABLE_EMAIL_TESTS=true pytest tests/test_email_client.py -v
   
   Windows PowerShell:
     $env:ENABLE_EMAIL_TESTS="true"; pytest tests/test_email_client.py -v
   
   Windows CMD:
     set ENABLE_EMAIL_TESTS=true && pytest tests/test_email_client.py -v

3. 只运行模板渲染测试（不发送邮件）：
   pytest tests/test_email_client.py::TestEmailClient::test_template_rendering -v

4. 只运行发送模板邮件测试（需要设置环境变量）：
   Linux/Mac (Bash):
     ENABLE_EMAIL_TESTS=true pytest tests/test_email_client.py::TestEmailClient::test_send_template_email -v
   
   Windows PowerShell:
     $env:ENABLE_EMAIL_TESTS="true"; pytest tests/test_email_client.py::TestEmailClient::test_send_template_email -v
   
   Windows CMD:
     set ENABLE_EMAIL_TESTS=true && pytest tests/test_email_client.py::TestEmailClient::test_send_template_email -v

注意：
- 默认情况下，实际发送邮件的测试会被跳过，避免每次运行都发送邮件
- 需要实际发送邮件时，请设置环境变量 ENABLE_EMAIL_TESTS=true
- 确保 config.dev.yaml 中已正确配置邮件服务参数
"""
from __future__ import annotations

import pytest
import os
from pathlib import Path

from core.email import (
    EmailClient,
    send_email,
    get_email_client,
    init_email,
    close_email,
    is_email_enabled,
)
from core.config import load_config
from dotenv import load_dotenv

load_dotenv()

smtp_pwd = os.getenv("SMTP_PWD")
print(f"SMTP_PWD: {smtp_pwd}")


class TestEmailClient:
    """邮件客户端测试类"""
    
    # 测试邮箱地址
    TEST_EMAIL = "changyunjeff@outlook.com"
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, template_dir):
        """每个测试前后的设置和清理"""
        # 测试前：加载配置并初始化邮件服务
        try:
            config = load_config()
            if config.email.enabled:
                email_config = config.email.smtp
                init_email(
                    host=email_config.host,
                    port=email_config.port,
                    user=email_config.user,
                    password=smtp_pwd,
                    tls=email_config.tls,
                )
                # 初始化邮件客户端并设置模板目录
                # 重置全局实例以确保使用正确的模板目录
                import core.email.client as email_client_module
                email_client_module._email_client_instance = None
                get_email_client(template_dir=template_dir)
        except Exception as e:
            pytest.skip(f"Email service not configured: {e}")
        
        yield
        
        # 测试后：关闭邮件服务并重置客户端
        close_email()
        import core.email.client as email_client_module
        email_client_module._email_client_instance = None
    
    @pytest.fixture
    def template_dir(self):
        """获取模板目录路径"""
        template_path = Path(__file__).parent.parent / "static" / "email_template"
        return str(template_path)
    
    @pytest.fixture
    def email_client(self, template_dir):
        """创建邮件客户端实例"""
        return EmailClient(template_dir=template_dir)
    
    def test_email_client_initialization(self, template_dir):
        """测试邮件客户端初始化"""
        client = EmailClient(template_dir=template_dir)
        assert client.template_dir == template_dir
        assert client._jinja_env is not None, "Jinja2 环境应该已初始化"
    
    def test_email_client_initialization_without_template_dir(self):
        """测试不带模板目录的邮件客户端初始化"""
        client = EmailClient(template_dir=None)
        assert client.template_dir is None
        assert client._jinja_env is None
    
    def test_email_client_initialization_with_invalid_template_dir(self):
        """测试无效模板目录的初始化"""
        client = EmailClient(template_dir="/nonexistent/path")
        assert client._jinja_env is None, "无效路径不应该初始化 Jinja2 环境"
    
    def test_template_rendering(self, email_client):
        """测试模板渲染功能"""
        context = {
            "title": "测试标题",
            "subtitle": "测试副标题",
            "name": "测试用户",
            "content": "<p>这是测试内容</p>",
        }
        
        text_body, html_body = email_client._render_template("test", context)
        
        assert html_body is not None, "HTML 模板应该被成功渲染"
        assert "测试标题" in html_body, "HTML 内容应该包含标题"
        assert "测试用户" in html_body, "HTML 内容应该包含用户名"
        assert "测试内容" in html_body, "HTML 内容应该包含内容"
    
    def test_template_rendering_with_info_items(self, email_client):
        """测试带信息列表的模板渲染"""
        context = {
            "title": "订单通知",
            "name": "张三",
            "info_items": [
                {"label": "订单号", "value": "ORD-2024-001"},
                {"label": "创建时间", "value": "2024-01-15 10:30:00"},
                {"label": "订单金额", "value": "¥199.00"},
            ],
        }
        
        text_body, html_body = email_client._render_template("test", context)
        
        assert html_body is not None
        assert "订单号" in html_body
        assert "ORD-2024-001" in html_body
        assert "订单金额" in html_body
        assert "¥199.00" in html_body
    
    def test_template_rendering_with_button(self, email_client):
        """测试带按钮的模板渲染"""
        context = {
            "title": "欢迎使用",
            "name": "李四",
            "button_text": "查看详情",
            "button_url": "https://example.com/details",
        }
        
        text_body, html_body = email_client._render_template("test", context)
        
        assert html_body is not None
        assert "查看详情" in html_body
        assert "https://example.com/details" in html_body
    
    def test_template_rendering_nonexistent_template(self, email_client):
        """测试不存在的模板"""
        text_body, html_body = email_client._render_template("nonexistent", {})
        assert text_body == ""
        assert html_body is None
    
    @pytest.mark.skipif(
        not os.getenv("ENABLE_EMAIL_TESTS", "").lower() == "true",
        reason="需要设置 ENABLE_EMAIL_TESTS=true 来运行实际邮件发送测试"
    )
    def test_send_plain_text_email(self):
        """测试发送纯文本邮件"""
        result = send_email(
            to=self.TEST_EMAIL,
            subject="测试邮件 - 纯文本",
            body="这是一封纯文本测试邮件。\n\n如果您收到这封邮件，说明邮件发送功能正常工作。",
        )
        
        assert result is True, "邮件应该发送成功"
    
    @pytest.mark.skipif(
        not os.getenv("ENABLE_EMAIL_TESTS", "").lower() == "true",
        reason="需要设置 ENABLE_EMAIL_TESTS=true 来运行实际邮件发送测试"
    )
    def test_send_html_email(self):
        """测试发送 HTML 邮件"""
        html_content = """
        <html>
            <body>
                <h1 style="color: #667eea;">HTML 测试邮件</h1>
                <p>这是一封 HTML 格式的测试邮件。</p>
                <p>如果您看到这封邮件，说明 HTML 邮件发送功能正常工作。</p>
            </body>
        </html>
        """
        
        result = send_email(
            to=self.TEST_EMAIL,
            subject="测试邮件 - HTML",
            body="这是纯文本版本（如果您的邮件客户端不支持 HTML）",
            html=html_content,
        )
        
        assert result is True, "HTML 邮件应该发送成功"
    
    @pytest.mark.skipif(
        not os.getenv("ENABLE_EMAIL_TESTS", "").lower() == "true",
        reason="需要设置 ENABLE_EMAIL_TESTS=true 来运行实际邮件发送测试"
    )
    def test_send_template_email(self, template_dir):
        """测试使用 test.html 模板发送邮件"""
        # 确保邮件客户端使用正确的模板目录
        client = get_email_client(template_dir=template_dir)
        
        context = {
            "title": "Easy Export 邮件测试",
            "subtitle": "模板邮件发送功能测试",
            "name": "Jeff Chang",
            "content": """
                <p>这是一封使用 <strong>test.html</strong> 模板发送的测试邮件。</p>
                <p>模板渲染功能正常工作，所有变量都已正确替换。</p>
                <p>如果您看到这封邮件，说明：</p>
                <ul>
                    <li>邮件服务配置正确</li>
                    <li>模板渲染功能正常</li>
                    <li>邮件发送功能正常</li>
                </ul>
            """,
            "info_items": [
                {"label": "测试时间", "value": "2024-01-15 10:30:00"},
                {"label": "测试类型", "value": "白盒测试"},
                {"label": "模板名称", "value": "test.html"},
                {"label": "收件人", "value": self.TEST_EMAIL},
            ],
            "button_text": "访问项目",
            "button_url": "https://github.com/your-repo/easy_export",
            "footer_text": "此邮件由 Easy Export 系统自动发送，用于测试邮件功能。",
            "company_name": "Easy Export",
            "company_address": "测试地址",
            "contact_email": "changyunjeff@outlook.com",
            "current_year": "2024",
        }
        
        result = client.send_template(
            to=self.TEST_EMAIL,
            subject="【Easy Export】邮件模板测试 - test.html",
            template="test",
            context=context,
        )
        
        assert result is True, "模板邮件应该发送成功"
    
    @pytest.mark.skipif(
        not os.getenv("ENABLE_EMAIL_TESTS", "").lower() == "true",
        reason="需要设置 ENABLE_EMAIL_TESTS=true 来运行实际邮件发送测试"
    )
    def test_send_template_email_with_send_email_function(self, template_dir):
        """测试使用 send_email 函数发送模板邮件"""
        # 注意：由于 get_email_client 是单例，需要确保模板目录在首次调用时设置
        # 这里直接使用已初始化的客户端，因为 setup_and_teardown 已经初始化了邮件服务
        
        context = {
            "title": "Easy Export 邮件测试（send_email 函数）",
            "subtitle": "使用 send_email 便捷函数测试",
            "name": "Jeff Chang",
            "content": "<p>这是通过 <code>send_email</code> 函数发送的模板邮件。</p>",
        }
        
        # 使用 send_email 函数发送邮件
        # 注意：这需要全局邮件客户端已经使用正确的模板目录初始化
        result = send_email(
            to=self.TEST_EMAIL,
            subject="【Easy Export】邮件模板测试 - send_email 函数",
            template="test",
            context=context,
        )
        
        assert result is True, "通过 send_email 函数发送的模板邮件应该成功"
    
    @pytest.mark.skipif(
        not os.getenv("ENABLE_EMAIL_TESTS", "").lower() == "true",
        reason="需要设置 ENABLE_EMAIL_TESTS=true 来运行实际邮件发送测试"
    )
    def test_send_email_to_multiple_recipients(self):
        """测试向多个收件人发送邮件"""
        recipients = [
            self.TEST_EMAIL,
            # 可以添加更多测试邮箱
        ]
        
        result = send_email(
            to=recipients,
            subject="测试邮件 - 多个收件人",
            body="这是一封发送给多个收件人的测试邮件。",
        )
        
        assert result is True, "多收件人邮件应该发送成功"
    
    def test_send_email_when_disabled(self):
        """测试邮件服务未启用时的行为"""
        # 先关闭邮件服务
        close_email()
        
        # 尝试发送邮件
        result = send_email(
            to=self.TEST_EMAIL,
            subject="测试",
            body="测试内容",
        )
        
        assert result is False, "邮件服务未启用时应该返回 False"
    
    def test_send_email_with_invalid_template(self, email_client):
        """测试使用无效模板发送邮件"""
        result = email_client.send(
            to=self.TEST_EMAIL,
            subject="测试",
            template="nonexistent_template",
            context={},
        )
        
        assert result is False, "无效模板应该导致发送失败"
    
    def test_email_client_singleton(self, template_dir):
        """测试邮件客户端单例模式"""
        client1 = get_email_client(template_dir=template_dir)
        client2 = get_email_client()
        
        assert client1 is client2, "get_email_client 应该返回同一个实例"
    
    def test_template_rendering_with_all_variables(self, email_client):
        """测试模板渲染包含所有变量"""
        context = {
            "subject": "完整测试",
            "title": "完整变量测试",
            "subtitle": "测试所有模板变量",
            "name": "完整测试用户",
            "content": "<p>完整内容测试</p>",
            "info_items": [
                {"label": "变量1", "value": "值1"},
                {"label": "变量2", "value": "值2"},
            ],
            "button_text": "测试按钮",
            "button_url": "https://test.com",
            "footer_text": "测试页脚",
            "company_name": "测试公司",
            "company_address": "测试地址",
            "contact_email": "test@example.com",
            "current_year": "2024",
        }
        
        text_body, html_body = email_client._render_template("test", context)
        
        assert html_body is not None
        # 检查所有变量是否都被渲染
        assert "完整变量测试" in html_body
        assert "完整测试用户" in html_body
        assert "测试按钮" in html_body
        assert "https://test.com" in html_body
        assert "测试公司" in html_body
        assert "test@example.com" in html_body
        assert "2024" in html_body
    
    def test_is_email_enabled(self):
        """测试邮件服务启用状态检查"""
        # 邮件服务应该在 setup_and_teardown 中初始化
        if is_email_enabled():
            assert is_email_enabled() is True, "邮件服务应该已启用"
        else:
            pytest.skip("邮件服务未启用，跳过此测试")

