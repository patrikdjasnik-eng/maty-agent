from __future__ import annotations

import email
import html
import imaplib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from app.config import Settings


class _HTMLTextExtractor(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.parts: list[str] = []

  def handle_data(self, data: str) -> None:
    value = data.strip()
    if value:
      self.parts.append(value)

  def text(self) -> str:
    return "\n".join(self.parts)


@dataclass(frozen=True)
class MailMessage:
  message_id: str
  subject: str
  sender: str
  received_at: datetime
  text: str


def _decode_header_value(value: str | None) -> str:
  if not value:
    return ""

  chunks = decode_header(value)
  decoded: list[str] = []

  for chunk, encoding in chunks:
    if isinstance(chunk, bytes):
      decoded.append(chunk.decode(encoding or "utf-8", errors="replace"))
    else:
      decoded.append(chunk)

  return "".join(decoded).strip()


def _decode_payload(part: Message) -> str:
  payload = part.get_payload(decode=True)
  if payload is None:
    raw = part.get_payload()
    return raw if isinstance(raw, str) else ""

  charset = part.get_content_charset() or "utf-8"
  return payload.decode(charset, errors="replace")


def _extract_text(message: Message) -> str:
  plain_parts: list[str] = []
  html_parts: list[str] = []

  if message.is_multipart():
    for part in message.walk():
      disposition = (part.get("Content-Disposition") or "").lower()
      if "attachment" in disposition:
        continue

      content_type = part.get_content_type()
      if content_type == "text/plain":
        plain_parts.append(_decode_payload(part))
      elif content_type == "text/html":
        html_parts.append(_decode_payload(part))
  else:
    content_type = message.get_content_type()
    if content_type == "text/html":
      html_parts.append(_decode_payload(message))
    else:
      plain_parts.append(_decode_payload(message))

  if plain_parts:
    return "\n".join(plain_parts).strip()

  parser = _HTMLTextExtractor()
  parser.feed(html.unescape("\n".join(html_parts)))
  return parser.text().strip()


def _received_at(message: Message) -> datetime:
  raw_date = message.get("Date")
  if not raw_date:
    return datetime.now(timezone.utc)

  try:
    parsed = parsedate_to_datetime(raw_date)
  except (TypeError, ValueError):
    return datetime.now(timezone.utc)

  if parsed.tzinfo is None:
    parsed = parsed.replace(tzinfo=timezone.utc)

  return parsed.astimezone(timezone.utc)


def fetch_bookio_messages(settings: Settings) -> list[MailMessage]:
  since = datetime.now(timezone.utc) - timedelta(days=settings.bookio_lookback_days)
  since_token = since.strftime("%d-%b-%Y")

  connection = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)

  try:
    connection.login(settings.email_user, settings.email_password)
    status, _ = connection.select("INBOX", readonly=True)
    if status != "OK":
      raise RuntimeError("Nepodařilo se otevřít INBOX")

    status, data = connection.uid("search", None, f'(SINCE "{since_token}")')
    if status != "OK" or not data:
      return []

    result: list[MailMessage] = []

    for uid in data[0].split():
      fetch_status, payload = connection.uid("fetch", uid, "(RFC822)")
      if fetch_status != "OK" or not payload:
        continue

      raw_message = next(
        (item[1] for item in payload if isinstance(item, tuple) and len(item) > 1),
        None,
      )
      if not isinstance(raw_message, bytes):
        continue

      parsed = email.message_from_bytes(raw_message)
      subject = _decode_header_value(parsed.get("Subject"))
      sender = _decode_header_value(parsed.get("From"))

      sender_filter = settings.bookio_sender_contains.casefold()
      subject_filter = settings.bookio_subject_contains.casefold()

      if sender_filter and sender_filter not in sender.casefold():
        continue
      if subject_filter and subject_filter not in subject.casefold():
        continue

      message_id = (parsed.get("Message-ID") or f"imap-uid:{uid.decode()}").strip()

      result.append(
        MailMessage(
          message_id=message_id,
          subject=subject,
          sender=sender,
          received_at=_received_at(parsed),
          text=_extract_text(parsed),
        )
      )

    return result
  finally:
    try:
      connection.logout()
    except imaplib.IMAP4.error:
      pass
