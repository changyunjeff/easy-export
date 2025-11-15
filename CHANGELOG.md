<div align="center">
  <h1>这里是标题</h1>
  <p>
    <a href="#v0.1.0">
      <img alt="version" src="https://img.shields.io/badge/version-v0.1.0-blue?style=flat-square">
    </a>
    <img alt="stage" src="https://img.shields.io/badge/stage-alpha-orange?style=flat-square">
    <img alt="license" src="https://img.shields.io/badge/license-Apache%202.0-lightgrey?style=flat-square">
  </p>
  <p style="margin-top:8px;color:#666;">
    这里是简介
  </p>
</div>

<hr>

<details open>
  <summary><strong>目录</strong></summary>
  <ul>
    <li><a href="#v0.1.0">v0.1.0 — 2025-11-14</a></li>
  </ul>
</details>

<hr>

<h2 id="v0.1.0">v0.1.0 <small style="color:#888;font-weight:normal;">2025‑11‑14</small></h2>

<blockquote>
  <p><strong>Alpha 首个节点</strong>：这里是变更简介。</p>
</blockquote>

<div>
  <h3>✨ 新增</h3>
  <ul>
    <li>实现 TemplateStorage 文件落盘与版本管理，新增 manifest/哈希维护并补充单元测试。</li>
    <li>实现 FileStorage 输出落盘、URL 生成与过期清理能力，并补充单元测试。</li>
    <li>实现 CacheStorage 图表/模板元数据/任务状态三类缓存接口，提供 TTL/校验工具并编写配套单测。</li>
    <li>实现 TemplateEngine 模板加载、占位符解析/校验与 Jinja2 渲染能力，新增覆盖 HTML/DOCX 的单元测试。</li>
    <li>实现 HTML 渲染器与 RendererFactory，打通 ExportService HTML 单文档导出流程并补充单元测试。</li>
    <li>实现 ChartGenerator 折线/柱状/饼图、统一配置与数据哈希缓存，支持 PNG/JPEG 输出并新增 <code>tests/test_chart_generator.py</code>。</li>
    <li>新增 <code>mvp/chart_export.py</code> 与 <code>mvp/chart_sample.json</code>，提供 CLI 级图表导出 MVP 参考流程。</li>
    <li>实现 Text/Table/Image/Chart Filler 及数据映射/空值策略，新增结构化 FillResult 数据结构与 <code>tests/test_filler.py</code> 全覆盖单测。</li>
    <li><strong>实现 DocxRenderer - 使用 docxtpl 渲染 Word 模板，支持 Jinja2 语法与完整数据填充</strong>。</li>
    <li><strong>实现 PDFRenderer - 支持从 HTML 和 Word 模板生成 PDF，集成 Converter 实现双路径渲染</strong>。</li>
    <li><strong>实现 Converter.html_to_pdf - 使用 weasyprint 将 HTML 转换为 PDF，支持自定义 CSS 样式</strong>。</li>
    <li><strong>实现 Converter.docx_to_pdf - 使用 docx2pdf 将 Word 文档转换为 PDF（需要系统安装 LibreOffice 或 MS Word）</strong>。</li>
    <li><strong>新增 <code>tests/test_renderer_and_converter.py</code> - 覆盖所有渲染器和转换器的单元测试</strong>。</li>
    <li><strong>新增 <code>core/gtk3_checker.py</code> - GTK3 环境检查与初始化模块，优雅处理 WeasyPrint 依赖</strong>。</li>
    <li><strong>实现 GTK3 自动检测 - 应用启动时自动检查 GTK3 可用性，提供详细诊断信息与配置指引</strong>。</li>
    <li><strong>新增 <code>docs/GTK3配置指南.md</code> - 详细的 GTK3 配置文档，覆盖 Windows/Linux/macOS 多平台</strong>。</li>
    <li><strong>完成 TemplateService 核心功能 - 实现模板创建、获取、列表、更新、删除、版本管理等7大功能，通过23个单元测试</strong>。</li>
    <li><strong>修复 TemplateService.get_template - 增强 datetime 字段处理，支持字符串与对象混合场景</strong>。</li>
    <li><strong>实现 TemplateStorage.list_templates - 新增列出所有模板 ID 的方法，支持服务层分页查询</strong>。</li>
    <li><strong>优化 TemplateService 异常处理 - delete_template 和 create_version 增加完善的异常抛出逻辑</strong>。</li>
  </ul>
</div>

<div>
  <h3>🛠️ 变更</h3>
  <ul>
    <li>更新能力矩阵，标记缓存存储能力与里程碑 M2 进度。</li>
    <li>更新能力矩阵与里程碑状态，标记模板引擎完成并刷新核心引擎层进度。</li>
    <li>能力矩阵与里程碑同步图表生成器完成度，核心引擎完成率提升至 60.6%。</li>
    <li>项目依赖新增 matplotlib，并补充 MVP 文档介绍图表导出流程。</li>
    <li>能力矩阵同步填充引擎 6/6 完成度，核心引擎完成率提升至 78.8%，里程碑 M3 更新至 79%。</li>
    <li><strong>更新能力矩阵：渲染引擎进度更新为 5/5 (100%)，格式转换器进度更新为 3/4 (75%)</strong>。</li>
    <li><strong>核心引擎层总进度提升至 31/33 (93.9%)，里程碑 M3 更新至 93.9%（接近完成）</strong>。</li>
    <li><strong>项目整体完成度从 39.4% 提升至 43.1%，P0 核心功能完成率从 48.0% 提升至 54.7%</strong>。</li>
    <li><strong>重构 main.py - 移除硬编码的 MSYS2 路径，改用环境变量配置，提升部署灵活性</strong>。</li>
    <li><strong>增强应用启动流程 - 集成 GTK3 检查到生命周期管理，优雅处理依赖检测失败场景</strong>。</li>
  </ul>
</div>

<div>
  <h3>📌 兼容性与备注</h3>
  <ul>
    <li><strong>GTK3 配置变更</strong>：从硬编码路径改为环境变量 <code>MSYS2_BIN</code>，需在 <code>.env</code> 文件中配置（Windows 系统）。</li>
    <li><strong>PDF 导出依赖</strong>：使用 WeasyPrint 生成 PDF 需要正确配置 GTK3 环境，应用启动时会自动检测并提供配置指引。</li>
    <li><strong>向后兼容</strong>：未配置 GTK3 不会影响应用启动，但 PDF 导出功能将不可用，建议按照文档配置 GTK3 环境。</li>
  </ul>
</div>

<div>
  <h3>⬆️ 升级指引</h3>
  <ol>
    <li><strong>配置 MSYS2_BIN 环境变量</strong>：如果之前依赖硬编码的 MSYS2 路径，请在项目根目录的 <code>.env</code> 文件中添加 <code>MSYS2_BIN=C:\msys64\ucrt64\bin</code>（根据实际路径调整）。</li>
    <li><strong>运行 GTK3 检查工具</strong>：执行 <code>python -m core.gtk3_checker</code> 验证 GTK3 配置是否正确。</li>
    <li><strong>查看配置指南</strong>：如遇到 GTK3 相关问题，请参考 <code>docs/GTK3配置指南.md</code> 进行排查。</li>
    <li><strong>测试 PDF 导出</strong>：启动应用后查看日志，确认 GTK3 检查通过，然后测试 PDF 导出功能。</li>
  </ol>
</div>

<hr>

<p align="right" style="color:#888;">
  采用 <a href="https://keepachangelog.com/zh-CN/1.1.0/">Keep a Changelog</a> 风格（结合 HTML 展示）。
  版本遵循 <a href="https://semver.org/lang/zh-CN/">SemVer</a>（预发布标记：alpha）。
</p>

