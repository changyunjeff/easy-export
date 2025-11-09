from __future__ import annotations

import logging
from typing import Optional, Union, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .connection import get_email_client as get_smtp_client, is_email_enabled

logger = logging.getLogger(__name__)


class EmailClient:
    """
    邮件客户端封装类，提供便捷的邮件发送接口
    支持模板渲染
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化邮件客户端
        
        Args:
            template_dir: 邮件模板目录路径
        """
        self.template_dir = template_dir
        self._jinja_env: Optional[Environment] = None
        
        if template_dir:
            template_path = Path(template_dir)
            if template_path.exists() and template_path.is_dir():
                self._jinja_env = Environment(
                    loader=FileSystemLoader(str(template_path)),
                    autoescape=True
                )
                logger.info(f"Email template directory loaded: {template_dir}")
            else:
                logger.warning(f"Email template directory not found: {template_dir}")
    
    def _render_template(
        self,
        template_name: str,
        context: dict,
    ) -> tuple[str, Optional[str]]:
        """
        渲染邮件模板
        
        Args:
            template_name: 模板文件名（不含扩展名）
            context: 模板上下文变量
        
        Returns:
            (text_body, html_body) 元组
        """
        if not self._jinja_env:
            return "", None
        
        try:
            # 尝试加载文本模板
            try:
                text_template = self._jinja_env.get_template(f"{template_name}.txt")
                text_body = text_template.render(**context)
            except TemplateNotFound:
                text_body = ""
            
            # 尝试加载 HTML 模板
            try:
                html_template = self._jinja_env.get_template(f"{template_name}.html")
                html_body = html_template.render(**context)
            except TemplateNotFound:
                html_body = None
            
            return text_body, html_body
        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            return "", None
    
    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: Optional[str] = None,
        html: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[dict] = None,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        发送邮件
        
        Args:
            to: 收件人邮箱（单个或列表）
            subject: 邮件主题
            body: 纯文本内容（如果使用模板则忽略）
            html: HTML 内容（如果使用模板则忽略）
            template: 模板名称（不含扩展名）
            context: 模板上下文变量
            from_email: 发件人邮箱（默认使用配置的 user）
        
        Returns:
            是否发送成功
        """
        if not is_email_enabled():
            logger.error("Email service is not enabled")
            return False
        
        client = get_smtp_client()
        if not client:
            logger.error("Email client is not initialized")
            return False
        
        # 如果使用模板，渲染模板
        if template:
            if not context:
                context = {}
            text_body, html_body = self._render_template(template, context)
            if not text_body and not html_body:
                logger.error(f"Template {template} rendered empty content")
                return False
        else:
            text_body = body or ""
            html_body = html
        
        # 发送邮件
        return client.send(
            to=to,
            subject=subject,
            body=text_body,
            html=html_body,
            from_email=from_email,
        )
    
    def send_template(
        self,
        to: Union[str, List[str]],
        subject: str,
        template: str,
        context: dict,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        使用模板发送邮件（便捷方法）
        
        Args:
            to: 收件人邮箱（单个或列表）
            subject: 邮件主题
            template: 模板名称（不含扩展名）
            context: 模板上下文变量
            from_email: 发件人邮箱（默认使用配置的 user）
        
        Returns:
            是否发送成功
        """
        return self.send(
            to=to,
            subject=subject,
            template=template,
            context=context,
            from_email=from_email,
        )


# 全局邮件客户端实例
_email_client_instance: Optional[EmailClient] = None


def get_email_client(template_dir: Optional[str] = None) -> EmailClient:
    """
    获取全局邮件客户端实例
    
    Args:
        template_dir: 邮件模板目录路径（仅在首次调用时生效）
    
    Returns:
        EmailClient 实例
    """
    global _email_client_instance
    
    if _email_client_instance is None:
        _email_client_instance = EmailClient(template_dir=template_dir)
    
    return _email_client_instance


def send_email(
    to: Union[str, List[str]],
    subject: str,
    body: Optional[str] = None,
    html: Optional[str] = None,
    template: Optional[str] = None,
    context: Optional[dict] = None,
    from_email: Optional[str] = None,
) -> bool:
    """
    发送邮件的便捷函数
    
    Args:
        to: 收件人邮箱（单个或列表）
        subject: 邮件主题
        body: 纯文本内容（如果使用模板则忽略）
        html: HTML 内容（如果使用模板则忽略）
        template: 模板名称（不含扩展名）
        context: 模板上下文变量
        from_email: 发件人邮箱（默认使用配置的 user）
    
    Returns:
        是否发送成功
    """
    client = get_email_client()
    return client.send(
        to=to,
        subject=subject,
        body=body,
        html=html,
        template=template,
        context=context,
        from_email=from_email,
    )

