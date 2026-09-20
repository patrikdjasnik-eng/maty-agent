from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
  env_path = Path(path)
  if not env_path.exists():
    return

  for raw_line in env_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    os.environ.setdefault(key, value)


def _as_bool(value: str | None, default: bool) -> bool:
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "ano", "on"}


@dataclass(frozen=True)
class Settings:
  email_user: str
  email_password: str
  imap_host: str = "imap.seznam.cz"
  imap_port: int = 993
  smtp_host: str = "smtp.seznam.cz"
  smtp_port: int = 465
  report_to_email: str = ""
  report_send_email: bool = True
  report_interval_hours: int = 48
  poll_seconds: int = 300
  bookio_sender_contains: str = "bookio"
  bookio_subject_contains: str = ""
  bookio_lookback_days: int = 7
  database_path: str = "data/maty_agent.db"
  report_directory: str = "reports"

  @classmethod
  def from_env(cls) -> "Settings":
    load_dotenv()

    email_user = os.getenv("EMAIL_USER", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()

    if not email_user:
      raise ValueError("Chybí EMAIL_USER v .env")
    if not email_password:
      raise ValueError("Chybí EMAIL_PASSWORD v .env")

    return cls(
      email_user=email_user,
      email_password=email_password,
      imap_host=os.getenv("IMAP_HOST", "imap.seznam.cz").strip(),
      imap_port=int(os.getenv("IMAP_PORT", "993")),
      smtp_host=os.getenv("SMTP_HOST", "smtp.seznam.cz").strip(),
      smtp_port=int(os.getenv("SMTP_PORT", "465")),
      report_to_email=os.getenv("REPORT_TO_EMAIL", "").strip(),
      report_send_email=_as_bool(os.getenv("REPORT_SEND_EMAIL"), True),
      report_interval_hours=int(os.getenv("REPORT_INTERVAL_HOURS", "48")),
      poll_seconds=max(60, int(os.getenv("POLL_SECONDS", "300"))),
      bookio_sender_contains=os.getenv("BOOKIO_SENDER_CONTAINS", "bookio").strip(),
      bookio_subject_contains=os.getenv("BOOKIO_SUBJECT_CONTAINS", "").strip(),
      bookio_lookback_days=max(1, int(os.getenv("BOOKIO_LOOKBACK_DAYS", "7"))),
      database_path=os.getenv("DATABASE_PATH", "data/maty_agent.db").strip(),
      report_directory=os.getenv("REPORT_DIRECTORY", "reports").strip(),
    )

  @property
  def report_recipient(self) -> str:
    return self.report_to_email or self.email_user
