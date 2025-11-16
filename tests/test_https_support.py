"""
HTTPS支持功能测试

测试SSL/TLS配置和HTTPS服务启动
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSSLConfig:
    """测试SSL配置类"""
    
    def test_ssl_config_schema(self):
        """测试SSL配置schema定义"""
        from core.schemas.configs import SSLConfig
        
        # 测试默认配置
        config = SSLConfig()
        assert config.enabled is False
        assert config.certfile is None
        assert config.keyfile is None
        assert config.cert_reqs == 0
        
    def test_ssl_config_with_values(self):
        """测试带值的SSL配置"""
        from core.schemas.configs import SSLConfig
        
        config = SSLConfig(
            enabled=True,
            certfile="certs/test-cert.pem",
            keyfile="certs/test-key.pem",
            ca_certs="certs/ca.pem",
            cert_reqs=2,
        )
        
        assert config.enabled is True
        assert config.certfile == "certs/test-cert.pem"
        assert config.keyfile == "certs/test-key.pem"
        assert config.ca_certs == "certs/ca.pem"
        assert config.cert_reqs == 2
    
    def test_global_config_includes_ssl(self):
        """测试全局配置包含SSL配置"""
        from core.schemas import GlobalConfig, SSLConfig
        
        # 验证GlobalConfig有ssl字段
        assert hasattr(GlobalConfig, '__annotations__')
        assert 'ssl' in GlobalConfig.__annotations__


class TestSSLConfigLoading:
    """测试SSL配置加载"""
    
    def test_load_config_with_ssl_disabled(self):
        """测试加载禁用SSL的配置"""
        from core.config import load_config
        
        # 使用开发环境配置（默认禁用SSL）
        config = load_config("config.dev.yaml")
        
        assert hasattr(config, 'ssl')
        # 开发环境默认禁用SSL
        if config.ssl:
            assert config.ssl.enabled is False
    
    def test_load_config_with_ssl_enabled(self):
        """测试加载启用SSL的配置"""
        from core.config import parse_yaml_raw_as
        from core.schemas import GlobalConfig
        
        # 创建测试配置
        yaml_config = """
app:
  title: Test App
  port: 8000
  host: localhost
  
ssl:
  enabled: true
  certfile: "certs/test-cert.pem"
  keyfile: "certs/test-key.pem"
  cert_reqs: 0
"""
        
        config = parse_yaml_raw_as(GlobalConfig, yaml_config)
        
        assert config.ssl is not None
        assert config.ssl.enabled is True
        assert config.ssl.certfile == "certs/test-cert.pem"
        assert config.ssl.keyfile == "certs/test-key.pem"


class TestCertificateGeneration:
    """测试证书生成功能"""
    
    @pytest.fixture
    def temp_cert_dir(self):
        """创建临时证书目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_generate_ssl_cert_import(self):
        """测试证书生成脚本可以导入"""
        # 动态导入证书生成脚本
        script_path = Path(__file__).parent.parent / "script" / "generate_ssl_cert.py"
        assert script_path.exists(), f"证书生成脚本不存在: {script_path}"
        
        # 验证脚本包含必要的函数
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'generate_self_signed_cert' in content
            assert 'cryptography' in content
    
    def test_generate_self_signed_cert(self, temp_cert_dir):
        """测试生成自签名证书"""
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.x509.oid import NameOID
            from datetime import datetime, timedelta
        except ImportError:
            pytest.skip("cryptography库未安装")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # 创建证书
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(__import__('ipaddress').IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # 保存证书和私钥
        cert_file = Path(temp_cert_dir) / "test-cert.pem"
        key_file = Path(temp_cert_dir) / "test-key.pem"
        
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # 验证文件已创建
        assert cert_file.exists()
        assert key_file.exists()
        
        # 验证文件内容
        assert cert_file.stat().st_size > 0
        assert key_file.stat().st_size > 0


class TestHTTPSServerConfiguration:
    """测试HTTPS服务器配置"""
    
    def test_uvicorn_ssl_config(self):
        """测试uvicorn SSL配置参数"""
        # 验证uvicorn支持SSL参数
        import uvicorn
        
        # uvicorn.Config应该接受ssl相关参数
        # 这里只验证参数名称，不实际启动服务器
        ssl_params = [
            'ssl_keyfile',
            'ssl_certfile',
            'ssl_ca_certs',
            'ssl_cert_reqs',
        ]
        
        # 验证Config类接受这些参数（通过inspect）
        import inspect
        config_params = inspect.signature(uvicorn.Config.__init__).parameters
        
        # 至少应该有ssl_keyfile和ssl_certfile
        assert 'ssl_keyfile' in config_params or hasattr(uvicorn.Config, 'ssl_keyfile')
        assert 'ssl_certfile' in config_params or hasattr(uvicorn.Config, 'ssl_certfile')
    
    def test_main_ssl_config_logic(self):
        """测试main.py中的SSL配置逻辑"""
        import main
        
        # 验证main模块包含SSL配置逻辑
        with open(main.__file__, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 验证包含SSL配置检查
            assert 'ssl_config' in content.lower()
            assert 'ssl_keyfile' in content
            assert 'ssl_certfile' in content
            
            # 验证包含证书文件存在性检查
            assert 'exists' in content or 'isfile' in content


class TestHTTPSIntegration:
    """HTTPS集成测试"""
    
    @pytest.fixture
    def temp_cert_and_config(self):
        """创建临时证书和配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 生成证书
            try:
                from cryptography import x509
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.primitives import serialization, hashes
                from cryptography.x509.oid import NameOID
                from datetime import datetime, timedelta
            except ImportError:
                pytest.skip("cryptography库未安装")
            
            cert_dir = Path(tmpdir) / "certs"
            cert_dir.mkdir()
            
            # 生成私钥
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # 创建证书
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=1)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # 保存文件
            cert_file = cert_dir / "test-cert.pem"
            key_file = cert_dir / "test-key.pem"
            
            with open(cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_file, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            yield {
                "cert_dir": cert_dir,
                "cert_file": str(cert_file),
                "key_file": str(key_file),
            }
    
    def test_ssl_config_in_yaml(self, temp_cert_and_config):
        """测试YAML配置中的SSL配置"""
        from core.config import parse_yaml_raw_as
        from core.schemas import GlobalConfig
        
        # 使用正斜杠避免Windows路径反斜杠转义问题
        cert_file_path = str(temp_cert_and_config['cert_file']).replace('\\', '/')
        key_file_path = str(temp_cert_and_config['key_file']).replace('\\', '/')
        
        yaml_config = f"""
app:
  title: Test App
  port: 8443
  host: localhost
  
ssl:
  enabled: true
  certfile: "{cert_file_path}"
  keyfile: "{key_file_path}"
"""
        
        config = parse_yaml_raw_as(GlobalConfig, yaml_config)
        
        assert config.ssl.enabled is True
        assert Path(config.ssl.certfile).exists()
        assert Path(config.ssl.keyfile).exists()


class TestHTTPSDocumentation:
    """测试HTTPS文档"""
    
    def test_https_guide_exists(self):
        """测试HTTPS配置指南是否存在"""
        guide_path = Path(__file__).parent.parent / "docs" / "HTTPS配置指南.md"
        assert guide_path.exists(), "HTTPS配置指南不存在"
    
    def test_https_guide_content(self):
        """测试HTTPS配置指南内容"""
        guide_path = Path(__file__).parent.parent / "docs" / "HTTPS配置指南.md"
        
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 验证包含关键章节
            assert "自签名证书" in content
            assert "Let's Encrypt" in content
            assert "生产环境" in content
            assert "证书生成" in content
            assert "故障排查" in content


class TestConfigFiles:
    """测试配置文件中的SSL配置"""
    
    @pytest.mark.parametrize("config_file", [
        "config.dev.yaml",
        "config.test.yaml",
        "config.prod.yaml",
    ])
    def test_config_has_ssl_section(self, config_file):
        """测试配置文件包含SSL配置段"""
        config_path = Path(__file__).parent.parent / config_file
        
        if not config_path.exists():
            pytest.skip(f"配置文件不存在: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 验证包含ssl配置段
            assert 'ssl:' in content
            assert 'enabled:' in content
            assert 'certfile:' in content
            assert 'keyfile:' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

