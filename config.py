import pydantic
import yaml
from functools import lru_cache


class Config(pydantic.BaseSettings):
    app_id: str
    app_secret: str
    api_key: str
    database_host: str = "localhost"
    database_port: int = 6379
    proxy: str = ""
    database: int = 0
    server: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    initial_count: int = 1000
    jwt_secret: str = (
        "7P^V7vGhL1f5w3Do0O*)JLQlG8PuT28_k3u%t#3PUR%4RxU9D~fbHLFN%$5$zlvUo9qz6GLu"
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    @pydantic.root_validator
    def check_required_keys(cls, values):
        required_keys = ["app_id", "app_secret", "api_key"]
        for key in required_keys:
            if key not in values:
                raise ValueError(f"Missing required configuration key: {key}")
        return values


@lru_cache()
def read_config():
    with open("config.yml", "r") as f:
        config_data = yaml.safe_load(f)

    config = Config(**config_data)
    return config


config = read_config()
