from __future__ import annotations

import logging
from typing import Optional
from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# 全局 SMTP 连接
_email_client: Optional['EmailClient'] = None
_email_enabled: bool = False


class EmailClient:
    """SMTP 邮件客户端"""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        tls: bool = True,
    ):
        """
        初始化邮件客户端
        
        Args:
            host: SMTP 服务器地址
            port: SMTP 端口
            user: SMTP 用户名/邮箱
            password: SMTP 密码
            tls: 是否启用 TLS
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.tls = tls
        self._smtp: Optional[SMTP] = None
    
    def connect(self) -> bool:
        """
        连接到 SMTP 服务器
        
        Returns:
            是否连接成功
        """
        try:
            if self.tls:
                self._smtp = SMTP(self.host, self.port)
                self._smtp.starttls()
            else:
                self._smtp = SMTP_SSL(self.host, self.port)
            
            self._smtp.login(self.user, self.password)
            logger.info(f"Email client connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            self._smtp = None
            return False
    
    def send(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        发送邮件
        
        Args:
            to: 收件人邮箱（单个或列表）
            subject: 邮件主题
            body: 纯文本内容
            html: HTML 内容（可选）
            from_email: 发件人邮箱（默认使用配置的 user）
        
        Returns:
            是否发送成功
        """
        if self._smtp is None:
            if not self.connect():
                return False
        
        try:
            # 确保 to 是列表
            if isinstance(to, str):
                to = [to]
            
            from_email = from_email or self.user
            
            # 创建邮件
            if html:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = ', '.join(to)
                
                # 添加纯文本和 HTML 版本
                text_part = MIMEText(body, 'plain', 'utf-8')
                html_part = MIMEText(html, 'html', 'utf-8')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                msg = MIMEText(body, 'plain', 'utf-8')
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = ', '.join(to)
            
            # 发送邮件
            self._smtp.sendmail(from_email, to, msg.as_string())
            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def close(self):
        """关闭 SMTP 连接"""
        if self._smtp:
            try:
                self._smtp.quit()
            except Exception as e:
                logger.warning(f"Error closing email connection: {e}")
            finally:
                self._smtp = None


def init_email(
    host: str,
    port: int,
    user: str,
    password: str,
    tls: bool = True,
) -> bool:
    """
    初始化全局邮件客户端
    
    Args:
        host: SMTP 服务器地址
        port: SMTP 端口
        user: SMTP 用户名/邮箱
        password: SMTP 密码
        tls: 是否启用 TLS
    
    Returns:
        是否初始化成功
    """
    global _email_client, _email_enabled
    
    try:
        _email_client = EmailClient(host, port, user, password, tls)
        if _email_client.connect():
            _email_enabled = True
            logger.info("Email service initialized successfully")
            return True
        else:
            _email_enabled = False
            logger.warning("Email service initialization failed")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize email service: {e}")
        _email_enabled = False
        return False


def close_email():
    """关闭全局邮件客户端"""
    global _email_client, _email_enabled
    
    if _email_client:
        _email_client.close()
        _email_client = None
    _email_enabled = False
    logger.info("Email service closed")


def is_email_enabled() -> bool:
    """检查邮件服务是否已启用"""
    return _email_enabled


def get_email_client() -> Optional[EmailClient]:
    """获取全局邮件客户端"""
    return _email_client

