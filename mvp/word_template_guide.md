# Word模板创建指南

## 方法一：使用Python脚本创建基础模板（推荐）

运行以下命令创建示例模板：

```bash
python mvp/word_export.py --create-template mvp/example_template.docx
```

然后使用Microsoft Word打开该文件，手动将示例文本替换为Jinja2语法占位符。

## 方法二：手动创建Word模板

### 步骤1：创建新的Word文档

1. 打开Microsoft Word
2. 创建新文档
3. 保存为 `.docx` 格式（例如：`template.docx`）

### 步骤2：添加Jinja2语法占位符

在Word文档中，你可以直接输入Jinja2语法作为占位符。docxtpl库会自动识别并替换这些占位符。

#### 基本变量替换

在Word中输入以下内容：

```
订单号: {{ order_id }}
订单金额: {{ amount }}
客户姓名: {{ name }}
```

#### 带默认值的变量

```
订单号: {{ order_id | default("未指定") }}
```

#### 条件判断

```
{% if has_discount %}
您享受了折扣优惠！
{% endif %}
```

#### 循环列表

```
订单详情：
{% for item in info_items %}
{{ item.label }}: {{ item.value }}
{% endfor %}
```

#### 表格循环

在Word中创建表格，然后在表格行中使用循环。**重要**：docxtpl在表格中循环需要使用特殊的 `{% tr for %}` 语法。

**方法一：使用 {% tr for %} 语法（推荐）**

1. 创建表格，包含表头行（例如："项目" 和 "内容"）
2. 在表头下创建一行数据行
3. 在数据行的第一个单元格中，输入：`{% tr for item in info_items %}{{ item.label }}`
4. 在数据行的第二个单元格中，输入：`{{ item.value }}{% endtr %}`

示例表格结构：
```
| 项目 | 内容 |
|-----|-----|
| {% tr for item in info_items %}{{ item.label }} | {{ item.value }}{% endtr %} |
```

**方法二：使用 {% for %} 包裹整个表格行**

1. 创建表格，包含表头行
2. 在表头下创建一行数据行
3. 在该行的第一个单元格前添加：`{% for item in info_items %}`
4. 在该行的最后一个单元格后添加：`{% endfor %}`
5. 单元格内容设置为：`{{ item.label }}` 和 `{{ item.value }}`

**注意**：如果表格数据未填充，请确保：
- 使用了正确的循环语法（`{% tr for %}` 或 `{% for %}`）
- JSON数据中包含 `info_items` 数组
- 数组中的每个对象包含 `label` 和 `value` 字段

### 步骤3：保存模板文件

保存Word文档为 `.docx` 格式。

## 示例模板内容

以下是一个完整的示例模板内容，你可以复制到Word中：

```
{{ title | default("订单确认") }}

亲爱的 {{ name | default("客户") }}，

感谢您的购买！您的订单已成功提交。

订单信息：
订单号: {{ order_id }}
订单金额: {{ amount }}
下单时间: {{ order_time }}
预计送达: {{ delivery_time }}

{% if info_items %}
详细信息：
{% for item in info_items %}
{{ item.label }}: {{ item.value }}
{% endfor %}
{% endif %}

{% if has_discount %}
您享受了折扣优惠！
{% endif %}

{{ footer_text | default("此邮件由系统自动发送，请勿直接回复。") }}

{{ company_name | default("Easy Export") }}
{{ company_address }}
联系邮箱: {{ contact_email }}

© {{ current_year | default("2024") }} All rights reserved.
```

## 注意事项

1. **语法格式**：确保Jinja2语法正确，包括 `{{ }}` 和 `{% %}` 的配对
2. **空格敏感**：Jinja2对空格敏感，注意占位符前后的空格
3. **特殊字符**：如果需要在输出中显示 `{{` 或 `}}`，使用 `{{ "{{" }}` 或 `{{ "}}" }}`
4. **表格处理**：在表格中使用循环时，确保循环语法正确嵌套
5. **图片处理**：docxtpl支持图片替换，使用 `{%p image_path %}` 语法

## 测试模板

创建模板后，使用以下命令测试：

```bash
python mvp/word_export.py mvp/example_template.docx mvp/example_data.json output.docx
```

## 支持的Jinja2功能

- 变量替换：`{{ variable }}`
- 过滤器：`{{ variable | default("默认值") }}`
- 条件判断：`{% if condition %}...{% endif %}`
- 循环：`{% for item in list %}...{% endfor %}`
- 注释：`{# 这是注释 #}`
- 图片：`{%p image_path %}`

## 依赖安装

确保已安装必要的库：

```bash
pip install docxtpl python-docx
```

