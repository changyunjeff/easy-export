"""
手动验证API文档功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app

def main():
    print("正在创建FastAPI应用...")
    app = create_app()
    
    print("\n=== 应用信息 ===")
    print(f"Title: {app.title}")
    print(f"Description 长度: {len(app.description) if app.description else 0} 字符")
    print(f"Version: {app.version}")
    print(f"OpenAPI URL: {app.openapi_url}")
    print(f"Docs URL: {app.docs_url}")
    print(f"ReDoc URL: {app.redoc_url}")
    
    print("\n=== OpenAPI Tags ===")
    if app.openapi_tags:
        for tag in app.openapi_tags:
            print(f"- {tag.get('name')}: {tag.get('description', '')[:50]}...")
    else:
        print("没有定义tags")
    
    print("\n=== Swagger UI 参数 ===")
    if app.swagger_ui_parameters:
        for key, value in list(app.swagger_ui_parameters.items())[:5]:
            print(f"- {key}: {value}")
    else:
        print("没有定义Swagger UI参数")
    
    print("\n=== 路由统计 ===")
    routes_count = len(app.routes)
    print(f"总路由数: {routes_count}")
    
    # 统计不同类型的路由
    api_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/' in r.path]
    health_routes = [r for r in app.routes if hasattr(r, 'path') and 'health' in r.path]
    
    print(f"API路由数: {len(api_routes)}")
    print(f"健康检查路由数: {len(health_routes)}")
    
    print("\n=== 主要API路由 ===")
    for route in app.routes[:20]:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods_str = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"{methods_str:15} {route.path}")
    
    print("\n✅ API文档功能验证完成")
    print(f"\n启动服务后可访问:")
    print(f"- Swagger UI: http://localhost:8000{app.docs_url}")
    print(f"- ReDoc: http://localhost:8000{app.redoc_url}")
    print(f"- OpenAPI JSON: http://localhost:8000{app.openapi_url}")

if __name__ == "__main__":
    main()

