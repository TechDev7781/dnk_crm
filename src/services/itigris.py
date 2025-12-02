from datetime import datetime

import requests

from src.constants import (
    ITIGRIS_URL,
    ITIGRIS_URL_NEW,
)
from src.env import env_settings


class ItigrisService:
    # MARK: Auth
    @classmethod
    def login(
        cls,
        company: str = env_settings.ITIGRIS_COMPANY,
        login: str = env_settings.ITIGRIS_LOGIN,
        password: str = env_settings.ITIGRIS_PASSWORD,
        department_id: int = env_settings.ITIGRIS_DEPARTAMENT_ID,
    ) -> str:
        """Вход в систему"""

        response = requests.post(
            url=f"{ITIGRIS_URL_NEW}/api/v2/sign/in",
            json={
                "company": company,
                "login": login,
                "password": password,
                "departmentId": department_id,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Ошибка при входе в систему: {response.text}")

        return response.json()["accessToken"]

    # MARK: Clients
    @classmethod
    def get_client_id_for_lead(cls, token: str, phone: str) -> str | None:
        """Получение ID клиента по номеру телефона"""

        response = requests.get(
            url=f"{ITIGRIS_URL_NEW}/api/v2/clients",
            params={
                "clientSearchType": "PHONE_NUMBER",
                "searchString": phone,
                "deleted": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при получении клиента: {response.text}, статус: {response.status_code}"
            )

        try:
            return response.json().get("content", [{}])[0].get("id")
        except Exception as e:
            print(f"Ошибка при получении клиента, создаем новый: {e}")

    @classmethod
    def get_client_ids(cls, token: str) -> str | None:
        """Получение ID клиента по номеру телефона"""

        response = requests.get(
            url=f"{ITIGRIS_URL_NEW}/api/v2/clients",
            params={
                "deleted": False,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при получении клиента: {response.text}, статус: {response.status_code}"
            )

        try:
            ids = []
            for client in response.json().get("content", [{}]):
                ids.append(client.get("id"))
            return ids
        except Exception as e:
            print(f"Ошибка при получении клиентов: {e}")

    @classmethod
    def create_client(
        cls,
        token: str,
        first_name: str,
        second_name: str,
        last_name: str,
        phone: str,
        email: str,
        gender: bool,
    ):
        """Создание клиента"""

        response = requests.post(
            url=f"{ITIGRIS_URL_NEW}/api/v2/clients",
            json={
                "firstName": first_name,
                "familyName": second_name,
                "patronymicName": last_name,
                "tel1": phone,
                "gender": gender,
                "email": email,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        if response.status_code != 201:
            raise Exception(
                f"Ошибка при создании клиента: {response.text}, статус: {response.status_code}"
            )

        return response.json()["id"]

    @classmethod
    def prepare_client(cls, token: str, id: int) -> None:
        """Подготовка клиента на первом и втором этапе"""

        response = requests.post(
            url=f"{ITIGRIS_URL_NEW}/api/v2/clients/{id}/agreements/prepare-text",
            json={
                "agreementType": "PERSONAL_DATA_PROCESSING",
                "collectionMethod": "QUESTIONNAIRE",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Host": "optima-2-backend-yc-prod-2.itigris.ru",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при подготовке клиента на первом этапе: {response.text}, статус: {response.status_code}"
            )

        response = requests.post(
            url=f"{ITIGRIS_URL_NEW}/api/v2/clients/{id}/agreements",
            json={
                "agreementType": "PERSONAL_DATA_PROCESSING",
                "collectionMethod": "QUESTIONNAIRE",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Host": "optima-2-backend-yc-prod-2.itigris.ru",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при подготовке клиента на втором этапе: {response.text}, статус: {response.status_code}"
            )

    # MARK: Records
    @classmethod
    def create_record(
        cls,
        client_id: int,
        time: str,
        key: str = env_settings.ITIGRIS_KEY,
        user_id: int = env_settings.ITIGRIS_USER_ID,
        service_type_id: int = env_settings.ITIGRIS_SERVICE_TYPE_ID,
    ) -> None:
        """Создание записи"""

        response = requests.post(
            url=f"{ITIGRIS_URL}/remoteRegistry/register",
            params={
                "key": key,
                "clientId": client_id,
                "userId": user_id,
                "serviceTypeId": service_type_id,
                "time": time,
            },
            headers={"Host": "optima.itigris.ru"},
        )

        if not response.status_code == 200:
            raise Exception(
                f"Ошибка при создании записи: {response.text}, статус: {response.status_code}"
            )

    @classmethod
    def get_records(
        cls,
        token: str,
        status: str | None = None,
    ) -> list[dict]:
        """Получение записей по статусу"""

        params = {}
        if status:
            params["status"] = status

        params["appointmentFrom"] = datetime.now().strftime("%Y-%m-%d")

        response = requests.get(
            url=f"{ITIGRIS_URL_NEW}/api/v2/registry-records",
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Host": "optima-2-backend-yc-prod-2.itigris.ru",
            },
        )

        if not response.status_code == 200:
            raise Exception(
                f"Ошибка при получении записей с подтвержденным статусом: {response.text}, статус: {response.status_code}"
            )

        return response.json()

    @classmethod
    def _format_receipt(cls, receipt: dict | None) -> str | None:
        """Форматирование рецепта для Bitrix24"""

        if not receipt:
            return

        receipt_str = ""

        for field in [
            "sphOd",
            "sphOs",
            "cylOd",
            "cylOs",
            "axOd",
            "axOs",
            "prism1DioptreOd",
            "prism1DioptreOs",
            "prism2DioptreOd",
            "prism2DioptreOs",
            "prism1BaseOd",
            "prism1BaseOs",
            "prism2BaseOd",
            "prism2BaseOs",
            "addidationOd",
            "addidationOs",
            "dpp",
            "dppOd",
            "dppOs",
            "visusOd",
            "visusOs",
            "comments",
        ]:
            receipt_str += f"{field}: {receipt.get(field) or 'не указано'}\n"

        return receipt_str

    @classmethod
    def _format_contact_lens_receipt(cls, receipt: dict | None) -> str | None:
        """Форматирование рецепта контактных линз для Bitrix24"""

        if not receipt:
            return

        receipt_str = ""
        for field in ["model", "color"]:
            receipt_str += f"{field}: {receipt.get(field) or 'не указано'}\n"

        for eye in ["leftEye", "rightEye"]:
            receipt_str += f"{eye}:"
            for field in [
                "dioptre",
                "cylinder",
                "axis",
                "add",
                "curvatureRadius",
                "diameter",
            ]:
                receipt_str += (
                    f"{field}: {receipt.get(eye, {}).get(field) or 'не указано'}\n"
                )

        return receipt_str

    @classmethod
    def handle_finished_records(
        cls,
        record_id_to_lead_id: dict[int, int],
        explored_order_ids: set[int],
    ) -> None:
        """
        Обработка записей с подтвержденным статусом
        и обновление лидов в Bitrix24
        """

        print(
            f"Обработка записей с подтвержденным статусом {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        from src.services.bitrix import BitrixService

        # Получение токена для работы с Itigris
        token = cls.login()

        records = cls.get_records(token, status="REALIZED")
        if not records:
            return

        for record in records:
            try:
                if record.get("id") in explored_order_ids:
                    print(f"Запись {record.get('id')} уже обработана")
                    continue

                print(f"Обработка записи {record.get('id')}")

                orders = cls.get_orders(record.get("client").get("id"))
                if not orders:
                    print(
                        f"Заказы для клиента {record.get('client').get('id')} не найдены"
                    )
                    continue

                # Сопоставление записи с заказом, по максимальному ID заказа
                order, max_id = None, None
                for order in orders:
                    if not max_id:
                        max_id = int(order.get("id", 0))
                        order = order
                    else:
                        if int(order.get("id", 0)) > max_id:
                            max_id = int(order.get("id", 0))
                            order = order

                # Получение рецептов к записи (очки и контактные линзы)
                prescriptions = cls.get_prescriptions(
                    token,
                    record.get("client").get("id"),
                )

                perscriptions = prescriptions.get("prescriptions")
                contact_lens_perscriptions = prescriptions.get(
                    "contactLensPrescriptions",
                )
                # Получение первого рецепта (очки) и первого рецепта для контактных линз
                perscription = perscriptions[0] if perscriptions else None
                contact_lens_perscription = (
                    contact_lens_perscriptions[0]
                    if contact_lens_perscriptions
                    else None
                )

                # Форматирование рецептов
                receipt_str = cls._format_receipt(perscription)
                contact_lens_receipt_str = cls._format_contact_lens_receipt(
                    contact_lens_perscription
                )

                # Поиск лида по имени, фамилии и отчеству
                lead_id = record_id_to_lead_id.get(int(record.get("id", 0)))
                if not lead_id:
                    print(f"Лид не найден для записи {record.get('id')}")
                    continue

                # Обновление лида в Bitrix24
                fields = {
                    "UF_CRM_1760104053415": receipt_str,
                    "UF_CRM_1760104354563": contact_lens_receipt_str,
                    "UF_CRM_1760104146355": float(order.get("sum", 0))
                    + float(order.get("discount", 0)),  # Сумма заказа
                    "UF_CRM_1760104154471": float(
                        order.get("sum", 0)
                    ),  # Сумма к оплате
                    "UF_CRM_1760104282834": int(
                        (
                            float(order.get("discount", 0))
                            / (
                                float(order.get("sum", 0))
                                + float(order.get("discount", 0))
                            )
                        )
                        * 100
                    ),  # Скидка
                    "UF_CRM_1760104313977": [
                        {
                            "NAME": "не выбрано",
                            "VALUE": "",
                            "IS_SELECTED": True,
                        },
                        {
                            "NAME": "Ночные",
                            "VALUE": 45,
                            "IS_SELECTED": False,
                        },
                        {
                            "NAME": "Дневные",
                            "VALUE": 47,
                            "IS_SELECTED": False,
                        },
                    ],  # Тип очков
                }
                BitrixService.update_lead(lead_id, fields)

            except Exception as e:
                print(f"Ошибка при обработке записи {record.get('id')}: {e}")
            finally:
                explored_order_ids.add(record.get("id"))

    # MARK: Orders
    @classmethod
    def get_orders(
        cls,
        client_id: int,
        status: str | None = None,
        key: str = env_settings.ITIGRIS_KEY,
    ) -> list[dict]:
        """Получение записей по статусу"""

        # Фильтрация по дате (пока убрано, можно добавить по необходимости)
        # params["startDate"] = datetime.now().strftime("%d.%m.%Y")
        # params["endDate"] = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")

        response = requests.get(
            url=f"{ITIGRIS_URL}/remoteOrderHistory/list",
            params={
                "key": key,
                "clientId": client_id,
            },
            headers={"Host": "optima.itigris.ru"},
        )

        if not response.status_code == 200:
            raise Exception(
                f"Ошибка при получении записей с подтвержденным статусом: {response.text}, статус: {response.status_code}"
            )

        if not status:
            return response.json()

        try:
            records = []
            for record in response.json():
                if record.get("status") == status:
                    records.append(record)

            return records
        except Exception as e:
            print(f"Ошибка при получении записей: {e}")
            return []

    # MARK: Prescriptions
    @classmethod
    def get_prescriptions(
        cls,
        token: str,
        client_id: int,
    ) -> list[dict]:
        """Получение рецептов по ID клиента"""

        response = requests.get(
            f"{ITIGRIS_URL_NEW}/api/v2/clients/{client_id}/prescription",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Host": "optima-2-backend-yc-prod-2.itigris.ru",
            },
        )

        if not response.status_code == 200:
            raise Exception(
                f"Ошибка при получении рецепта очков: {response.text}, статус: {response.status_code}"
            )

        return response.json()
