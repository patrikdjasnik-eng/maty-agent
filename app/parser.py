from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Literal

from app.mail_client import MailMessage


EventType = Literal["new", "changed", "cancelled", "unknown"]


@dataclass(frozen=True)
class ReservationEvent:
  event_type: EventType
  reservation_key: str
  reservation_id: str
  customer_name: str
  service: str
  scheduled_for: str
  phone: str
  customer_email: str
  subject: str
  sender: str
  received_at: str
  source_message_id: str
  raw_excerpt: str


def _first_match(patterns: list[str], text: str) -> str:
  for pattern in patterns:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if match:
      return match.group(1).strip()
  return ""


def _classify(text: str) -> EventType:
  normalized = text.casefold()

  cancelled = ("zrušen", "zrusen", "storno", "stornov", "cancel")
  changed = ("změn", "zmen", "upraven", "přesun", "presun", "reschedul")
  created = (
    "nová rezervace",
    "nova rezervace",
    "new reservation",
    "nová objednávka",
    "nova objednavka",
    "vytvořena rezervace",
    "vytvorena rezervace",
    "potvrzení rezervace",
    "potvrzeni rezervace",
  )

  if any(keyword in normalized for keyword in cancelled):
    return "cancelled"
  if any(keyword in normalized for keyword in changed):
    return "changed"
  if any(keyword in normalized for keyword in created):
    return "new"
  return "unknown"


def _reservation_key(
  reservation_id: str,
  customer_name: str,
  customer_email: str,
  phone: str,
  subject: str,
) -> str:
  if reservation_id:
    return f"bookio:{reservation_id.casefold()}"

  stable_source = "|".join(
    value.casefold().strip()
    for value in (customer_email, phone, customer_name, subject)
    if value.strip()
  )
  return "fallback:" + hashlib.sha256(stable_source.encode("utf-8")).hexdigest()[:24]


def parse_bookio_message(message: MailMessage) -> ReservationEvent:
  combined = f"{message.subject}\n{message.text}".strip()

  reservation_id = _first_match(
    [
      r"(?:číslo\s+rezervace|cislo\s+rezervace|reservation\s+id|booking\s+id)\s*[:#]?\s*([A-Z0-9_-]{3,})",
      r"(?:rezervace|booking)\s*#\s*([A-Z0-9_-]{3,})",
    ],
    combined,
  )
  customer_name = _first_match(
    [
      r"(?:jméno|jmeno|zákazník|zakaznik|klient|customer)\s*:\s*([^\r\n]+)",
    ],
    combined,
  )
  service = _first_match(
    [
      r"(?:služba|sluzba|service|procedura)\s*:\s*([^\r\n]+)",
    ],
    combined,
  )
  scheduled_for = _first_match(
    [
      r"(?:termín|termin|datum\s+a\s+čas|datum\s+a\s+cas|date\s+and\s+time|appointment)\s*:\s*([^\r\n]+)",
      r"(?:datum|date)\s*:\s*([^\r\n]+)",
    ],
    combined,
  )
  phone = _first_match(
    [
      r"(?:telefon|tel\.?|phone)\s*:\s*([+0-9][+0-9 ()-]{6,})",
    ],
    combined,
  )
  customer_email = _first_match(
    [
      r"(?:e-?mail|email)\s*:\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})",
    ],
    combined,
  )

  event_type = _classify(combined)
  key = _reservation_key(
    reservation_id,
    customer_name,
    customer_email,
    phone,
    message.subject,
  )

  compact_excerpt = re.sub(r"\s+", " ", message.text).strip()[:1000]

  return ReservationEvent(
    event_type=event_type,
    reservation_key=key,
    reservation_id=reservation_id,
    customer_name=customer_name,
    service=service,
    scheduled_for=scheduled_for,
    phone=phone,
    customer_email=customer_email,
    subject=message.subject,
    sender=message.sender,
    received_at=message.received_at.isoformat(),
    source_message_id=message.message_id,
    raw_excerpt=compact_excerpt,
  )
