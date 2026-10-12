import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# If python-dotenv is installed and a .env file exists, load it automatically.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv not available — environment variables must be set externally
    pass


def send_email(to_address: str, subject: str, body: str, html: str | None = None) -> None:
    """Send a plain-text email using SMTP.

    Configuration is read from environment variables, which can be set permanently
    in your system or placed in a project `.env` file (add `.env` to `.gitignore`).

    Required env vars:
      - SMTP_HOST
      - SMTP_USER
      - SMTP_PASSWORD

    Optional env vars:
      - SMTP_PORT (default 587)
      - FROM_EMAIL (defaults to SMTP_USER)
      - SMTP_USE_TLS (true/1 to enable STARTTLS; default true)

    Raises RuntimeError if required settings are missing.
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", user)
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

    if not host or not user or not password:
        raise RuntimeError("SMTP configuration incomplete. Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD environment variables or add them to a .env file")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_address
    # Plain-text fallback
    msg.set_content(body)

    # If caller supplied an HTML body in the env var `REPORT_HTML_TEMPLATE`, use it.
    # Otherwise callers can pass HTML using send_email(..., html=...)

    # Attach HTML alternative if provided
    if html:
        msg.add_alternative(html, subtype="html")

    server = smtplib.SMTP(host, port, timeout=30)
    try:
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass


def format_html_report(title: str, plain_text: str) -> str:
        """Return an HTML report converting plain-text tables into responsive HTML tables."""
        import re
        import html as _html

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        def block_is_table(lines: list[str]) -> bool:
            # Heuristic: at least 2 lines and splitting on 2+ spaces yields same column count
            if len(lines) < 2:
                return False
            counts = []
            for l in lines:
                s = l.strip()
                if not s:
                    continue
                parts = re.split(r" {2,}", s)
                counts.append(len(parts))
            return len(counts) >= 2 and len(set(counts)) == 1 and counts[0] >= 2

        def render_table(lines: list[str]) -> str:
            rows = [re.split(r" {2,}", l.strip()) for l in lines if l.strip()]
            # Escape cells
            esc = [[_html.escape(cell) for cell in row] for row in rows]
            header = esc[0]
            body_rows = esc[1:]
            ths = "".join(f"<th>{c}</th>" for c in header)
            trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body_rows)
            return f"<table class=\"report-table\"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"

        def render_block(lines: list[str]) -> str:
            if block_is_table(lines):
                return render_table(lines)
            # preserve monospace for code-like blocks
            text = _html.escape("\n".join(lines))
            return f"<pre class=\"report-pre\">{text}</pre>"

        parts = []
        cur = []
        for line in (plain_text or "").splitlines():
            if line.strip() == "":
                if cur:
                    parts.append(cur)
                    cur = []
                else:
                    # consecutive blank lines -> small gap
                    parts.append([])
            else:
                cur.append(line)
        if cur:
            parts.append(cur)

        rendered = []
        for block in parts:
            if not block:
                rendered.append('<div style="height:8px"></div>')
            else:
                rendered.append(render_block(block))

        body_html = "".join(rendered)

        html_template = f"""
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background:#f6f8fb; color:#0b1220; padding:20px; }}
                    .card {{ background: white; border-radius:8px; box-shadow:0 2px 6px rgba(11,17,32,0.08); padding:18px; max-width:900px; margin:0 auto }}
                    h1 {{ font-size:18px; margin:0 0 8px 0; }}
                    .meta {{ color:#6b7280; font-size:12px; margin-bottom:12px }}
                    .report-pre {{ background:#0b1220; color:#e6eef8; padding:12px; border-radius:6px; overflow:auto; white-space:pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', 'Courier New', monospace; font-size:12px }}
                    table.report-table {{ width:100%; border-collapse:collapse; margin:8px 0; font-size:13px }}
                    table.report-table thead th {{ text-align:left; background:#0b1220; color:#e6eef8; padding:8px; border-radius:4px }}
                    table.report-table td {{ padding:8px; border-bottom:1px solid #eef2f7; color:#0b1220 }}
                    @media (max-width:600px) {{ table.report-table thead {{ display:none }} table.report-table td {{ display:block; width:100% }} }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>{_html.escape(title)}</h1>
                    <div class="meta">Generated: {timestamp}</div>
                    {body_html}
                </div>
            </body>
        </html>
        """
        return html_template


def wrap_html(title: str, body_html: str) -> str:
    """Wrap pre-built HTML fragments into the site's email template without escaping."""
    from html import escape as _escape
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    # body_html is assumed to be safe/escaped by caller where necessary
    html_template = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background:#f6f8fb; color:#0b1220; padding:20px; }}
                .card {{ background: white; border-radius:8px; box-shadow:0 2px 6px rgba(11,17,32,0.08); padding:18px; max-width:900px; margin:0 auto }}
                h1 {{ font-size:18px; margin:0 0 8px 0; }}
                .meta {{ color:#6b7280; font-size:12px; margin-bottom:12px }}
                .report-pre {{ background:#0b1220; color:#e6eef8; padding:12px; border-radius:6px; overflow:auto; white-space:pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', 'Courier New', monospace; font-size:12px }}
                table.report-table {{ width:100%; border-collapse:collapse; margin:8px 0; font-size:13px }}
                table.report-table thead th {{ text-align:left; background:#0b1220; color:#e6eef8; padding:8px; border-radius:4px }}
                table.report-table td {{ padding:8px; border-bottom:1px solid #eef2f7; color:#0b1220 }}
                @media (max-width:600px) {{ table.report-table thead {{ display:none }} table.report-table td {{ display:block; width:100% }} }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>{_escape(title)}</h1>
                <div class="meta">Generated: {timestamp}</div>
                {body_html}
            </div>
        </body>
    </html>
    """
    return html_template
