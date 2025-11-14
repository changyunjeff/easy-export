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
  </ul>
</div>

<div>
  <h3>🛠️ 变更</h3>
  <ul>
    <li>更新能力矩阵，标记缓存存储能力与里程碑 M2 进度。</li>
    <li>更新能力矩阵与里程碑状态，标记模板引擎完成并刷新核心引擎层进度。</li>
    <li>能力矩阵与里程碑同步图表生成器完成度，核心引擎完成率提升至 60.6%。</li>
    <li>项目依赖新增 matplotlib，并补充 MVP 文档介绍图表导出流程。</li>
  </ul>
</div>

<div>
  <h3>📌 兼容性与备注</h3>
  <ul>
    <li>这里是备注列表。</li>
  </ul>
</div>

<div>
  <h3>⬆️ 升级指引</h3>
  <ol>
    <li>这里是升级指引列表。</li>
  </ol>
</div>

<hr>

<p align="right" style="color:#888;">
  采用 <a href="https://keepachangelog.com/zh-CN/1.1.0/">Keep a Changelog</a> 风格（结合 HTML 展示）。
  版本遵循 <a href="https://semver.org/lang/zh-CN/">SemVer</a>（预发布标记：alpha）。
</p>

