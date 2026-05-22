"""
AI配置模块单元测试
"""
import pytest
from unittest.mock import patch, MagicMock
from openai import AsyncOpenAI

from app.core.ai_config import AIConfig, get_ai_client, switch_ai_provider, ai_config


class TestAIConfig:
    """AI配置类测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = AIConfig()
        
        assert config.provider == "deepseek"
        assert config.api_base == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"
        assert config.timeout == 30
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = AIConfig(
            provider="custom",
            api_base="http://localhost:8000/v1",
            api_key="test-key",
            model="qwen2.5-7b-instruct",
            timeout=60
        )
        
        assert config.provider == "custom"
        assert config.api_base == "http://localhost:8000/v1"
        assert config.api_key == "test-key"
        assert config.model == "qwen2.5-7b-instruct"
        assert config.timeout == 60
    
    @patch('app.core.ai_config.settings')
    def test_from_env(self, mock_settings):
        """测试从环境变量加载配置"""
        mock_settings.AI_PROVIDER = "deepseek"
        mock_settings.AI_API_BASE = "https://api.deepseek.com/v1"
        mock_settings.AI_API_KEY = "sk-test-key"
        mock_settings.AI_MODEL = "deepseek-chat"
        mock_settings.AI_TIMEOUT = 30
        
        config = AIConfig.from_env()
        
        assert config.provider == "deepseek"
        assert config.api_base == "https://api.deepseek.com/v1"
        assert config.api_key == "sk-test-key"
        assert config.model == "deepseek-chat"
        assert config.timeout == 30
    
    def test_create_client(self):
        """测试创建OpenAI客户端"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test-key",
            model="deepseek-chat"
        )
        
        client = config.create_client()
        
        assert isinstance(client, AsyncOpenAI)
        assert client.api_key == "sk-test-key"
        assert client.base_url == "https://api.deepseek.com/v1"
    
    def test_validate_config_success(self):
        """测试配置验证成功"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test-key",
            model="deepseek-chat"
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_config_missing_api_base(self):
        """测试配置验证失败 - 缺少API基础URL"""
        config = AIConfig(
            provider="deepseek",
            api_base="",
            api_key="sk-test-key",
            model="deepseek-chat"
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is False
        assert "API基础URL不能为空" in error_msg
    
    def test_validate_config_missing_api_key_for_deepseek(self):
        """测试配置验证失败 - DeepSeek缺少API密钥"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="",
            model="deepseek-chat"
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is False
        assert "DeepSeek API密钥不能为空" in error_msg
    
    def test_validate_config_custom_without_api_key(self):
        """测试配置验证成功 - 自部署模型可以没有API密钥"""
        config = AIConfig(
            provider="custom",
            api_base="http://localhost:8000/v1",
            api_key="",
            model="qwen2.5-7b-instruct"
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_config_missing_model(self):
        """测试配置验证失败 - 缺少模型名称"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test-key",
            model=""
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is False
        assert "模型名称不能为空" in error_msg
    
    def test_validate_config_invalid_timeout(self):
        """测试配置验证失败 - 无效的超时时间"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test-key",
            model="deepseek-chat",
            timeout=0
        )
        
        is_valid, error_msg = config.validate_config()
        
        assert is_valid is False
        assert "超时时间必须大于0" in error_msg
    
    def test_get_provider_info_deepseek(self):
        """测试获取DeepSeek提供商信息"""
        config = AIConfig(provider="deepseek")
        
        info = config.get_provider_info()
        
        assert info["name"] == "DeepSeek"
        assert info["description"] == "DeepSeek官方API服务"
        assert info["default_base_url"] == "https://api.deepseek.com/v1"
        assert info["default_model"] == "deepseek-chat"
        assert info["requires_api_key"] is True
    
    def test_get_provider_info_custom(self):
        """测试获取自部署模型提供商信息"""
        config = AIConfig(provider="custom")
        
        info = config.get_provider_info()
        
        assert info["name"] == "自部署模型"
        assert info["description"] == "通过OpenAI兼容API接入的自部署模型"
        assert info["default_base_url"] == "http://localhost:8000/v1"
        assert info["default_model"] == "qwen2.5-7b-instruct"
        assert info["requires_api_key"] is False
    
    def test_repr_masks_api_key(self):
        """测试字符串表示隐藏API密钥"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-1234567890abcdef",
            model="deepseek-chat"
        )
        
        repr_str = repr(config)
        
        assert "sk-12345..." in repr_str
        assert "sk-1234567890abcdef" not in repr_str
    
    def test_repr_short_api_key(self):
        """测试字符串表示处理短API密钥"""
        config = AIConfig(
            provider="deepseek",
            api_base="https://api.deepseek.com/v1",
            api_key="short",
            model="deepseek-chat"
        )
        
        repr_str = repr(config)
        
        assert "***" in repr_str
        assert "short" not in repr_str


class TestAIConfigFunctions:
    """AI配置函数测试"""
    
    def test_get_ai_client(self):
        """测试获取AI客户端"""
        client = get_ai_client()
        
        assert isinstance(client, AsyncOpenAI)
    
    @patch('app.core.ai_config.ai_config')
    def test_switch_ai_provider_to_custom(self, mock_ai_config):
        """测试切换到自部署模型"""
        mock_ai_config.api_key = "test-key"
        mock_ai_config.timeout = 30
        mock_ai_config.max_tokens = 2000
        mock_ai_config.temperature = 0.7
        
        new_config = switch_ai_provider(
            provider="custom",
            api_base="http://localhost:8000/v1",
            model="qwen2.5-7b-instruct"
        )
        
        assert new_config.provider == "custom"
        assert new_config.api_base == "http://localhost:8000/v1"
        assert new_config.model == "qwen2.5-7b-instruct"
    
    @patch('app.core.ai_config.ai_config')
    def test_switch_ai_provider_to_deepseek(self, mock_ai_config):
        """测试切换到DeepSeek"""
        mock_ai_config.api_key = "sk-test-key"
        mock_ai_config.timeout = 30
        mock_ai_config.max_tokens = 2000
        mock_ai_config.temperature = 0.7
        
        new_config = switch_ai_provider(
            provider="deepseek",
            api_key="sk-new-key"
        )
        
        assert new_config.provider == "deepseek"
        assert new_config.api_key == "sk-new-key"
    
    @patch('app.core.ai_config.ai_config')
    def test_switch_ai_provider_invalid_config(self, mock_ai_config):
        """测试切换到无效配置"""
        mock_ai_config.api_key = ""
        mock_ai_config.api_base = "https://api.deepseek.com/v1"
        mock_ai_config.timeout = 30
        mock_ai_config.max_tokens = 2000
        mock_ai_config.temperature = 0.7
        
        with pytest.raises(ValueError, match="AI配置无效"):
            switch_ai_provider(
                provider="deepseek",
                api_key=""  # DeepSeek需要API密钥
            )


class TestAIConfigIntegration:
    """AI配置集成测试"""
    
    def test_temperature_validation(self):
        """测试温度参数验证"""
        # 有效温度
        config = AIConfig(temperature=0.5)
        assert config.temperature == 0.5
        
        config = AIConfig(temperature=0.0)
        assert config.temperature == 0.0
        
        config = AIConfig(temperature=2.0)
        assert config.temperature == 2.0
    
    def test_max_tokens_default(self):
        """测试最大token数默认值"""
        config = AIConfig()
        assert config.max_tokens == 2000
    
    def test_custom_max_tokens(self):
        """测试自定义最大token数"""
        config = AIConfig(max_tokens=4000)
        assert config.max_tokens == 4000
