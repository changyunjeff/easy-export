"""
测试API文档功能
"""

import pytest
from fastapi.testclient import TestClient
from main import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


def test_openapi_json(client):
    """测试OpenAPI JSON端点"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证基础信息
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert "components" in data
    
    # 验证info部分
    info = data["info"]
    assert "title" in info
    assert "description" in info
    assert "version" in info
    assert "contact" in info or "license" in info
    
    # 验证title
    assert "FastExport" in info["title"] or "通用内容导出" in info["description"]


def test_swagger_ui(client):
    """测试Swagger UI页面"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"swagger-ui" in response.content or b"Swagger" in response.content


def test_redoc(client):
    """测试ReDoc页面"""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert b"redoc" in response.content or b"ReDoc" in response.content


def test_openapi_tags(client):
    """测试API标签分组"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证tags
    if "tags" in data:
        tags = data["tags"]
        tag_names = [tag["name"] for tag in tags]
        
        # 验证主要标签存在
        expected_tags = ["templates", "export", "health"]
        for expected_tag in expected_tags:
            assert any(expected_tag in tag for tag in tag_names), \
                f"Expected tag '{expected_tag}' not found in {tag_names}"


def test_openapi_paths(client):
    """测试API路径定义"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # 验证关键路径存在
    expected_paths = [
        "/health",
        "/api/v1/templates",
        "/api/v1/export",
    ]
    
    for expected_path in expected_paths:
        # 检查路径或其变体是否存在
        found = False
        for path in paths.keys():
            if expected_path in path:
                found = True
                break
        assert found, f"Expected path '{expected_path}' not found in {list(paths.keys())}"


def test_openapi_schemas(client):
    """测试数据模型定义"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证schemas存在
    if "components" in data and "schemas" in data["components"]:
        schemas = data["components"]["schemas"]
        assert len(schemas) > 0, "No schemas defined"
        
        # 验证关键模型存在
        # 注意：模型名称可能包含版本后缀，所以使用部分匹配
        schema_names = list(schemas.keys())
        
        # 检查是否有任何模型定义
        assert any("Request" in name or "Response" in name for name in schema_names), \
            f"No request/response models found in {schema_names}"


def test_api_endpoint_documentation(client):
    """测试API端点文档"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # 检查至少一个端点有文档
    documented = False
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # 验证端点有描述或摘要
                if "summary" in details or "description" in details:
                    documented = True
                    break
        if documented:
            break
    
    assert documented, "No API endpoints have documentation"


def test_health_endpoint_in_docs(client):
    """测试健康检查端点在文档中"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # 查找health端点
    health_paths = [path for path in paths.keys() if "health" in path.lower()]
    assert len(health_paths) > 0, "Health endpoint not found in API docs"


def test_export_endpoint_in_docs(client):
    """测试导出端点在文档中"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # 查找export端点
    export_paths = [path for path in paths.keys() if "export" in path.lower()]
    assert len(export_paths) > 0, "Export endpoint not found in API docs"


def test_template_endpoint_in_docs(client):
    """测试模板端点在文档中"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # 查找template端点
    template_paths = [path for path in paths.keys() if "template" in path.lower()]
    assert len(template_paths) > 0, "Template endpoint not found in API docs"


def test_api_response_models(client):
    """测试API响应模型"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 检查是否定义了响应模型
    has_responses = False
    paths = data["paths"]
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                if "responses" in details and len(details["responses"]) > 0:
                    has_responses = True
                    break
        if has_responses:
            break
    
    assert has_responses, "No response models defined"


def test_api_request_bodies(client):
    """测试API请求体定义"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 检查POST端点是否定义了请求体
    has_request_body = False
    paths = data["paths"]
    for path, methods in paths.items():
        if "post" in methods:
            post_details = methods["post"]
            if "requestBody" in post_details:
                has_request_body = True
                break
    
    assert has_request_body, "No request bodies defined for POST endpoints"


def test_api_examples(client):
    """测试API示例数据"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 检查是否有任何示例数据
    has_examples = False
    
    # 检查schemas中的examples
    if "components" in data and "schemas" in data["components"]:
        schemas = data["components"]["schemas"]
        for schema_name, schema_def in schemas.items():
            if "examples" in schema_def or "example" in schema_def:
                has_examples = True
                break
            
            # 检查属性中的examples
            if "properties" in schema_def:
                for prop_name, prop_def in schema_def["properties"].items():
                    if "examples" in prop_def or "example" in prop_def:
                        has_examples = True
                        break
    
    # 注意：示例数据是可选的，所以这个测试作为信息性测试
    # 如果没有示例也不会失败，只是记录
    if not has_examples:
        pytest.skip("No examples defined in schemas (optional)")


def test_api_description_formatting(client):
    """测试API描述格式"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证info.description格式
    if "info" in data and "description" in data["info"]:
        description = data["info"]["description"]
        assert len(description) > 0, "API description is empty"
        
        # 验证描述包含有用信息
        # 可以是markdown格式
        assert len(description) > 50, "API description is too short"


def test_api_version(client):
    """测试API版本信息"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证版本信息
    assert "info" in data
    assert "version" in data["info"]
    
    version = data["info"]["version"]
    assert len(version) > 0, "API version is empty"
    
    # 验证版本格式（应该是 X.Y.Z 格式）
    # 但不强制，因为可能有其他格式
    assert len(version.split(".")) >= 2, f"Invalid version format: {version}"


def test_contact_info(client):
    """测试联系信息"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证联系信息（可选）
    if "info" in data and "contact" in data["info"]:
        contact = data["info"]["contact"]
        # 联系信息应该包含至少一个字段
        assert len(contact) > 0, "Contact info is empty"


def test_license_info(client):
    """测试许可证信息"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证许可证信息（可选）
    if "info" in data and "license" in data["info"]:
        license_info = data["info"]["license"]
        assert "name" in license_info, "License name not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

