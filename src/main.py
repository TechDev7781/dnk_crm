import time

from src.constants import FETCH_PERIOD_MINUTES
from src.services.bitrix import BitrixService
from src.services.itigris import ItigrisService


def main() -> None:
    """Входная точка в приложение"""

    while True:
        BitrixService.handle_new_leads()
        ItigrisService.handle_finished_records()

        time.sleep(60 * FETCH_PERIOD_MINUTES)


if __name__ == "__main__":
    main()
