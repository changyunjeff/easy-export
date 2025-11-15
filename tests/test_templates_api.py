"""
模板管理接口集成测试
测试模板API的HTTP端点功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from fastapi.testclient import TestClient

from main import app
from core.storage import TemplateStorage


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_html_content():
    """示例HTML模板内容"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
"""


def test_create_template(client, sample_html_content):
    """测试创建模板接口"""
    # 准备文件
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    
    data = {
        "name": "测试模板",
        "description": "这是一个测试模板",
        "tags": "test,api",
        "version": "1.0.0"
    }
    
    # 发送请求
    response = client.post("/api/v1/templates", files=files, data=data)
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert "data" in result
    assert "template_id" in result["data"]
    assert result["data"]["name"] == "测试模板"
    assert result["data"]["version"] == "1.0.0"
    assert result["data"]["format"] == "html"
    assert result["data"]["file_size"] > 0
    assert "hash" in result["data"]
    assert "created_at" in result["data"]
    
    return result["data"]["template_id"]


def test_get_template(client, sample_html_content):
    """测试获取模板详情接口"""
    # 1. 先创建模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "测试模板详情",
        "description": "用于测试获取接口",
        "tags": "test",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 获取模板详情
    response = client.get(f"/api/v1/templates/{template_id}")
    
    # 3. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert result["data"]["template_id"] == template_id
    assert result["data"]["name"] == "测试模板详情"
    assert result["data"]["version"] == "1.0.0"


def test_list_templates(client, sample_html_content):
    """测试获取模板列表接口"""
    # 1. 创建几个模板
    for i in range(3):
        files = {
            "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
        }
        data = {
            "name": f"测试模板{i}",
            "description": f"描述{i}",
            "tags": "test,list",
            "version": "1.0.0"
        }
        response = client.post("/api/v1/templates", files=files, data=data)
        assert response.status_code == 200
    
    # 2. 获取模板列表
    response = client.get("/api/v1/templates?page=1&page_size=10")
    
    # 3. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert "data" in result
    assert "total" in result["data"]
    assert "page" in result["data"]
    assert "page_size" in result["data"]
    assert "items" in result["data"]
    assert result["data"]["total"] >= 3
    assert len(result["data"]["items"]) >= 3


def test_list_templates_with_filters(client, sample_html_content):
    """测试带过滤条件的模板列表查询"""
    # 1. 创建模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "过滤测试模板",
        "description": "用于过滤测试",
        "tags": "filter,special",
        "version": "1.0.0"
    }
    response = client.post("/api/v1/templates", files=files, data=data)
    assert response.status_code == 200
    
    # 2. 按名称过滤
    response = client.get("/api/v1/templates?name=过滤测试")
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert len(result["data"]["items"]) >= 1
    
    # 3. 按格式过滤
    response = client.get("/api/v1/templates?format=html")
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0


def test_update_template(client, sample_html_content):
    """测试更新模板接口"""
    # 1. 创建模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "原始名称",
        "description": "原始描述",
        "tags": "original",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 更新模板
    update_data = {
        "name": "更新后名称",
        "description": "更新后描述",
        "tags": "updated,new"
    }
    
    response = client.put(f"/api/v1/templates/{template_id}", data=update_data)
    
    # 3. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert result["data"]["name"] == "更新后名称"
    assert result["data"]["description"] == "更新后描述"
    assert "updated" in result["data"]["tags"]


def test_delete_template(client, sample_html_content):
    """测试删除模板接口"""
    # 1. 创建模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "待删除模板",
        "description": "将被删除",
        "tags": "delete",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 删除模板
    response = client.delete(f"/api/v1/templates/{template_id}")
    
    # 3. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert result["data"]["deleted"] is True
    
    # 4. 验证模板已删除
    get_response = client.get(f"/api/v1/templates/{template_id}")
    assert get_response.status_code == 404


def test_create_version(client, sample_html_content):
    """测试创建模板版本接口"""
    # 1. 创建初始模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "版本测试模板",
        "description": "用于版本测试",
        "tags": "version",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 创建新版本
    modified_content = sample_html_content.replace("{{ heading }}", "{{ heading_v2 }}")
    files = {
        "file": ("test_template_v2.html", modified_content.encode("utf-8"), "text/html")
    }
    data = {
        "version": "2.0.0",
        "changelog": "更新了heading占位符"
    }
    
    response = client.post(f"/api/v1/templates/{template_id}/versions", files=files, data=data)
    
    # 3. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert result["data"]["version"] == "2.0.0"
    assert result["data"]["changelog"] == "更新了heading占位符"


def test_list_versions(client, sample_html_content):
    """测试获取版本列表接口"""
    # 1. 创建初始模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "版本列表测试",
        "description": "用于版本列表测试",
        "tags": "version",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 创建多个版本
    for i in range(2, 4):
        files = {
            "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
        }
        data = {
            "version": f"{i}.0.0",
            "changelog": f"版本{i}"
        }
        response = client.post(f"/api/v1/templates/{template_id}/versions", files=files, data=data)
        assert response.status_code == 200
    
    # 3. 获取版本列表
    response = client.get(f"/api/v1/templates/{template_id}/versions")
    
    # 4. 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["code"] == 0
    assert result["data"]["total"] >= 3  # 至少有3个版本
    assert len(result["data"]["items"]) >= 3


def test_download_template(client, sample_html_content):
    """测试下载模板接口"""
    # 1. 创建模板
    files = {
        "file": ("test_template.html", sample_html_content.encode("utf-8"), "text/html")
    }
    data = {
        "name": "下载测试模板",
        "description": "用于下载测试",
        "tags": "download",
        "version": "1.0.0"
    }
    
    create_response = client.post("/api/v1/templates", files=files, data=data)
    assert create_response.status_code == 200
    template_id = create_response.json()["data"]["template_id"]
    
    # 2. 下载模板
    response = client.get(f"/api/v1/templates/{template_id}/download")
    
    # 3. 验证响应
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html"
    assert "content-disposition" in response.headers
    assert len(response.content) > 0
    assert "<!DOCTYPE html>" in response.content.decode("utf-8")


def test_get_nonexistent_template(client):
    """测试获取不存在的模板"""
    response = client.get("/api/v1/templates/nonexistent_id")
    assert response.status_code == 404


def test_delete_nonexistent_template(client):
    """测试删除不存在的模板"""
    response = client.delete("/api/v1/templates/nonexistent_id")
    assert response.status_code == 404


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])

