from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.mail_client import fetch_bookio_messages
from app.parser import parse_bookio_message
from app.reporting import build_report, save_report, send_report
from app.storage import Storage


logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("maty-agent")

LAST_REPORT_KEY = "last_report_at"


def process_inbox(settings: Settings, storage: Storage) -> int:
  messages = fetch_bookio_messages(settings)
  processed = 0

  for message in messages:
    if storage.is_processed(message.message_id):
      continue

    event = parse_bookio_message(message)
    storage.save_event(event)
    processed += 1

    logger.info(
      "Zpracována Bookio zpráva: %s (%s)",
      message.subject,
      event.event_type,
    )

  return processed


def create_report_if_due(
  settings: Settings,
  storage: Storage,
  force: bool = False,
) -> bool:
  now = datetime.now(timezone.utc)
  last_report_raw = storage.get_meta(LAST_REPORT_KEY)

  if last_report_raw:
    last_report = datetime.fromisoformat(last_report_raw)
  else:
    last_report = now - timedelta(hours=settings.report_interval_hours)

  due_at = last_report + timedelta(hours=settings.report_interval_hours)
  if not force and now < due_at:
    return False

  events = storage.events_since(last_report.isoformat())
  report = build_report(events, since=last_report, until=now)
  report_path = save_report(report, settings.report_directory, now)

  if settings.report_send_email:
    send_report(settings, report, now)
    logger.info("Report odeslán na %s", settings.report_recipient)

  storage.set_meta(LAST_REPORT_KEY, now.isoformat())
  logger.info("Report uložen: %s", report_path)
  return True


def run_cycle(settings: Settings, storage: Storage, report_now: bool = False) -> None:
  processed = process_inbox(settings, storage)
  logger.info("Nově zpracovaných zpráv: %d", processed)
  create_report_if_due(settings, storage, force=report_now)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Maty Agent pro Bookio rezervace")
  parser.add_argument(
    "--once",
    action="store_true",
    help="Provede jeden průchod inboxem a skončí.",
  )
  parser.add_argument(
    "--report-now",
    action="store_true",
    help="Vynutí vytvoření reportu po zpracování inboxu.",
  )
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  settings = Settings.from_env()
  storage = Storage(settings.database_path)

  if args.once:
    run_cycle(settings, storage, report_now=args.report_now)
    return

  logger.info(
    "Maty Agent běží. Kontrola inboxu každých %d sekund, report každých %d hodin.",
    settings.poll_seconds,
    settings.report_interval_hours,
  )

  first_cycle = True

  while True:
    try:
      run_cycle(
        settings,
        storage,
        report_now=args.report_now and first_cycle,
      )
    except Exception:
      logger.exception("Cyklus agenta selhal")

    first_cycle = False
    time.sleep(settings.poll_seconds)


if __name__ == "__main__":
  main()
