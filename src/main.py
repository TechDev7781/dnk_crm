import time

from src.constants import FETCH_PERIOD_MINUTES
from src.services.bitrix import BitrixService
from src.services.itigris import ItigrisService

record_id_to_lead_id: dict[int, int] = {}  # ID записи -> ID лида
explored_order_ids: set[int] = set()  # ID заказа, которые уже были обработаны


def main() -> None:
    """Входная точка в приложение"""

    while True:
        BitrixService.handle_new_leads(record_id_to_lead_id)
        ItigrisService.handle_finished_records(record_id_to_lead_id, explored_order_ids)

        time.sleep(60 * FETCH_PERIOD_MINUTES)


if __name__ == "__main__":
    main()
