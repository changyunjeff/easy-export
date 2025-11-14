# MVP 文件说明

本目录包含两个MVP文件，用于模板填充和导出功能。

## 1. HTML模板导出 (html_export.py)

### 功能
- 读取HTML模板文件
- 使用JSON数据填充模板（支持Jinja2语法）
- **导出为HTML格式**

### 安装依赖
```bash
pip install jinja2
```

### 使用方法

#### 命令行方式
```bash
# 导出为HTML（默认）
python mvp/html_export.py static/email_template/test.html mvp/example_data.json

# 指定输出HTML文件
python mvp/html_export.py static/email_template/test.html mvp/example_data.json output.html
```

#### 代码方式
```python
from mvp.html_export import HTMLExporter

exporter = HTMLExporter(template_dir='static/email_template')
data = {
    'title': '欢迎',
    'name': '张三',
    # ... 更多数据
}

# 导出为HTML
exporter.export_to_file('test.html', data, 'output.html')
```

---

## 2. Word模板导出 (word_export.py)

### 功能
- 读取Word模板文件（.docx格式）
- 使用JSON数据填充模板（支持Jinja2语法）
- **默认导出为PDF格式**，也可导出为Word文档

### 安装依赖
```bash
pip install docxtpl python-docx docx2pdf
```

**重要**: `docx2pdf` 需要系统安装以下软件之一：
- **LibreOffice** (推荐，免费开源，跨平台)
  - Windows: 下载安装 [LibreOffice](https://www.libreoffice.org/download/)
  - Linux: `sudo apt-get install libreoffice` (Ubuntu/Debian)
  - macOS: `brew install --cask libreoffice`
- **Microsoft Word** (仅Windows/macOS，需要已安装)

### 使用方法

#### 命令行方式
```bash
# 创建示例模板（可选）
python mvp/create_word_template.py mvp/example_template.docx

# 默认导出为PDF
python mvp/word_export.py mvp/example_template.docx mvp/word_example_data.json

# 指定输出PDF文件
python mvp/word_export.py mvp/example_template.docx mvp/word_example_data.json output.pdf

# 导出为Word格式
python mvp/word_export.py mvp/example_template.docx mvp/word_example_data.json output.docx
```

#### 代码方式
```python
from mvp.word_export import WordExporter

exporter = WordExporter()
data = {
    'title': '订单确认',
    'name': '张三',
    'order_id': 'ORD-2024-001234',
    # ... 更多数据
}

# 导出为PDF（默认）
exporter.render_from_file('template.docx', data, 'output.pdf')

# 或导出为Word
exporter.render_from_file('template.docx', data, 'output.docx', format='docx')
```

### Word模板创建方法

#### 方法一：使用脚本创建基础模板（推荐）
```bash
python mvp/create_word_template.py mvp/example_template.docx
```
然后使用Microsoft Word打开，删除【请替换为】标记，将示例文本替换为Jinja2语法。

#### 方法二：手动创建
1. 打开Microsoft Word，创建新文档
2. 在文档中输入Jinja2语法占位符，例如：
   - `{{ order_id }}` - 变量替换
   - `{{ name | default("客户") }}` - 带默认值
   - `{% if condition %}...{% endif %}` - 条件判断
   - `{% for item in list %}...{% endfor %}` - 循环
3. 保存为 `.docx` 格式

详细说明请参考：`mvp/word_template_guide.md`

### 支持的Jinja2功能
- ✅ 变量替换：`{{ variable }}`
- ✅ 过滤器：`{{ variable | default("默认值") }}`
- ✅ 条件判断：`{% if condition %}...{% endif %}`
- ✅ 循环：`{% for item in list %}...{% endfor %}`
- ✅ 注释：`{# 这是注释 #}`
- ✅ 图片：`{%p image_path %}`

---

## 3. 图表快速导出 (chart_export.py)

### 功能
- 读取包含 `data/config/type` 的 JSON 文件
- 通过 `ChartGenerator` 生成折线/柱状/饼图图片
- 支持 PNG/JPEG 输出与多序列配置

### 安装依赖
```bash
pip install matplotlib Pillow
```
（完整项目请执行 `pip install -r requirements.txt`）

### 使用方法

```bash
# 基于示例数据生成折线图（默认输出 chart_line.png）
python mvp/chart_export.py mvp/chart_sample.json

# 指定输出路径与图片格式
python mvp/chart_export.py mvp/chart_sample.json -o output/sales.jpg --format jpg

# 覆盖 JSON 中的图表类型
python mvp/chart_export.py mvp/chart_sample.json --type bar
```

示例 JSON 结构参考 `mvp/chart_sample.json`：
```json
{
  "type": "line",
  "data": [{ "month": "Jan", "actual": 72, "plan": 65 }],
  "config": {
    "x_field": "month",
    "series": [
      { "y_field": "actual", "label": "Actual" },
      { "y_field": "plan", "label": "Plan" }
    ],
    "title": "Monthly Signups"
  }
}
```

---

## 示例数据文件

- `example_data.json` - HTML模板示例数据
- `word_example_data.json` - Word模板示例数据
- `chart_sample.json` - 图表生成示例数据

---

## 注意事项

1. **导出格式**：
   - HTML导出器：仅支持导出为HTML格式
   - Word导出器：默认导出为PDF格式，也可导出为Word文档
2. **Word模板语法**：确保Jinja2语法正确，包括 `{{ }}` 和 `{% %}` 的配对
3. **文件编码**：所有JSON文件使用UTF-8编码
4. **依赖安装**：
   - HTML导出需要：`jinja2`
   - Word导出需要：`docxtpl`、`python-docx`、`docx2pdf`
   - `docx2pdf` 需要系统安装 LibreOffice 或 Microsoft Word
5. **模板路径**：可以使用相对路径或绝对路径
6. **PDF转换**：Word转PDF需要系统安装LibreOffice或Microsoft Word

---

## 快速开始

### HTML导出
```bash
# 安装依赖
pip install jinja2

# 导出为HTML
python mvp/html_export.py static/email_template/test.html mvp/example_data.json

# 指定输出文件
python mvp/html_export.py static/email_template/test.html mvp/example_data.json output.html
```

### Word导出（默认PDF）
```bash
# 1. 安装依赖
pip install docxtpl python-docx docx2pdf

# 2. 安装LibreOffice（如果还没有）
# Windows: 下载安装 https://www.libreoffice.org/download/
# Linux: sudo apt-get install libreoffice
# macOS: brew install --cask libreoffice

# 3. 创建模板（可选）
python mvp/create_word_template.py mvp/example_template.docx

# 4. 导出为PDF（默认）
python mvp/word_export.py mvp/example_template.docx mvp/word_example_data.json

# 或导出为Word
python mvp/word_export.py mvp/example_template.docx mvp/word_example_data.json output.docx
```

