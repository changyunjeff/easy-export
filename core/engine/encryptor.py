"""
文档加密模块
负责PDF和Word文档的密码保护
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentEncryptor:
    """
    文档加密器类
    负责PDF和Word文档的加密
    """
    
    def encrypt_pdf(
        self,
        pdf_bytes: bytes,
        password: str,
        *,
        owner_password: Optional[str] = None,
    ) -> bytes:
        """
        加密PDF文档
        
        Args:
            pdf_bytes: PDF文档字节内容
            password: 用户密码(打开文档需要的密码)
            owner_password: 所有者密码(修改权限需要的密码,可选)
            
        Returns:
            加密后的PDF文档字节内容
            
        Raises:
            ImportError: 缺少必要的依赖库
            ValueError: 加密失败
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except ImportError as exc:
            raise ImportError(
                "PDF加密需要安装PyPDF2库。请运行: pip install PyPDF2"
            ) from exc
        
        if not password:
            raise ValueError("密码不能为空")
        
        try:
            # 读取PDF
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            
            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)
            
            # 复制元数据
            if reader.metadata:
                writer.add_metadata(reader.metadata)
            
            # 设置密码加密(PyPDF2使用默认的128位RC4加密)
            writer.encrypt(
                user_password=password,
                owner_password=owner_password
            )
            
            # 保存到字节流
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            result = output.read()
            
            logger.info(
                "PDF加密成功 (%d bytes -> %d bytes)",
                len(pdf_bytes),
                len(result)
            )
            return result
            
        except Exception as exc:
            raise ValueError(f"PDF加密失败: {exc}") from exc
    
    def encrypt_word(
        self,
        docx_bytes: bytes,
        password: str,
    ) -> bytes:
        """
        加密Word文档
        
        Args:
            docx_bytes: Word文档字节内容
            password: 文档密码
            
        Returns:
            加密后的Word文档字节内容
            
        Raises:
            ImportError: 缺少必要的依赖库
            ValueError: 加密失败
        """
        try:
            import msoffcrypto
        except ImportError as exc:
            raise ImportError(
                "Word加密需要安装msoffcrypto-tool库。请运行: pip install msoffcrypto-tool"
            ) from exc
        
        if not password:
            raise ValueError("密码不能为空")
        
        try:
            # 读取Word文档
            input_stream = io.BytesIO(docx_bytes)
            output_stream = io.BytesIO()
            
            # 创建加密对象
            office_file = msoffcrypto.OfficeFile(input_stream)
            
            # 设置密码加密
            # 注意：load_key是用于解密的，加密时直接调用encrypt即可
            office_file.encrypt(password, output_stream)
            
            output_stream.seek(0)
            result = output_stream.read()
            
            logger.info(
                "Word加密成功 (%d bytes -> %d bytes)",
                len(docx_bytes),
                len(result)
            )
            return result
            
        except Exception as exc:
            raise ValueError(f"Word加密失败: {exc}") from exc
    
    def encrypt_document(
        self,
        document_bytes: bytes,
        password: str,
        format: str,
        **kwargs
    ) -> bytes:
        """
        根据格式自动选择加密方法
        
        Args:
            document_bytes: 文档字节内容
            password: 文档密码
            format: 文档格式(pdf/docx)
            **kwargs: 额外参数(如owner_password等)
            
        Returns:
            加密后的文档字节内容
            
        Raises:
            ValueError: 不支持的格式或加密失败
        """
        format_lower = format.lower()
        
        if format_lower == "pdf":
            return self.encrypt_pdf(
                document_bytes,
                password,
                owner_password=kwargs.get("owner_password")
            )
        elif format_lower == "docx":
            return self.encrypt_word(document_bytes, password)
        else:
            raise ValueError(f"不支持的文档格式: {format}")

