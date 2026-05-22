"""
AI配置模块
支持DeepSeek API和自部署模型(通过OpenAI兼容API)
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

from app.core.config import settings


class AIConfig(BaseModel):
    """
    AI配置类
    
    支持两种AI服务提供商:
    1. DeepSeek API - 官方DeepSeek服务
    2. Custom - 自部署模型(通过OpenAI兼容API,如vLLM、Ollama、LocalAI)
    """
    
    provider: Literal["deepseek", "custom"] = Field(
        default="deepseek",
        description="AI服务提供商: deepseek 或 custom"
    )
    
    api_base: str = Field(
        default="https://api.deepseek.com/v1",
        description="API基础URL"
    )
    
    api_key: str = Field(
        default="",
        description="API密钥"
    )
    
    model: str = Field(
        default="deepseek-chat",
        description="模型名称"
    )
    
    timeout: int = Field(
        default=30,
        description="请求超时时间(秒)"
    )
    
    max_tokens: int = Field(
        default=2000,
        description="最大生成token数"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成温度(0.0-2.0)"
    )
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """
        从环境变量加载配置
        
        Returns:
            AIConfig实例
        """
        return cls(
            provider=settings.AI_PROVIDER,
            api_base=settings.AI_API_BASE,
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL,
            timeout=settings.AI_TIMEOUT
        )
    
    def create_client(self) -> AsyncOpenAI:
        """
        创建OpenAI兼容的异步客户端
        
        Returns:
            AsyncOpenAI客户端实例
        """
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout
        )
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        验证配置是否有效
        
        Returns:
            (是否有效, 错误信息)
        """
        # 检查API基础URL
        if not self.api_base:
            return False, "API基础URL不能为空"
        
        # 检查API密钥(某些自部署模型可能不需要)
        if self.provider == "deepseek" and not self.api_key:
            return False, "DeepSeek API密钥不能为空"
        
        # 检查模型名称
        if not self.model:
            return False, "模型名称不能为空"
        
        # 检查超时时间
        if self.timeout <= 0:
            return False, "超时时间必须大于0"
        
        return True, None
    
    def get_provider_info(self) -> dict:
        """
        获取提供商信息
        
        Returns:
            提供商信息字典
        """
        provider_info = {
            "deepseek": {
                "name": "DeepSeek",
                "description": "DeepSeek官方API服务",
                "default_base_url": "https://api.deepseek.com/v1",
                "default_model": "deepseek-chat",
                "requires_api_key": True
            },
            "custom": {
                "name": "自部署模型",
                "description": "通过OpenAI兼容API接入的自部署模型",
                "default_base_url": "http://localhost:8000/v1",
                "default_model": "qwen2.5-7b-instruct",
                "requires_api_key": False
            }
        }
        
        return provider_info.get(self.provider, {})
    
    def __repr__(self) -> str:
        """字符串表示"""
        # 隐藏API密钥
        masked_key = f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***"
        return (
            f"AIConfig(provider={self.provider}, "
            f"api_base={self.api_base}, "
            f"model={self.model}, "
            f"api_key={masked_key})"
        )


# 创建全局AI配置实例
ai_config = AIConfig.from_env()


def get_ai_client() -> AsyncOpenAI:
    """
    获取AI客户端实例
    
    Returns:
        AsyncOpenAI客户端
    """
    return ai_config.create_client()


def switch_ai_provider(
    provider: Literal["deepseek", "custom"],
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> AIConfig:
    """
    切换AI服务提供商
    
    Args:
        provider: 提供商类型
        api_base: API基础URL(可选)
        api_key: API密钥(可选)
        model: 模型名称(可选)
        
    Returns:
        新的AIConfig实例
    """
    global ai_config
    
    # 获取提供商默认配置
    provider_info = AIConfig(provider=provider).get_provider_info()
    
    # 创建新配置
    new_config = AIConfig(
        provider=provider,
        api_base=api_base or provider_info.get("default_base_url", ai_config.api_base),
        api_key=api_key or ai_config.api_key,
        model=model or provider_info.get("default_model", ai_config.model),
        timeout=ai_config.timeout,
        max_tokens=ai_config.max_tokens,
        temperature=ai_config.temperature
    )
    
    # 验证配置
    is_valid, error_msg = new_config.validate_config()
    if not is_valid:
        raise ValueError(f"AI配置无效: {error_msg}")
    
    # 更新全局配置
    ai_config = new_config
    
    return ai_config
