from lcaconfig import config


class DocumentationSettings(config.Settings):
    # Azure Storage
    STORAGE_ACCOUNT_URL: str
    STORAGE_CONTAINER_NAME: str
    STORAGE_ACCESS_KEY: str
    STORAGE_BASE_PATH: str
    ROUTER_URL: str
    SPECKLE_TOKEN: str


settings = DocumentationSettings()
