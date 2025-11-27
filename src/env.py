import os

from dotenv import load_dotenv

load_dotenv()


class EnvSettings:
    ITIGRIS_COMPANY = str(os.getenv("ITIGRIS_COMPANY"))
    ITIGRIS_LOGIN = str(os.getenv("ITIGRIS_LOGIN"))
    ITIGRIS_PASSWORD = str(os.getenv("ITIGRIS_PASSWORD"))
    ITIGRIS_DEPARTAMENT_ID = int(os.getenv("ITIGRIS_DEPARTAMENT_ID"))
    ITIGRIS_KEY = str(os.getenv("ITIGRIS_KEY"))
    ITIGRIS_USER_ID = int(os.getenv("ITIGRIS_USER_ID"))
    ITIGRIS_SERVICE_TYPE_ID = int(os.getenv("ITIGRIS_SERVICE_TYPE_ID"))

    BITRIX_WEBHOOK_URL = str(os.getenv("BITRIX_WEBHOOK_URL"))


env_settings = EnvSettings()
