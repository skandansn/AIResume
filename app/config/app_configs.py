from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AIResume"
    gemini_api_key: str = "gemini_api_key"
    firebase_api_key: str = "firebase_api_key"
    firebase_auth_domain: str = "firebase_auth_domain"
    firebase_project_id: str = "firebase_project_id"
    firebase_storage_bucket: str = "firebase_storage_bucket"
    firebase_messaging_sender_id: str = "firebase_messaging_sender_id"
    firebase_app_id: str = "firebase_app_id"
    firebase_measurement_id: str = "firebase_measurement_id"
    firebase_database_url: str = "firebase_database_url"
    local_saving: bool = False

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
   
        

