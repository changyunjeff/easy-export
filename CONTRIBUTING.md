<div align="center">
  <h1>VectorBD · 提交与贡献指南</h1>
  <p style="margin-top:8px;color:#666;">
    感谢你对 VectorBD 的关注与贡献！
  </p>
  <p>
    <a href="#发布说明--版本策略">发布策略</a> • <a href="#提交信息conventional-commits">提交规范</a> • <a href="#pr-规范">PR 规范</a> • <a href="#代码与目录规范python">代码规范</a> • <a href="#质量门禁最小">质量门禁</a>
  </p>
</div>

<hr>

## 目录

- [核心原则](#核心原则)
- [1. 发布说明 / 版本策略](#1-发布说明--版本策略)
  - [1.1 版本号规范（SemVer）](#11-版本号规范semver)
  - [1.2 分支与标签](#12-分支与标签)
  - [1.3 发布流程（Checklist）](#13-发布流程checklist)
  - [1.4 兼容性与弃用策略](#14-兼容性与弃用策略)
- [2. 提交信息（Conventional Commits）](#2-提交信息conventional-commits)
- [3. PR 规范](#3-pr-规范)
- [4. 代码与目录规范（Python）](#4-代码与目录规范python)
- [5. 文档与接口同步](#5-文档与接口同步)
- [6. 质量门禁（最小）](#6-质量门禁最小)
- [7. 贡献流程（建议）](#7-贡献流程建议)
- [8. 自检清单（提交前）](#8-自检清单提交前)
- [9. 许可证与版权](#9-许可证与版权)

---

## 核心原则

为确保协作高效、质量稳定，请在提交代码或文档前阅读并遵循本指南。

本项目的实现必须严格遵循以下规范性文档（强制约束）：
- 《概要与架构设计.md》：接口/目录/命名/异常与约束
- 《编程规范.md》：WBS/验收与范围边界

如两者与实现有冲突，请先在 PR 中说明并发起讨论，不要私自更改既定规范。

---

### 1. 发布说明 / 版本策略

#### 1.1 版本号规范（SemVer）
- 采用语义化版本：`MAJOR.MINOR.PATCH`
  - `MAJOR`：存在破坏性变更（接口或行为不兼容）
  - `MINOR`：向后兼容的新功能
  - `PATCH`：向后兼容的问题修复
- 预发布版本使用 Python/PEP 440 约定：`a`（alpha）、`b`（beta）、`rc`（候选）。示例：`0.2.0a1`、`0.2.0b2`、`0.2.0rc1`。

#### 1.2 分支与标签
- 主分支：`master`（或 `main`）。
- 打标签：`vX.Y.Z`（例如 `v0.1.0`）。预发布示例：`v0.2.0a1`。
- 推荐在标签说明中粘贴本次变更摘要。

#### 1.3 发布流程（Checklist）
1. 更新 `pyproject.toml` 中的 `version` 字段（如 `0.1.0` → `0.2.0a1`）。
2. 更新文档：`README.md`、`CHANGELOG.md`（新增版本节）。
3. 运行测试：`pytest -q`，确保通过。
4. 构建发行物：`python -m build`（生成 `dist/`）。
5. 创建 Git 标签：`git tag -a vX.Y.Z -m "release: vX.Y.Z" && git push --tags`。
6. 内部分发：将 `dist/*.whl` / `dist/*.tar.gz` 上传到内部制品库或共享盘。
7.（可选）发布到 PyPI：`python -m pip install twine && twine upload dist/*`。
8. 在代码托管平台创建 Release，附上发行物与发布说明。

#### 1.4 兼容性与弃用策略
- `0.y.z` 阶段视为快速演进期，可能包含不稳定接口；尽量减少破坏性变更。
- 标注弃用（deprecate）的接口会在后续至少一个 `MINOR` 版本后再移除；在文档与日志中给出替代方案。
- 工厂与接口层的稳定性优先；适配器的实验性能力独立标注“成熟度标签”。

### 2. 提交信息（Conventional Commits）
使用约定式提交，格式：
```
<type>(<scope>): <subject>

[optional body]
[optional footer]
```
- 常用 type：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`build`、`ci`、`chore`、`revert`
- `subject` 简洁明了（建议 ≤ 72 字符），中英文皆可，避免含糊词
- 如影响接口/行为，请在 body 中写明变更点与迁移说明

示例：
```
feat(service): add /upsert endpoint with request schema validation
fix(chroma): correct metadata flatten for None values in upsert
docs: add quickstart and usage examples for CLI search
```

### 3. PR 规范
- 每个 PR 只解决一件明确的事（原子任务）；描述清楚动机、方案与影响范围
- 勾选自检清单（见下文），关联相关 Issue/任务编号（如有）
- 保持变更最小化，避免无关格式化与重排
- 通过基本运行/静态检查（见“质量门禁”）后再提交 Review

### 4. 代码与目录规范（Python）
- 目录/接口/命名需对齐《概要与架构设计.md》与现有结构（如 `vecdb/`、`service/`）
- 类型：面向外部/导出函数使用类型标注；避免 `Any` 与不安全类型转换
- 控制流：优先早返回；只在必要处使用 try/except，不吞异常
- 命名：使用完整、可读的语义化名称，避免 1-2 字母短名
- 注释：仅保留对未来维护者有价值的信息（意图/边界/安全/性能）
- 格式：保持与现有代码风格一致，避免无关重排

### 5. 文档与接口同步
- 涉及对外接口/数据模型/错误码的变更，需同步更新相关文档与 `service/schemas.py`（如适用）
- README/示例需可运行（或最小可导入），并与实现一致

### 6. 质量门禁（最小）
- 能导入：新增/修改的模块可被 `import`，无语法错误
- 能运行：基础示例或最小路径可运行（如 `examples/quickstart.py`、服务 `boot.py` 启动）
- 静态检查：不引入新的 Lint/类型错误（如仓库已有门禁则需通过）
- 兼容性：不破坏既有已实现能力（Chroma 适配、嵌入、基础检索等）

### 7. 贡献流程（建议）
1. 认领任务并与《开发计划.md》对齐边界
2. 从 `master` 切分支，完成原子实现（≤30 分钟可验收）
3. 自检（见下文）后提交 PR，等待 Review 与合并

### 8. 自检清单（提交前）
- [ ] 变更符合《概要与架构设计.md》《编程规范.md》约束
- [ ] 变更最小化，无无关改动
- [ ] 新/改文件可导入与最小运行通过
- [ ] 文档/示例/接口 Schema 已同步
- [ ] 提交信息符合 Conventional Commits

### 9. 许可证与版权
提交贡献即视为你同意将改动以本仓库所用许可协议发布（见 `README.md` 说明）。

—— 感谢你的贡献！


