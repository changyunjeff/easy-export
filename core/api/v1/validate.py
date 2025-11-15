"""
校验接口
提供文档格式校验功能
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix
from core.service.validate_service import ValidateService

logger = logging.getLogger(__name__)

validate_router = APIRouter(
    prefix=f"{get_api_prefix()}/validate",
    tags=["validate"],
)

# 创建服务实例
validate_service = ValidateService()


class ValidateRequest(BaseModel):
    """校验请求"""
    file_path: str = Field(..., description="文件路径")
    rules: Optional[Dict[str, Any]] = Field(
        default=None,
        description="校验规则（check_links, check_style, expected_table_rows, required_fields等）",
    )


class ValidateResponse(BaseModel):
    """校验响应"""
    file_path: str = Field(..., description="文件路径")
    passed: bool = Field(..., description="是否通过")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")
    summary: Dict[str, Any] = Field(..., description="汇总信息")


@validate_router.post("", response_model=HttpResponse)
async def validate_document(request: ValidateRequest):
    """
    校验文档
    
    - **file_path**: 文件路径
    - **rules**: 校验规则
      - **required_fields**: 必填字段列表
      - **expected_table_rows**: 预期表格行数
      - **check_links**: 是否检查链接有效性（默认False）
      - **check_style**: 是否检查样式统一性（默认False）
      - **link_timeout_sec**: 链接检查超时时间（秒，默认3）
    
    ## 示例请求
    
    ```json
    {
      "file_path": "static/outputs/report.html",
      "rules": {
        "required_fields": ["订单号", "客户名称", "2024"],
        "expected_table_rows": 10,
        "check_links": true,
        "check_style": true,
        "link_timeout_sec": 3
      }
    }
    ```
    
    ## 响应示例
    
    ```json
    {
      "code": 0,
      "msg": "success",
      "data": {
        "file_path": "static/outputs/report.html",
        "passed": true,
        "errors": [],
        "warnings": [
          {
            "type": "slow_link",
            "message": "链接响应较慢: https://example.com (2.5秒)",
            "detail": {
              "url": "https://example.com",
              "elapsed": 2.5
            }
          }
        ],
        "summary": {
          "total_checks": 1,
          "passed_checks": 0,
          "failed_checks": 0,
          "warning_checks": 1
        }
      }
    }
    ```
    """
    try:
        logger.info(f"开始校验文档: {request.file_path}")
        
        # 设置默认规则
        rules = request.rules or {}
        
        # 执行校验
        result = validate_service.validate_document(
            file_path=request.file_path,
            rules=rules
        )
        
        # 构建响应数据
        result_dict = result.to_dict()
        response_data = {
            "file_path": request.file_path,
            **result_dict
        }
        
        logger.info(f"文档校验完成: passed={result.passed}, errors={len(result.errors)}, warnings={len(result.warnings)}")
        
        return OkWithDetail(data=response_data)
    
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        return ErrorWithDetail(
            code=40403,
            msg="文件不存在",
            data={"file_path": request.file_path, "error": str(e)}
        )
    
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return ErrorWithDetail(
            code=40004,
            msg="文件格式不支持",
            data={"file_path": request.file_path, "error": str(e)}
        )
    
    except Exception as e:
        logger.error(f"文档校验失败: {e}", exc_info=True)
        return ErrorWithDetail(
            code=50040,
            msg="文档校验失败",
            data={"file_path": request.file_path, "error": str(e)}
        )

