"""
GTK3检查模块
在应用启动时检查GTK3库是否可用，确保WeasyPrint能正常运行
"""

import os
import sys
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class GTK3CheckError(Exception):
    """GTK3检查失败异常"""
    pass


def setup_gtk3_environment() -> bool:
    """
    设置GTK3运行环境
    
    从环境变量MSYS2_BIN读取MSYS2的bin目录路径，
    并将其添加到PATH和DLL搜索路径中。
    
    Returns:
        bool: 是否成功设置环境
    """
    msys2_bin = os.getenv('MSYS2_BIN')
    
    if not msys2_bin:
        logger.debug("未设置MSYS2_BIN环境变量，跳过GTK3环境配置")
        return False
    
    if not os.path.exists(msys2_bin):
        logger.warning(f"MSYS2_BIN路径不存在: {msys2_bin}")
        return False
    
    try:
        # 确保MSYS2的bin目录在PATH最前面
        current_path = os.environ.get('PATH', '')
        path_parts = current_path.split(os.pathsep)
        
        # 如果MSYS2_BIN不在PATH最前面，则添加
        if not path_parts or path_parts[0] != msys2_bin:
            os.environ['PATH'] = msys2_bin + os.pathsep + current_path
            logger.debug(f"已将 {msys2_bin} 添加到PATH最前面")
        
        # 添加DLL搜索路径（Python 3.8+）
        if sys.version_info >= (3, 8):
            try:
                os.add_dll_directory(msys2_bin)
                logger.debug(f"已添加DLL搜索路径: {msys2_bin}")
            except (OSError, AttributeError) as e:
                logger.warning(f"添加DLL搜索路径失败: {e}")
        
        return True
        
    except Exception as e:
        logger.warning(f"设置GTK3环境时出错: {e}")
        return False


def check_gtk3_availability(raise_on_error: bool = False) -> Tuple[bool, Optional[str]]:
    """
    检查GTK3库是否可用
    
    尝试导入WeasyPrint并创建一个简单的HTML对象来验证GTK3是否正常工作。
    
    Args:
        raise_on_error: 如果为True，检查失败时抛出异常；否则返回错误信息
    
    Returns:
        Tuple[bool, Optional[str]]: (是否可用, 错误信息)
    
    Raises:
        GTK3CheckError: 当raise_on_error=True且检查失败时
    """
    try:
        # 尝试导入WeasyPrint
        from weasyprint import HTML
        
        # 创建一个简单的HTML对象来测试GTK3
        test_html = '<html><body><p>GTK3 Test</p></body></html>'
        HTML(string=test_html)
        
        logger.info("✓ GTK3库检查通过，WeasyPrint可正常使用")
        return True, None
        
    except ImportError as e:
        error_msg = f"WeasyPrint未安装: {e}"
        logger.error(f"✗ {error_msg}")
        logger.info("请运行: pip install weasyprint")
        
        if raise_on_error:
            raise GTK3CheckError(error_msg) from e
        return False, error_msg
        
    except OSError as e:
        # 通常是GTK3库缺失或配置错误
        error_msg = f"GTK3库不可用: {e}"
        logger.error(f"✗ {error_msg}")
        
        # 提供详细的解决方案
        msys2_bin = os.getenv('MSYS2_BIN')
        if not msys2_bin:
            logger.info("""
请按以下步骤配置GTK3:

1. 安装MSYS2 (如果尚未安装):
   下载地址: https://www.msys2.org/

2. 在MSYS2终端中安装GTK3:
   pacman -S mingw-w64-ucrt-x86_64-gtk3

3. 设置环境变量MSYS2_BIN:
   在.env文件中添加:
   MSYS2_BIN=C:\\msys64\\ucrt64\\bin
   (请根据实际安装路径调整)

4. 重启应用
""")
        else:
            logger.info(f"""
GTK3配置检查:

1. 当前MSYS2_BIN: {msys2_bin}
2. 路径是否存在: {os.path.exists(msys2_bin)}

请确认:
- MSYS2已正确安装
- GTK3已安装 (pacman -S mingw-w64-ucrt-x86_64-gtk3)
- MSYS2_BIN路径正确

如问题仍然存在，请参考项目中的GTK3安装向导文档。
""")
        
        if raise_on_error:
            raise GTK3CheckError(error_msg) from e
        return False, error_msg
        
    except Exception as e:
        error_msg = f"GTK3检查时发生未知错误: {e}"
        logger.error(f"✗ {error_msg}")
        
        if raise_on_error:
            raise GTK3CheckError(error_msg) from e
        return False, error_msg


def initialize_gtk3(required: bool = False) -> bool:
    """
    初始化GTK3环境并检查可用性
    
    这是主要的入口函数，在应用启动时调用。
    
    Args:
        required: 如果为True，GTK3不可用时将抛出异常；
                 如果为False，只记录警告并继续运行
    
    Returns:
        bool: GTK3是否可用
    
    Raises:
        GTK3CheckError: 当required=True且GTK3不可用时
    """
    logger.info("开始GTK3环境初始化...")
    
    # 步骤1: 设置环境
    env_setup = setup_gtk3_environment()
    if env_setup:
        logger.info("GTK3环境配置完成")
    else:
        logger.info("未配置GTK3环境（可能在非Windows系统或未设置MSYS2_BIN）")
    
    # 步骤2: 检查可用性
    is_available, error_msg = check_gtk3_availability(raise_on_error=required)
    
    if not is_available and not required:
        logger.warning("GTK3不可用，PDF导出功能可能无法正常工作")
        logger.warning("如需使用PDF导出功能，请按照上述说明配置GTK3")
    
    return is_available


def test_pdf_generation(output_path: str = "test_gtk3.pdf") -> bool:
    """
    测试PDF生成功能
    
    生成一个简单的测试PDF文件，验证GTK3和WeasyPrint是否正常工作。
    
    Args:
        output_path: 输出PDF文件路径
    
    Returns:
        bool: 是否成功生成PDF
    """
    try:
        from weasyprint import HTML
        
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #2c3e50; }
                p { color: #34495e; line-height: 1.6; }
            </style>
        </head>
        <body>
            <h1>GTK3配置成功！</h1>
            <p>这是一个测试PDF文档，如果您能看到这个文件，说明WeasyPrint和GTK3已正确配置。</p>
            <p>测试时间: {}</p>
        </body>
        </html>
        '''.format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"✓ 测试PDF生成成功: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"✗ 测试PDF生成失败: {e}")
        return False


if __name__ == "__main__":
    # 独立运行时进行测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("GTK3环境检查工具")
    print("=" * 60)
    print()
    
    # 加载.env文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ 已加载.env文件")
    except ImportError:
        print("⚠ python-dotenv未安装，跳过.env加载")
    except Exception as e:
        print(f"⚠ 加载.env文件失败: {e}")
    
    print()
    
    # 初始化并检查
    try:
        is_available = initialize_gtk3(required=False)
        
        print()
        print("=" * 60)
        if is_available:
            print("结果: ✓ GTK3可用")
            print()
            
            # 询问是否生成测试PDF
            try:
                response = input("是否生成测试PDF? (y/n): ").strip().lower()
                if response == 'y':
                    test_pdf_generation()
            except (KeyboardInterrupt, EOFError):
                print("\n测试已取消")
        else:
            print("结果: ✗ GTK3不可用")
            print("请按照上述说明配置GTK3环境")
        print("=" * 60)
        
    except GTK3CheckError as e:
        print()
        print("=" * 60)
        print(f"错误: {e}")
        print("=" * 60)
        sys.exit(1)

