from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'CareMesh API'
    app_debug: bool = True
    api_prefix: str = '/api'
    frontend_url: str = 'http://localhost:5173'
    database_url: str = 'sqlite:///./caremesh.db'

    # Default Interswitch sandbox/test values (hackathon-friendly)
    interswitch_merchant_code: str = 'MX-TEST'  # replace with actual test merchant if available
    interswitch_pay_item_id: str = '101'  # default test pay item id
    interswitch_client_id: str = ''
    interswitch_secret_key: str = ''
    interswitch_mode: str = 'TEST'
    interswitch_collections_base_url: str = ''
    interswitch_passport_base_url: str = ''
    interswitch_timeout_seconds: float = 30.0
    app_redirect_url: str = 'http://localhost:5173/payment/callback'

    hf_token: str = ''
    hf_model: str = 'CohereLabs/tiny-aya-global:cohere'
    hf_fallback_models: str = 'zai-org/GLM-5:together,zai-org/GLM-4.7:cerebras'
    hf_base_url: str = 'https://router.huggingface.co/v1/chat/completions'
    hf_max_tokens: int = 220
    hf_timeout_seconds: int = 45
    hf_temperature: float = 0.3

    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False, extra='ignore')


settings = Settings()
