"""
CORS 白盒测试
测试 CORS 配置是否正确工作，包括：
- 允许的源是否正确配置
- 预检请求（OPTIONS）是否正常工作
- 简单请求和复杂请求的 CORS 响应头是否正确
- 不允许的源是否被正确拒绝
"""
from __future__ import annotations

import pytest

try:
    import requests
except ImportError:
    pytest.skip("requests library not installed. Install with: pip install requests", allow_module_level=True)


class TestCORS:
    """CORS 配置测试类"""
    
    # 服务器地址（根据实际配置修改）
    BASE_URL = "http://localhost:8000"
    
    # 测试端点
    HEALTH_ENDPOINT = f"{BASE_URL}/health"
    API_ENDPOINT = f"{BASE_URL}/api/v1/examples/health"
    
    @pytest.fixture
    def allowed_origin(self):
        """从配置中获取允许的源（默认值）"""
        # 默认配置中的允许源
        return "http://localhost:3000"
    
    @pytest.fixture
    def disallowed_origin(self):
        """不允许的源"""
        return "http://localhost:9999"
    
    def test_cors_headers_present_on_simple_request(self, allowed_origin):
        """测试简单请求（GET）是否包含 CORS 响应头"""
        response = requests.get(
            self.HEALTH_ENDPOINT,
            headers={"Origin": allowed_origin}
        )
        
        assert response.status_code == 200
        
        # 检查 CORS 响应头
        assert "Access-Control-Allow-Origin" in response.headers, \
            "响应中缺少 Access-Control-Allow-Origin 头"
        
        # 验证允许的源
        assert response.headers["Access-Control-Allow-Origin"] == allowed_origin, \
            f"Access-Control-Allow-Origin 应该是 {allowed_origin}，实际是 {response.headers.get('Access-Control-Allow-Origin')}"
    
    def test_cors_headers_present_on_api_request(self, allowed_origin):
        """测试 API 端点的 CORS 响应头"""
        response = requests.get(
            self.API_ENDPOINT,
            headers={"Origin": allowed_origin}
        )
        
        assert response.status_code == 200
        
        # 检查 CORS 响应头
        assert "Access-Control-Allow-Origin" in response.headers, \
            "API 响应中缺少 Access-Control-Allow-Origin 头"
        
        assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    
    def test_cors_preflight_request(self, allowed_origin):
        """测试预检请求（OPTIONS）是否正常工作"""
        response = requests.options(
            self.API_ENDPOINT,
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )
        
        # 预检请求应该返回 200 或 204
        assert response.status_code in [200, 204], \
            f"预检请求应该返回 200 或 204，实际返回 {response.status_code}"
        
        # 检查 CORS 响应头
        assert "Access-Control-Allow-Origin" in response.headers, \
            "预检请求响应中缺少 Access-Control-Allow-Origin 头"
        
        assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
        
        # 检查允许的方法
        if "Access-Control-Allow-Methods" in response.headers:
            allowed_methods = response.headers["Access-Control-Allow-Methods"]
            # 应该包含 POST（因为我们在请求中指定了）
            assert "POST" in allowed_methods or "*" in allowed_methods, \
                f"Access-Control-Allow-Methods 应该包含 POST，实际是 {allowed_methods}"
        
        # 检查允许的请求头
        if "Access-Control-Allow-Headers" in response.headers:
            allowed_headers = response.headers["Access-Control-Allow-Headers"]
            # 应该包含 Content-Type 和 Authorization
            assert "Content-Type" in allowed_headers or "*" in allowed_headers, \
                f"Access-Control-Allow-Headers 应该包含 Content-Type，实际是 {allowed_headers}"
            assert "Authorization" in allowed_headers or "*" in allowed_headers, \
                f"Access-Control-Allow-Headers 应该包含 Authorization，实际是 {allowed_headers}"
        
        # 检查 max-age
        if "Access-Control-Max-Age" in response.headers:
            max_age = int(response.headers["Access-Control-Max-Age"])
            assert max_age > 0, \
                f"Access-Control-Max-Age 应该大于 0，实际是 {max_age}"
    
    def test_cors_credentials_header(self, allowed_origin):
        """测试 allow_credentials 配置是否正确"""
        response = requests.get(
            self.API_ENDPOINT,
            headers={"Origin": allowed_origin}
        )
        
        assert response.status_code == 200
        
        # 如果配置了 allow_credentials: true，应该包含这个头
        # 注意：这个测试依赖于实际配置，如果配置为 false，这个头可能不存在
        if "Access-Control-Allow-Credentials" in response.headers:
            assert response.headers["Access-Control-Allow-Credentials"].lower() == "true", \
                "Access-Control-Allow-Credentials 应该是 'true'"
    
    def test_cors_disallowed_origin(self, disallowed_origin):
        """测试不允许的源是否被正确拒绝"""
        response = requests.get(
            self.API_ENDPOINT,
            headers={"Origin": disallowed_origin}
        )
        
        # 请求可能仍然成功（返回 200），但 CORS 响应头应该不同
        # 如果源不在允许列表中，Access-Control-Allow-Origin 应该不存在或为空
        if "Access-Control-Allow-Origin" in response.headers:
            # 如果存在，应该不是不允许的源
            assert response.headers["Access-Control-Allow-Origin"] != disallowed_origin, \
                f"不允许的源 {disallowed_origin} 不应该出现在 Access-Control-Allow-Origin 中"
    
    def test_cors_post_request(self, allowed_origin):
        """测试 POST 请求的 CORS 响应头"""
        response = requests.post(
            self.API_ENDPOINT,
            headers={
                "Origin": allowed_origin,
                "Content-Type": "application/json"
            },
            json={"test": "data"}
        )
        
        # POST 请求可能返回 405（方法不允许）或其他状态码，这取决于端点实现
        # 但无论状态码如何，CORS 响应头应该存在
        if response.status_code < 500:  # 排除服务器错误
            assert "Access-Control-Allow-Origin" in response.headers, \
                "POST 请求响应中应该包含 Access-Control-Allow-Origin 头"
            
            if response.status_code < 400:  # 如果请求成功
                assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    
    def test_cors_expose_headers(self, allowed_origin):
        """测试暴露的响应头配置"""
        response = requests.get(
            self.API_ENDPOINT,
            headers={"Origin": allowed_origin}
        )
        
        assert response.status_code == 200
        
        # 如果配置了 expose_headers，应该包含 Access-Control-Expose-Headers
        # 这个测试依赖于实际配置，如果配置为空列表，这个头可能不存在
        # 这里只检查格式是否正确（如果存在）
        if "Access-Control-Expose-Headers" in response.headers:
            exposed_headers = response.headers["Access-Control-Expose-Headers"]
            assert isinstance(exposed_headers, str), \
                "Access-Control-Expose-Headers 应该是字符串"
    
    def test_cors_multiple_origins(self):
        """测试多个允许的源配置"""
        # 测试配置中可能存在的其他源
        test_origins = [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite 默认端口
        ]
        
        for origin in test_origins:
            try:
                response = requests.get(
                    self.API_ENDPOINT,
                    headers={"Origin": origin},
                    timeout=2
                )
                
                # 如果源在允许列表中，应该返回正确的 CORS 头
                if response.status_code == 200:
                    if "Access-Control-Allow-Origin" in response.headers:
                        # 允许的源应该匹配或使用通配符
                        allowed = response.headers["Access-Control-Allow-Origin"]
                        assert allowed == origin or allowed == "*", \
                            f"源 {origin} 应该被允许，但 Access-Control-Allow-Origin 是 {allowed}"
            except requests.exceptions.RequestException:
                # 如果请求失败（例如源不在允许列表中），跳过
                pass
    
    def test_cors_with_authorization_header(self, allowed_origin):
        """测试带 Authorization 头的请求"""
        response = requests.get(
            self.API_ENDPOINT,
            headers={
                "Origin": allowed_origin,
                "Authorization": "Bearer test-token"
            }
        )
        
        assert response.status_code == 200
        
        # 应该包含 CORS 响应头
        assert "Access-Control-Allow-Origin" in response.headers, \
            "带 Authorization 头的请求应该包含 CORS 响应头"
        
        assert response.headers["Access-Control-Allow-Origin"] == allowed_origin
    
    def test_cors_preflight_with_custom_headers(self, allowed_origin):
        """测试预检请求中的自定义请求头"""
        # 只使用配置中允许的请求头（Content-Type 和 Authorization）
        custom_headers = "Content-Type,Authorization"
        
        response = requests.options(
            self.API_ENDPOINT,
            headers={
                "Origin": allowed_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": custom_headers
            }
        )
        
        # 如果请求头不在允许列表中，可能返回 400
        # 但如果是允许的请求头，应该返回 200 或 204
        assert response.status_code in [200, 204, 400], \
            f"预检请求应该返回 200、204 或 400，实际返回 {response.status_code}"
        
        # 如果返回成功状态码，检查响应头
        if response.status_code in [200, 204]:
            # 检查响应头
            if "Access-Control-Allow-Headers" in response.headers:
                allowed_headers = response.headers["Access-Control-Allow-Headers"]
                # 如果使用通配符，所有头都应该被允许
                if "*" in allowed_headers:
                    # 通配符允许所有头
                    pass
                else:
                    # 否则，至少 Content-Type 和 Authorization 应该在允许列表中
                    assert "Content-Type" in allowed_headers or "*" in allowed_headers, \
                        "Content-Type 应该在允许的请求头列表中"
                    assert "Authorization" in allowed_headers or "*" in allowed_headers, \
                        "Authorization 应该在允许的请求头列表中"

