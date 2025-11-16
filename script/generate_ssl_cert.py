#!/usr/bin/env python3
"""
SSL证书生成工具

用于生成开发和测试环境的自签名SSL证书。

使用方法:
    python script/generate_ssl_cert.py --env dev
    python script/generate_ssl_cert.py --env test
    python script/generate_ssl_cert.py --env prod --days 365
    python script/generate_ssl_cert.py --output certs/custom
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def generate_self_signed_cert(
    output_dir: str = "certs",
    env: str = "dev",
    days: int = 365,
    country: str = "CN",
    state: str = "Beijing",
    locality: str = "Beijing",
    organization: str = "Easy Export",
    common_name: str = "localhost",
) -> tuple[str, str]:
    """
    生成自签名SSL证书
    
    Args:
        output_dir: 证书输出目录
        env: 环境名称 (dev/test/prod)
        days: 证书有效期（天）
        country: 国家代码
        state: 省/州
        locality: 城市
        organization: 组织名称
        common_name: 通用名称（域名）
    
    Returns:
        (cert_file, key_file): 证书文件路径和密钥文件路径
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("❌ 缺少依赖: cryptography")
        print("请安装: pip install cryptography")
        sys.exit(1)
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 输出目录: {output_path.absolute()}")
    
    # 生成私钥
    print("🔑 生成RSA私钥...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # 创建证书主题
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    # 创建证书
    print("📜 生成自签名证书...")
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
        datetime.utcnow() + timedelta(days=days)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(common_name),
            x509.DNSName(f"*.{common_name}") if "." in common_name else x509.DNSName("localhost"),
            x509.IPAddress(__import__('ipaddress').IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # 保存私钥
    key_file = output_path / f"{env}-key.pem"
    print(f"💾 保存私钥: {key_file}")
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # 保存证书
    cert_file = output_path / f"{env}-cert.pem"
    print(f"💾 保存证书: {cert_file}")
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"\n✅ SSL证书生成成功！")
    print(f"   证书文件: {cert_file}")
    print(f"   私钥文件: {key_file}")
    print(f"   有效期: {days} 天")
    print(f"   过期时间: {(datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # 生成配置提示
    print(f"\n📝 配置提示:")
    print(f"   在 config.{env}.yaml 中设置:")
    print(f"   ssl:")
    print(f"     enabled: true")
    print(f"     certfile: \"{cert_file}\"")
    print(f"     keyfile: \"{key_file}\"")
    
    return str(cert_file), str(key_file)


def main():
    parser = argparse.ArgumentParser(
        description="生成自签名SSL证书（用于开发和测试环境）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成开发环境证书（默认）
  python script/generate_ssl_cert.py
  
  # 生成测试环境证书
  python script/generate_ssl_cert.py --env test
  
  # 生成有效期为730天的生产环境证书
  python script/generate_ssl_cert.py --env prod --days 730
  
  # 自定义域名和组织
  python script/generate_ssl_cert.py --common-name example.com --organization "My Company"
  
  # 指定输出目录
  python script/generate_ssl_cert.py --output /path/to/certs

注意:
  1. 生成的证书是自签名证书，仅用于开发和测试
  2. 生产环境应使用受信任的CA签发的证书（如Let's Encrypt）
  3. 浏览器会提示自签名证书不受信任，这是正常的
        """
    )
    
    parser.add_argument(
        "--env",
        choices=["dev", "test", "prod"],
        default="dev",
        help="环境名称 (默认: dev)"
    )
    
    parser.add_argument(
        "--output",
        default="certs",
        help="证书输出目录 (默认: certs)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="证书有效期（天）(默认: 365)"
    )
    
    parser.add_argument(
        "--common-name",
        default="localhost",
        help="证书通用名称/域名 (默认: localhost)"
    )
    
    parser.add_argument(
        "--organization",
        default="Easy Export",
        help="组织名称 (默认: Easy Export)"
    )
    
    parser.add_argument(
        "--country",
        default="CN",
        help="国家代码 (默认: CN)"
    )
    
    parser.add_argument(
        "--state",
        default="Beijing",
        help="省/州 (默认: Beijing)"
    )
    
    parser.add_argument(
        "--locality",
        default="Beijing",
        help="城市 (默认: Beijing)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔐 SSL证书生成工具")
    print("=" * 60)
    print(f"环境: {args.env}")
    print(f"通用名称: {args.common_name}")
    print(f"组织: {args.organization}")
    print(f"有效期: {args.days} 天")
    print("=" * 60)
    print()
    
    try:
        generate_self_signed_cert(
            output_dir=args.output,
            env=args.env,
            days=args.days,
            country=args.country,
            state=args.state,
            locality=args.locality,
            organization=args.organization,
            common_name=args.common_name,
        )
        
        print("\n" + "=" * 60)
        print("⚠️  重要提示:")
        print("=" * 60)
        print("1. 这是自签名证书，浏览器会显示安全警告")
        print("2. 仅用于开发和测试环境")
        print("3. 生产环境请使用受信任的CA证书")
        print("4. 可以使用Let's Encrypt免费获取受信任证书")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 生成证书失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

