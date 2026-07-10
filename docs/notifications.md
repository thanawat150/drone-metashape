# Notifications

Notifications are disabled by default and never determine job success. A no-op notifier is always available. Notification exceptions are written as warnings to the processing log and processing continues.

Telegram credentials are read only from runtime environment variables:

- `DRONE_METASHAPE_TELEGRAM_TOKEN`
- `DRONE_METASHAPE_TELEGRAM_CHAT_ID`

Tokens are not stored in config, job/state JSON, diagnostics, browser data, or source control. Messages are limited to stage completion, warnings, failure, cancellation, and completion.
