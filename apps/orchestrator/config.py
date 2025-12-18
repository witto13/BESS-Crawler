from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_dsn: str = "postgresql://bess:bess@db:5432/bess"
    redis_url: str = "redis://redis:6379/0"
    queue_name: str = "crawl"
    storage_base_path: str = "/data/documents"
    
    # Performance settings
    crawl_mode: str = "fast"  # "fast" or "deep"
    crawl_global_concurrency: int = 100
    crawl_per_domain_concurrency: int = 2
    crawl_timeout_s: int = 30
    crawl_retries: int = 3
    crawl_pdf_max_size_mb: int = 25
    crawl_cache_base: str = "/data/cache"
    crawl_text_cache_base: str = "/data/text_cache"

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


settings = Settings()

