from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.parser import ReservationEvent
from app.storage import Storage


class StorageTests(unittest.TestCase):
  def test_message_is_deduplicated(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
      storage = Storage(str(Path(directory) / "test.db"))
      event = ReservationEvent(
        event_type="new",
        reservation_key="bookio:123",
        reservation_id="123",
        customer_name="Jan",
        service="Test",
        scheduled_for="",
        phone="",
        customer_email="",
        subject="Nová rezervace",
        sender="Bookio",
        received_at="2026-09-20T12:00:00+00:00",
        source_message_id="<message-1@example.test>",
        raw_excerpt="",
      )

      self.assertFalse(storage.is_processed(event.source_message_id))
      storage.save_event(event)
      self.assertTrue(storage.is_processed(event.source_message_id))

      storage.save_event(event)
      events = storage.events_since("2026-09-20T00:00:00+00:00")
      self.assertEqual(len(events), 1)


if __name__ == "__main__":
  unittest.main()
