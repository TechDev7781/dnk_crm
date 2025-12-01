import time
from datetime import datetime, timedelta, timezone

import requests

from src.constants import FETCH_PERIOD_MINUTES
from src.env import env_settings
from src.services.itigris import ItigrisService


class BitrixService:
    # MARK: Leads
    @classmethod
    def get_leads(cls, filters: dict | None = None) -> list[dict]:
        """Получение лидов с фильтрами"""

        response = requests.post(
            url=f"{env_settings.BITRIX_WEBHOOK_URL}/crm.lead.list",
            json={
                "filter": filters if filters else {},
                "select": ["*"],
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при получении лидов: {response.text}, статус: {response.status_code}"
            )

        return response.json().get("result", [])

    @classmethod
    def get_lead(cls, id: int) -> dict:
        """Получение лида по ID"""

        response = requests.post(
            url=f"{env_settings.BITRIX_WEBHOOK_URL}/crm.lead.get",
            json={
                "ID": id,
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при получении лидов: {response.text}, статус: {response.status_code}"
            )

        return response.json().get("result", [])

    @classmethod
    def get_lead_by_names(
        cls,
        first_name: str,
        second_name: str,
        last_name: str,
    ) -> dict:
        """Поиск лида по имени, фамилии и отчеству"""

        leads = cls.get_leads()
        for lead in leads:
            if (
                lead.get("NAME") == first_name
                and lead.get("SECOND_NAME") == second_name
                and lead.get("LAST_NAME") == last_name
            ):
                return lead

    @classmethod
    def update_lead(cls, id: int, fields: list[dict]) -> None:
        """Обновление лида в Bitrix24"""

        response = requests.post(
            url=f"{env_settings.BITRIX_WEBHOOK_URL}/crm.lead.update",
            json={
                "id": id,
                "fields": fields,
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Ошибка при обновлении лида: {response.text}, статус: {response.status_code}"
            )

        return response.json()

    @classmethod
    def _convert_date(cls, date: str) -> str:
        """Функция утиилита для конвертации даты в формат Itigris"""

        dt = datetime.fromisoformat(date)
        dt_utc = dt.astimezone(timezone(timedelta(hours=3)))
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S")

    @classmethod
    def handle_new_leads(cls, record_id_to_lead_id: dict[int, int]) -> None:
        """
        Обработка обнавленных лидов за последние FETCH_PERIOD_MINUTES минут
        и статусом IN_PROCESS
        """

        print(
            f"Обработка обнавленных лидов {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        try:
            filters = {
                "=STATUS_ID": "IN_PROCESS",
                ">DATE_MODIFY": (
                    datetime.now() - timedelta(minutes=FETCH_PERIOD_MINUTES)
                ).isoformat(),
            }

            # Получение лидов с фильтрами
            leads = cls.get_leads(filters)
            if not leads:
                return

            # Получение токена для работы с Itigris
            itigris_token = ItigrisService.login()

            for lead in leads:
                print(f"Обработка обновленного лида {lead['ID']}")
                try:
                    # Получение полного лида с полями email и phone
                    lead_full = cls.get_lead(lead["ID"])
                    # Получение ID клиента в Itigris по номеру телефона
                    client_id = ItigrisService.get_client_id_for_lead(
                        token=itigris_token,
                        phone=lead_full.get("PHONE", [{}])[0].get("VALUE"),
                    )
                    # Если клиент не найден, создаем нового
                    if not client_id:
                        client_id = ItigrisService.create_client(
                            token=itigris_token,
                            first_name=lead_full.get("NAME"),
                            second_name=lead_full.get("SECOND_NAME"),
                            last_name=lead_full.get("LAST_NAME"),
                            phone=lead_full.get("PHONE", [{}])[0].get("VALUE"),
                            email=lead_full.get("EMAIL", [{}])[0].get("VALUE"),
                            gender=True
                            if lead_full.get("UF_CRM_1762957506003") == "223"
                            else False,
                        )
                        ItigrisService.prepare_client(itigris_token, client_id)

                    # Создание записи в Itigris
                    ItigrisService.create_record(
                        client_id=client_id,
                        time=cls._convert_date(lead_full.get("UF_CRM_1760092417949")),
                    )

                    time.sleep(3)

                    records = ItigrisService.get_records(itigris_token)
                    if not records:
                        print(f"Записи для лида {client_id} не найдены")
                        continue

                    max_id = None
                    for record in records:
                        if not max_id:
                            max_id = int(record.get("id", 0))
                        else:
                            if int(record.get("id", 0)) > max_id:
                                max_id = int(record.get("id", 0))

                    record_id_to_lead_id[max_id] = int(lead["ID"])

                    print(f"Лид {lead['ID']} обработан успешно")
                except Exception as e:
                    print(f"Ошибка при обработке лида {lead['ID']}: {e}")
        except Exception as e:
            print(f"Ошибка при обработке лидов: {e}")
