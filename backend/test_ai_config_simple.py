"""
Simple test script for AI configuration
"""
import sys
sys.path.insert(0, '/Users/cm/Documents/kiro/project/backend')

from app.core.ai_config import AIConfig, get_ai_client, switch_ai_provider

def test_default_config():
    """测试默认配置"""
    config = AIConfig()
    print("✓ Default config created")
    assert config.provider == "deepseek"
    assert config.model == "deepseek-chat"
    print("✓ Default config values correct")

def test_custom_config():
    """测试自定义配置"""
    config = AIConfig(
        provider="custom",
        api_base="http://localhost:8000/v1",
        api_key="test-key",
        model="qwen2.5-7b-instruct"
    )
    print("✓ Custom config created")
    assert config.provider == "custom"
    assert config.model == "qwen2.5-7b-instruct"
    print("✓ Custom config values correct")

def test_validate_config():
    """测试配置验证"""
    # 有效配置
    config = AIConfig(
        provider="deepseek",
        api_base="https://api.deepseek.com/v1",
        api_key="sk-test-key",
        model="deepseek-chat"
    )
    is_valid, error_msg = config.validate_config()
    assert is_valid is True
    assert error_msg is None
    print("✓ Valid config passes validation")
    
    # 无效配置 - 缺少API密钥
    config = AIConfig(
        provider="deepseek",
        api_base="https://api.deepseek.com/v1",
        api_key="",
        model="deepseek-chat"
    )
    is_valid, error_msg = config.validate_config()
    assert is_valid is False
    assert "API密钥" in error_msg
    print("✓ Invalid config fails validation correctly")

def test_create_client():
    """测试创建客户端"""
    config = AIConfig(
        provider="deepseek",
        api_base="https://api.deepseek.com/v1",
        api_key="sk-test-key",
        model="deepseek-chat"
    )
    client = config.create_client()
    print("✓ Client created successfully")
    assert client is not None
    print("✓ Client is not None")

def test_get_provider_info():
    """测试获取提供商信息"""
    config = AIConfig(provider="deepseek")
    info = config.get_provider_info()
    assert info["name"] == "DeepSeek"
    assert info["requires_api_key"] is True
    print("✓ DeepSeek provider info correct")
    
    config = AIConfig(provider="custom")
    info = config.get_provider_info()
    assert info["name"] == "自部署模型"
    assert info["requires_api_key"] is False
    print("✓ Custom provider info correct")

def test_repr_masks_api_key():
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
    print("✓ API key is masked in repr")

if __name__ == "__main__":
    print("Running AI Config Tests...\n")
    
    try:
        test_default_config()
        test_custom_config()
        test_validate_config()
        test_create_client()
        test_get_provider_info()
        test_repr_masks_api_key()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
