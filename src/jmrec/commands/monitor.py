import random
import time
from dataclasses import dataclass

import requests
import typer
from dotenv import load_dotenv
from rich.panel import Panel

from jmrec.utils import console

load_dotenv()
app = typer.Typer()


@dataclass(frozen=True)
class Validation:
    condition: bool
    error: str


@app.command()
def track(
    url: str = typer.Argument(
        "https://itpec.org/statsandresults/all-passers-information/Philippines/2026S_IP.pdf",
        help="URL of the PDF to monitor for availability.",
    ),
    token: str = typer.Option(
        None,
        "--token",
        "-t",
        help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env var).",
        envvar="TELEGRAM_BOT_TOKEN",
    ),
    chat_id: str = typer.Option(
        None,
        "--chat-id",
        "-c",
        help="Telegram chat ID (or set TELEGRAM_CHAT_ID env var).",
        envvar="TELEGRAM_CHAT_ID",
    ),
    interval: int = typer.Option(
        60,
        "--interval",
        "-i",
        help="Seconds between checks. Default is 60 seconds.",
    ),
    interval_jitter: tuple[int, int] = typer.Option(
        (-30, 30),
        "--interval-jitter",
        help="Random jitter (in seconds) to add/subtract from the interval to avoid predictable polling patterns. Default is (-30, 30) for ±30 seconds.",
    ),
    once: bool = typer.Option(
        False,
        "--once",
        "-1",
        help="Check once and exit instead of polling.",
    ),
):
    """
    Monitor a URL and send a Telegram notification when it becomes available (200 OK).

    Uses HEAD requests to check availability. When the resource is found,
    sends a notification via Telegram bot.

    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in a .env file or as env vars.
    """

    validations = [
        Validation(
            condition=not token,
            error="Telegram bot token required. Set TELEGRAM_BOT_TOKEN env var or use --token.",
        ),
        Validation(
            condition=not chat_id,
            error="Telegram chat ID required. Set TELEGRAM_CHAT_ID env var or use --chat-id.",
        ),
        Validation(
            condition=interval <= 10,
            error="Interval must be greater than 10 seconds to avoid excessive requests.",
        ),
        Validation(
            condition=interval_jitter[0] > interval_jitter[1],
            error="Invalid interval jitter range. Ensure the first value is less than or equal to the second.",
        ),
        Validation(
            condition=interval + interval_jitter[0] <= 0,
            error=f"Jitter lower bound ({interval_jitter[0]}) would cause negative sleep time. "
            f"Ensure interval + jitter_low > 0.",
        ),
    ]

    for v in validations:
        if v.condition:
            typer.secho(v.error, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

    console.print(
        Panel.fit(
            f"[bold]Monitoring:[/bold] {url}\n"
            f"[bold]Interval:[/bold] {interval}s | [bold]Jitter:[/bold] {interval_jitter} | [bold]Mode:[/bold] {'once' if once else 'polling'}",
            title="ITPEC Tracker",
            border_style="cyan",
        )
    )

    headers = {"User-Agent": "Mozilla/5.0"}

    while True:
        try:
            response = requests.head(url, headers=headers, timeout=10)

            if response.status_code == 200:
                console.print("[success]PDF Found (200 OK)![/success] Sending notification…")
                _send_telegram(token, chat_id, url)
                break
            else:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                console.print(
                    f"[info][{ts}][/info] Status: [warning]{response.status_code}[/warning] — retrying…"
                )

        except requests.RequestException as e:
            console.print(f"[error]Network error:[/error] {e}")

        if once:
            console.print("[info]Single check complete. Exiting.[/info]")
            break

        time.sleep(interval + random.randint(*interval_jitter))


def _send_telegram(token: str, chat_id: str, url: str) -> None:
    """Send a Telegram notification that the PDF is available."""
    message = f"*ITPEC Results Update!* \n\nThe PDF is now available!\n\n[Download link]({url})"
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(telegram_url, json=payload, timeout=10)
        if not resp.ok:
            console.print(f"[error]Telegram API error ({resp.status_code}):[/error] {resp.text}")
            return
        else:
            console.print("[success]Notification sent to Telegram![/success]")
    except requests.RequestException as e:
        console.print(f"[error]Failed to send Telegram notification:[/error] {e}")
