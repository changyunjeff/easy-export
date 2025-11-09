#!/usr/bin/env python3
"""
MVP: HTML模板填充JSON/CSV数据并导出为HTML
功能：读取HTML模板，使用JSON或CSV数据填充，渲染并导出为HTML文件
依赖：pip install jinja2
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template


class HTMLExporter:
    """HTML模板导出器"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化导出器
        
        Args:
            template_dir: 模板文件目录，如果为None则使用当前目录
        """
        if template_dir is None:
            template_dir = str(Path(__file__).parent)
        
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def render_from_file(self, template_path: str, data: Dict[str, Any]) -> str:
        """
        从文件读取模板并渲染
        
        Args:
            template_path: 模板文件路径（相对于template_dir或绝对路径）
            data: 用于填充模板的JSON数据字典
            
        Returns:
            渲染后的HTML字符串
        """
        template = self.env.get_template(template_path)
        return template.render(**data)
    
    def render_from_string(self, template_string: str, data: Dict[str, Any]) -> str:
        """
        从字符串渲染模板
        
        Args:
            template_string: 模板字符串
            data: 用于填充模板的JSON数据字典
            
        Returns:
            渲染后的HTML字符串
        """
        template = Template(template_string)
        return template.render(**data)
    
    def export_to_file(
        self,
        template_path: str,
        data: Dict[str, Any],
        output_path: Optional[str] = None,
        encoding: str = 'utf-8'
    ) -> str:
        """
        渲染模板并导出为HTML文件
        
        Args:
            template_path: 模板文件路径
            data: 用于填充模板的JSON数据字典
            output_path: 输出文件路径，如果为None则自动生成（基于模板文件名）
            encoding: 文件编码，默认utf-8
            
        Returns:
            输出文件路径
        """
        html_content = self.render_from_file(template_path, data)
        
        # 如果未指定输出路径，自动生成
        if output_path is None:
            template_name = Path(template_path).stem
            output_path = f"{template_name}_output.html"
        
        # 确保输出路径扩展名为.html
        output_file = Path(output_path)
        if output_file.suffix.lower() != '.html':
            output_path = str(output_file.with_suffix('.html'))
        
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入HTML文件
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(html_content)
        
        return str(output_file.absolute())


def load_json_data(json_path: str) -> Dict[str, Any]:
    """
    从JSON文件加载数据
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        解析后的字典数据
    """
    json_file = Path(json_path)
    if not json_file.exists():
        abs_path = json_file.absolute()
        raise FileNotFoundError(
            f"JSON文件不存在: {json_path}\n"
            f"绝对路径: {abs_path}\n"
            f"请检查文件路径是否正确。"
        )
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv_data(csv_path: str) -> Dict[str, Any]:
    """
    从CSV文件加载数据并转换为字典格式
    
    支持两种CSV格式：
    1. 键值对格式（第一列是键，第二列是值）：
       key,value
       title,订单确认
       name,张三
       
    2. 表格式（第一行是表头，后续行是数据，自动转换为数组）：
       label,value
       订单号,ORD-2024-001
       金额,¥299.00
       转换为: info_items = [{'label': '订单号', 'value': 'ORD-2024-001'}, ...]
    
    Args:
        csv_path: CSV文件路径
        
    Returns:
        解析后的字典数据
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        abs_path = csv_file.absolute()
        raise FileNotFoundError(
            f"CSV文件不存在: {csv_path}\n"
            f"绝对路径: {abs_path}\n"
            f"请检查文件路径是否正确。"
        )
    
    data: Dict[str, Any] = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # 使用csv.reader解析
        reader = csv.reader(f)
        rows = list(reader)
        
        if not rows:
            return data
        
        # 检查是否是表格式（第一行是表头，且有多行数据）
        if len(rows) > 1 and len(rows[0]) >= 2:
            # 检查第一行是否是表头（通常是字符串，不是纯数字）
            first_row = rows[0]
            second_row = rows[1] if len(rows) > 1 else []
            
            # 判断：如果第一行和第二行的列数相同，且第一行看起来像表头
            if (len(first_row) == len(second_row) and 
                all(isinstance(cell, str) and not cell.replace('.', '').replace('-', '').isdigit() 
                    for cell in first_row if cell)):
                # 表格式：转换为数组
                headers = [cell.strip() for cell in first_row]
                
                # 如果表头是 label,value，则转换为 info_items 数组
                if len(headers) == 2 and 'label' in headers and 'value' in headers:
                    label_idx = headers.index('label')
                    value_idx = headers.index('value')
                    info_items = []
                    for row in rows[1:]:
                        if len(row) > max(label_idx, value_idx):
                            info_items.append({
                                'label': row[label_idx].strip() if label_idx < len(row) else '',
                                'value': row[value_idx].strip() if value_idx < len(row) else ''
                            })
                    data['info_items'] = info_items
                else:
                    # 其他表格式：转换为以第一列值为键的字典数组
                    key_header = headers[0]
                    items = []
                    for row in rows[1:]:
                        if len(row) > 0:
                            item = {}
                            for i, header in enumerate(headers):
                                if i < len(row):
                                    item[header] = row[i].strip()
                            items.append(item)
                    # 使用表头第一列作为数组名
                    array_name = f"{key_header}s" if not key_header.endswith('s') else key_header
                    data[array_name] = items
            else:
                # 键值对格式
                for row in rows:
                    if len(row) >= 2:
                        key = row[0].strip()
                        value = row[1].strip()
                        # 尝试转换数据类型
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value)
                        data[key] = value
        else:
            # 键值对格式（只有一行或格式不明确）
            for row in rows:
                if len(row) >= 2:
                    key = row[0].strip()
                    value = row[1].strip()
                    # 尝试转换数据类型
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                    data[key] = value
    
    return data


def load_data(data_path: str) -> Dict[str, Any]:
    """
    从文件加载数据（自动检测JSON或CSV格式）
    
    Args:
        data_path: 数据文件路径（.json 或 .csv）
        
    Returns:
        解析后的字典数据
        
    Raises:
        ValueError: 不支持的文件格式
    """
    data_file = Path(data_path)
    suffix = data_file.suffix.lower()
    
    if suffix == '.json':
        return load_json_data(data_path)
    elif suffix == '.csv':
        return load_csv_data(data_path)
    else:
        raise ValueError(
            f"不支持的文件格式: {suffix}\n"
            f"支持格式: .json, .csv"
        )


def main():
    """主函数：示例用法"""
    import sys
    
    if len(sys.argv) >= 3:
        template_path = sys.argv[1]
        data_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 加载数据（自动检测JSON或CSV格式）
        data = load_data(data_path)
        
        # 创建导出器（模板文件所在目录）
        template_dir = str(Path(template_path).parent)
        exporter = HTMLExporter(template_dir)
        
        # 获取模板文件名
        template_name = Path(template_path).name
        
        # 导出为HTML
        result_path = exporter.export_to_file(template_name, data, output_path)
        print(f"✓ 导出成功 (HTML): {result_path}")
    else:
        print("HTML模板导出工具")
        print("\n使用示例:")
        print("  python html_export.py <template.html> <data.json> [output.html]")
        print("  python html_export.py <template.html> <data.csv> [output.html]")
        print("\n或者使用代码:")
        print("""
from mvp.html_export import HTMLExporter

# 创建导出器
exporter = HTMLExporter(template_dir='static/email_template')

# 准备数据（可以是字典或从JSON/CSV文件加载）
data = {
    'subject': '测试邮件',
    'title': '欢迎使用',
    'name': '张三',
    'content': '<p>这是一封测试邮件</p>',
    'info_items': [
        {'label': '订单号', 'value': 'ORD-2024-001'},
        {'label': '金额', 'value': '¥99.00'}
    ],
    'button_text': '查看详情',
    'button_url': 'https://example.com',
    'footer_text': '感谢您的使用',
    'company_name': 'Easy Export',
    'contact_email': 'support@example.com',
    'current_year': 2024
}

# 或从文件加载
from mvp.html_export import load_data
data = load_data('data.json')  # 或 load_data('data.csv')

# 导出为HTML
exporter.export_to_file('test.html', data, 'output.html')
        """)


if __name__ == '__main__':
    main()
