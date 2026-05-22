"""
认证相关API路由
包括钉钉OAuth登录、回调处理和获取当前用户信息
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.dingtalk_auth_service import DingTalkAuthService
from app.core.auth_middleware import get_current_user
from typing import Optional
import json


router = APIRouter(prefix="/api/auth", tags=["认证"])
auth_service = DingTalkAuthService()


@router.get("/dingtalk/login")
async def dingtalk_login(state: str = Query(default="default")):
    """
    获取钉钉授权登录URL
    
    Args:
        state: 状态参数,用于防止CSRF攻击
        
    Returns:
        包含授权URL的JSON响应
    """
    try:
        auth_url = auth_service.get_authorization_url(state)
        
        return {
            "success": True,
            "data": {
                "authUrl": auth_url
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成授权URL失败: {str(e)}"
        )


@router.get("/dingtalk/callback")
async def dingtalk_callback(
    code: str = Query(..., description="钉钉授权码"),
    state: str = Query(default="default", description="状态参数"),
    db: AsyncSession = Depends(get_db)
):
    """
    钉钉授权回调处理
    
    Args:
        code: 钉钉授权码
        state: 状态参数
        db: 数据库会话
        
    Returns:
        重定向到前端页面，并通过 URL 参数传递 token
    """
    try:
        # 处理授权回调
        result = await auth_service.handle_callback(code, db)
        
        # 返回 HTML 页面，使用 JavaScript 保存 token 并跳转
        token = result['token']
        # 将用户信息转换为JSON字符串,并进行HTML转义
        user_json = json.dumps(result['user']).replace("'", "\\'").replace('"', '&quot;')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>登录中...</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif;">
                <div style="text-align: center;">
                    <h2>登录成功</h2>
                    <p>正在跳转到系统...</p>
                </div>
            </div>
            <script>
                // 保存 token 和用户信息到 localStorage
                localStorage.setItem('token', '{token}');
                localStorage.setItem('user', `{json.dumps(result['user'])}`);
                
                // 跳转到首页
                window.location.href = '/';
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        # 返回错误页面
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>登录失败</title>
            <meta charset="UTF-8">
        </head>
        <body>
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif;">
                <div style="text-align: center;">
                    <h2>登录失败</h2>
                    <p>{str(e)}</p>
                    <button onclick="window.location.href='/api/auth/dingtalk/login'">重新登录</button>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/me")
async def get_current_user_info(request: Request):
    """
    获取当前登录用户信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        当前用户信息
    """
    try:
        user = get_current_user(request)
        
        return {
            "success": True,
            "data": {
                "user": user
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.post("/logout")
async def logout(request: Request):
    """
    用户登出
    
    注意: JWT是无状态的,实际的登出需要在客户端删除token
    这个端点主要用于记录登出日志或清理服务端资源
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        成功响应
    """
    try:
        user = get_current_user(request)
        
        # 这里可以添加登出日志记录
        # logger.info(f"用户 {user['name']} 登出")
        
        return {
            "success": True,
            "data": {
                "message": "登出成功"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"登出失败: {str(e)}"
        )
