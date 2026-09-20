from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.mail_client import MailMessage
from app.parser import parse_bookio_message


class ParserTests(unittest.TestCase):
  def _message(self, subject: str, body: str) -> MailMessage:
    return MailMessage(
      message_id=f"<{subject}@example.test>",
      subject=subject,
      sender="Bookio <notification@bookio.test>",
      received_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
      text=body,
    )

  def test_parses_new_reservation(self) -> None:
    event = parse_bookio_message(
      self._message(
        "Nová rezervace #AB123",
        """
        Číslo rezervace: AB123
        Jméno: Jan Novák
        Služba: Konzultace
        Termín: 22.09.2026 15:30
        Telefon: +420 777 111 222
        E-mail: jan@example.com
        """,
      )
    )

    self.assertEqual(event.event_type, "new")
    self.assertEqual(event.reservation_id, "AB123")
    self.assertEqual(event.customer_name, "Jan Novák")
    self.assertEqual(event.service, "Konzultace")
    self.assertEqual(event.scheduled_for, "22.09.2026 15:30")
    self.assertEqual(event.customer_email, "jan@example.com")

  def test_cancellation_has_priority(self) -> None:
    event = parse_bookio_message(
      self._message(
        "Rezervace byla zrušena",
        "Zrušení rezervace\nČíslo rezervace: AB123",
      )
    )

    self.assertEqual(event.event_type, "cancelled")
    self.assertEqual(event.reservation_key, "bookio:ab123")

  def test_parses_changed_reservation(self) -> None:
    event = parse_bookio_message(
      self._message(
        "Změna rezervace",
        "Rezervace byla přesunuta na jiný termín.",
      )
    )

    self.assertEqual(event.event_type, "changed")


if __name__ == "__main__":
  unittest.main()
