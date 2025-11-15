"""
格式转换器模块
负责HTML转PDF、格式互转、样式保持
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Converter:
    """
    格式转换器类
    负责格式转换、样式保持等
    """
    
    def html_to_pdf(
        self,
        html: str,
        css: Optional[str] = None,
    ) -> bytes:
        """
        将HTML转换为PDF（使用weasyprint）
        
        Args:
            html: HTML内容
            css: CSS样式（可选）
            
        Returns:
            PDF文档内容（字节）
            
        Raises:
            ImportError: 缺少必要的依赖库
            ValueError: HTML转换失败
        """
        try:
            from weasyprint import HTML, CSS
            from io import BytesIO
        except ImportError as exc:
            raise ImportError(
                "HTML转PDF需要安装weasyprint库。请运行: pip install weasyprint"
            ) from exc
        
        try:
            # 创建HTML对象
            html_obj = HTML(string=html)
            
            # 渲染为PDF
            output_stream = BytesIO()
            if css:
                css_obj = CSS(string=css)
                html_obj.write_pdf(output_stream, stylesheets=[css_obj])
            else:
                html_obj.write_pdf(output_stream)
            
            output_stream.seek(0)
            result = output_stream.read()
            
            logger.debug("HTML转PDF成功 (%d bytes)", len(result))
            return result
            
        except Exception as exc:
            raise ValueError(f"HTML转PDF失败: {exc}") from exc
    
    def docx_to_pdf(
        self,
        docx_bytes: bytes,
    ) -> bytes:
        """
        将Word文档转换为PDF（使用docx2pdf）
        
        注意：此方法需要系统安装LibreOffice或Microsoft Word
        
        Args:
            docx_bytes: Word文档内容（字节）
            
        Returns:
            PDF文档内容（字节）
            
        Raises:
            ImportError: 缺少必要的依赖库
            RuntimeError: PDF转换失败
        """
        try:
            from docx2pdf import convert
        except ImportError as exc:
            raise ImportError(
                "Word转PDF需要安装docx2pdf库。请运行: pip install docx2pdf\n"
                "注意: docx2pdf需要系统安装LibreOffice或Microsoft Word"
            ) from exc
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
            temp_docx.write(docx_bytes)
            temp_docx_path = temp_docx.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # 转换为PDF
            convert(temp_docx_path, temp_pdf_path)
            
            # 读取PDF内容
            with open(temp_pdf_path, 'rb') as f:
                result = f.read()
            
            logger.debug("Word转PDF成功 (%d bytes)", len(result))
            return result
            
        except Exception as exc:
            raise RuntimeError(
                f"Word转PDF失败: {exc}\n"
                "请确保系统已安装LibreOffice或Microsoft Word，"
                "并且docx2pdf库已正确安装。"
            ) from exc
        finally:
            # 清理临时文件
            try:
                Path(temp_docx_path).unlink()
            except:
                pass
            try:
                Path(temp_pdf_path).unlink()
            except:
                pass
    
    def pdf_to_html(
        self,
        pdf_bytes: bytes,
    ) -> str:
        """
        将PDF转换为HTML（可选功能，暂不实现）
        
        Args:
            pdf_bytes: PDF文档内容（字节）
            
        Returns:
            HTML内容
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("PDF转HTML功能待实现")

