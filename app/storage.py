from __future__ import annotations

import sqlite3
from pathlib import Path

from app.parser import ReservationEvent


class Storage:
  def __init__(self, database_path: str) -> None:
    self.database_path = database_path
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    self._initialize()

  def _connect(self) -> sqlite3.Connection:
    connection = sqlite3.connect(self.database_path)
    connection.row_factory = sqlite3.Row
    return connection

  def _initialize(self) -> None:
    with self._connect() as connection:
      connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS processed_messages (
          message_id TEXT PRIMARY KEY,
          processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reservation_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_type TEXT NOT NULL,
          reservation_key TEXT NOT NULL,
          reservation_id TEXT NOT NULL,
          customer_name TEXT NOT NULL,
          service TEXT NOT NULL,
          scheduled_for TEXT NOT NULL,
          phone TEXT NOT NULL,
          customer_email TEXT NOT NULL,
          subject TEXT NOT NULL,
          sender TEXT NOT NULL,
          received_at TEXT NOT NULL,
          source_message_id TEXT NOT NULL UNIQUE,
          raw_excerpt TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_events_received_at
          ON reservation_events(received_at);

        CREATE INDEX IF NOT EXISTS idx_events_reservation_key
          ON reservation_events(reservation_key);

        CREATE TABLE IF NOT EXISTS metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        """
      )

  def is_processed(self, message_id: str) -> bool:
    with self._connect() as connection:
      row = connection.execute(
        "SELECT 1 FROM processed_messages WHERE message_id = ? LIMIT 1",
        (message_id,),
      ).fetchone()
    return row is not None

  def save_event(self, event: ReservationEvent) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT OR IGNORE INTO reservation_events (
          event_type,
          reservation_key,
          reservation_id,
          customer_name,
          service,
          scheduled_for,
          phone,
          customer_email,
          subject,
          sender,
          received_at,
          source_message_id,
          raw_excerpt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          event.event_type,
          event.reservation_key,
          event.reservation_id,
          event.customer_name,
          event.service,
          event.scheduled_for,
          event.phone,
          event.customer_email,
          event.subject,
          event.sender,
          event.received_at,
          event.source_message_id,
          event.raw_excerpt,
        ),
      )
      connection.execute(
        "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
        (event.source_message_id,),
      )

  def events_since(self, since_iso: str) -> list[sqlite3.Row]:
    with self._connect() as connection:
      return connection.execute(
        """
        SELECT *
        FROM reservation_events
        WHERE received_at >= ?
        ORDER BY received_at ASC, id ASC
        """,
        (since_iso,),
      ).fetchall()

  def get_meta(self, key: str) -> str | None:
    with self._connect() as connection:
      row = connection.execute(
        "SELECT value FROM metadata WHERE key = ?",
        (key,),
      ).fetchone()
    return None if row is None else str(row["value"])

  def set_meta(self, key: str, value: str) -> None:
    with self._connect() as connection:
      connection.execute(
        """
        INSERT INTO metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
      )
