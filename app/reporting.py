from __future__ import annotations

import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from sqlite3 import Row

from app.config import Settings


EVENT_LABELS = {
  "new": "Nová rezervace",
  "changed": "Změněná rezervace",
  "cancelled": "Zrušená rezervace",
  "unknown": "Nerozpoznaná Bookio zpráva",
}


def build_report(events: list[Row], since: datetime, until: datetime) -> str:
  counts = {
    "new": 0,
    "changed": 0,
    "cancelled": 0,
    "unknown": 0,
  }

  for event in events:
    event_type = str(event["event_type"])
    counts[event_type if event_type in counts else "unknown"] += 1

  lines = [
    "MATY AGENT — REPORT REZERVACÍ",
    "",
    f"Období: {since.astimezone().strftime('%d.%m.%Y %H:%M')} – {until.astimezone().strftime('%d.%m.%Y %H:%M')}",
    f"Celkem Bookio událostí: {len(events)}",
    f"Nové rezervace: {counts['new']}",
    f"Změny rezervací: {counts['changed']}",
    f"Zrušené rezervace: {counts['cancelled']}",
    f"Nerozpoznané zprávy: {counts['unknown']}",
    "",
  ]

  if not events:
    lines.append("Za toto období nebyla nalezena žádná Bookio událost.")
    return "\n".join(lines)

  lines.append("DETAIL")
  lines.append("")

  for index, event in enumerate(events, start=1):
    event_type = str(event["event_type"])
    label = EVENT_LABELS.get(event_type, EVENT_LABELS["unknown"])

    details = [
      f"{index}. {label}",
      f"   Předmět: {event['subject']}",
      f"   Přijato: {event['received_at']}",
    ]

    optional_fields = (
      ("Rezervace", event["reservation_id"]),
      ("Klient", event["customer_name"]),
      ("Služba", event["service"]),
      ("Termín", event["scheduled_for"]),
      ("Telefon", event["phone"]),
      ("E-mail", event["customer_email"]),
    )

    for field_label, value in optional_fields:
      if value:
        details.append(f"   {field_label}: {value}")

    if event_type == "unknown" and event["raw_excerpt"]:
      details.append(f"   Náhled: {event['raw_excerpt'][:300]}")

    lines.extend(details)
    lines.append("")

  return "\n".join(lines).rstrip() + "\n"


def save_report(report: str, directory: str, created_at: datetime) -> Path:
  report_directory = Path(directory)
  report_directory.mkdir(parents=True, exist_ok=True)
  path = report_directory / f"report-{created_at.strftime('%Y%m%d-%H%M%S')}.txt"
  path.write_text(report, encoding="utf-8")
  return path


def send_report(settings: Settings, report: str, created_at: datetime) -> None:
  message = EmailMessage()
  message["From"] = settings.email_user
  message["To"] = settings.report_recipient
  message["Subject"] = f"Maty Agent — report rezervací {created_at.strftime('%d.%m.%Y')}"
  message.set_content(report)

  with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
    smtp.login(settings.email_user, settings.email_password)
    smtp.send_message(message)
