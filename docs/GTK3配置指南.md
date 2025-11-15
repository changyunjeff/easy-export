# GTK3 配置指南

## 概述

本项目使用 WeasyPrint 来生成 PDF 文档。WeasyPrint 依赖 GTK3 库来进行渲染。本指南将帮助你在不同操作系统上配置 GTK3 环境。

## 为什么需要 GTK3？

WeasyPrint 使用 Cairo、Pango 和 GdkPixbuf 等库来渲染 HTML 和 CSS，这些库都是 GTK3 的一部分。没有正确配置 GTK3，PDF 导出功能将无法正常工作。

## 自动检测机制

项目在启动时会自动检测 GTK3 是否可用：

- ✓ 如果 GTK3 可用，会显示 "GTK3库检查通过，WeasyPrint可正常使用"
- ✗ 如果 GTK3 不可用，会显示警告信息和配置说明
- ⚠ GTK3 不可用不会阻止应用启动，但 PDF 导出功能将无法使用

## Windows 系统配置

### 步骤 1: 安装 MSYS2

1. 访问 [MSYS2 官网](https://www.msys2.org/)
2. 下载适合你系统的安装包（通常是 `msys2-x86_64-*.exe`）
3. 运行安装程序，按默认设置安装（建议安装到 `C:\msys64`）
4. 安装完成后，运行 MSYS2 UCRT64 终端

### 步骤 2: 安装 GTK3

在 MSYS2 UCRT64 终端中运行以下命令：

```bash
# 更新包数据库
pacman -Syu

# 安装 GTK3
pacman -S mingw-w64-ucrt-x86_64-gtk3

# 安装 pkg-config (可选，用于验证)
pacman -S mingw-w64-ucrt-x86_64-pkg-config
```

### 步骤 3: 验证安装

在 MSYS2 终端中运行：

```bash
pkg-config --modversion gtk+-3.0
```

如果显示版本号（如 `3.24.38`），说明安装成功。

### 步骤 4: 配置环境变量

在项目根目录创建 `.env` 文件（如果不存在），添加以下内容：

```env
# Windows GTK3 配置
# 请根据你的实际 MSYS2 安装路径修改
MSYS2_BIN=C:\msys64\ucrt64\bin
```

**常见路径示例：**
- 默认安装: `C:\msys64\ucrt64\bin`
- 自定义安装: `D:\tools\msys2\ucrt64\bin`

**注意事项：**
- 使用反斜杠 `\` 或正斜杠 `/` 都可以
- 路径不需要加引号
- 确保路径指向 MSYS2 的 `ucrt64\bin` 目录（不是 `mingw64` 或其他目录）

### 步骤 5: 测试配置

运行项目自带的 GTK3 检查工具：

```bash
python -m core.gtk3_checker
```

或使用提供的测试脚本：

```bash
python gtk3_runnable_test.py
```

如果配置正确，会生成一个测试 PDF 文件。

## Linux 系统配置

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 \
    libpangoft2-1.0-0 libharfbuzz0b libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Fedora/RHEL/CentOS

```bash
sudo dnf install python3-pip python3-cffi python3-brotli pango \
    libffi-devel gdk-pixbuf2
```

### Arch Linux

```bash
sudo pacman -S python-pip python-cffi python-brotli pango gdk-pixbuf2
```

**注意：** Linux 系统通常不需要配置 `MSYS2_BIN` 环境变量，GTK3 库会自动被系统识别。

## macOS 系统配置

### 使用 Homebrew

```bash
brew install python3 cairo pango gdk-pixbuf libffi
```

**注意：** macOS 系统也不需要配置 `MSYS2_BIN` 环境变量。

## 故障排除

### 问题 1: "找不到 libgobject-2.0-0.dll"

**原因：** MSYS2_BIN 路径配置错误或 GTK3 未正确安装。

**解决方案：**
1. 检查 `.env` 文件中的 `MSYS2_BIN` 路径是否正确
2. 确认该目录下存在 `libgobject-2.0-0.dll` 文件
3. 重新安装 GTK3: `pacman -S mingw-w64-ucrt-x86_64-gtk3`

### 问题 2: "OSError: cannot load library 'gobject-2.0'"

**原因：** DLL 搜索路径未正确配置。

**解决方案：**
1. 确保 Python 版本 >= 3.8
2. 确认 `.env` 文件已正确加载
3. 尝试手动测试：`python gtk3_runnable_test.py`

### 问题 3: 应用启动但 PDF 导出失败

**原因：** GTK3 环境在应用启动后未正确初始化。

**解决方案：**
1. 查看启动日志，确认 GTK3 检查是否通过
2. 运行独立测试工具：`python -m core.gtk3_checker`
3. 检查是否有其他应用占用了 GTK3 相关 DLL

### 问题 4: "WeasyPrint 未安装"

**原因：** WeasyPrint 包未安装。

**解决方案：**
```bash
pip install weasyprint
```

### 问题 5: 多个 GTK3 版本冲突

**原因：** 系统中安装了多个版本的 GTK3。

**解决方案：**
1. 确保 MSYS2 的 bin 目录在 PATH 最前面（程序会自动处理）
2. 移除其他 GTK3 安装或调整环境变量优先级
3. 使用虚拟环境隔离依赖

## 手动测试 GTK3

项目提供了两种测试方式：

### 方式 1: 使用 GTK3 检查模块

```bash
python -m core.gtk3_checker
```

这会执行完整的检查流程并提供详细的诊断信息。

### 方式 2: 使用独立测试脚本

```bash
python gtk3_runnable_test.py
```

如果成功，会在当前目录生成 `test.pdf` 文件。

## 在服务器环境中部署

### Docker 部署

在 Dockerfile 中添加 GTK3 依赖：

```dockerfile
# 基于 Debian/Ubuntu
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# ... 其他配置
```

### 无界面服务器

在无图形界面的服务器上，确保安装了以下包：

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info
```

**注意：** 不需要安装完整的桌面环境，只需要这些库即可。

## 性能优化建议

1. **预加载库：** 在应用启动时预加载 GTK3，避免首次调用时的延迟
2. **缓存字体：** 确保系统字体缓存是最新的
3. **使用 CDN：** 对于 CSS/图片等资源，使用本地路径而非远程 URL
4. **限制并发：** PDF 生成是 CPU 密集型操作，建议限制并发数

## 相关文档

- [WeasyPrint 官方文档](https://doc.courtbouillon.org/weasyprint/)
- [MSYS2 官方网站](https://www.msys2.org/)
- [GTK 项目主页](https://www.gtk.org/)

## 常见问题 (FAQ)

**Q: 我可以不安装 GTK3 吗？**

A: 可以，应用仍然可以启动和运行，但 PDF 导出功能将不可用。如果你只需要 Word 或 HTML 导出，可以不配置 GTK3。

**Q: GTK3 安装后占用多少空间？**

A: 通过 MSYS2 安装的 GTK3 及其依赖大约占用 200-300 MB 空间。

**Q: 可以在运行时动态加载 GTK3 吗？**

A: 项目支持延迟加载 WeasyPrint，但 GTK3 的 DLL 路径必须在 Python 进程启动前配置好。

**Q: 生产环境推荐的部署方式？**

A: 推荐使用 Docker 部署，在镜像中预装好所有依赖，避免环境配置问题。

## 技术支持

如果按照本指南操作后仍然遇到问题，请：

1. 运行诊断工具：`python -m core.gtk3_checker`
2. 查看应用启动日志
3. 提供详细的错误信息和系统环境信息
4. 在项目 Issue 区提问或查看已有的解决方案

