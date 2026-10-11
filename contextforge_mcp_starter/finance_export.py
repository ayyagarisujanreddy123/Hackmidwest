"""Deterministic CSV rendering of actual, bounded finance tool results."""

import csv
import hashlib
import io
import re


CSV_COLUMNS = ["symbol", "trading_date", "time", "open", "high", "low", "close",
               "adjusted_close", "volume", "currency", "exchange_timezone", "retrieved_at", "source_url"]


def _csv_cell(value):
    # Quote escaping alone does not prevent spreadsheet formula interpretation.
    if isinstance(value, str) and value.lstrip(" ").startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def render_history_csv(batch: dict) -> dict:
    """Return content and a manifest; never create files or serve public URLs."""
    rows, manifest = [], []
    for result in batch["results"]:
        history = result["data"]
        manifest.append({"symbol": result["symbol"], "status": result["status"],
                         "message": result["message"], "retrieved_at": result["retrieved_at"],
                         "cached": result["cached"], "cache_age_seconds": result["cache_age_seconds"],
                         "row_count": history["row_count"] if history else 0,
                         "first_date": history["first_date"] if history else None,
                         "last_date": history["last_date"] if history else None,
                         "truncated": history["truncated"] if history else False})
        if result["status"] != "ok":
            continue
        for row in history["rows"]:
            rows.append({**row, "symbol": result["symbol"], "currency": history["currency"],
                         "exchange_timezone": history["exchange_timezone"],
                         "retrieved_at": result["retrieved_at"], "source_url": result["source_refs"][0]})
    rows.sort(key=lambda row: (row["trading_date"], row["symbol"], row["time"]))
    content = None
    if rows:
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: _csv_cell(value) for key, value in row.items()} for row in rows)
        content = stream.getvalue()
        if len(content.encode("utf-8")) > 512 * 1024:
            raise ValueError("CSV exceeds 512 KiB; request fewer symbols or a shorter date range.")
    window = batch["period"] or batch["start_date"] + "_to_" + batch["end_date"]
    basename = "_".join(re.sub(r"[^A-Z0-9._-]", "_", symbol) for symbol in batch["symbols"])
    return {"filename": basename + "_" + window + "_" + batch["interval"] + ".csv",
            "mime_type": "text/csv", "encoding": "utf-8", "csv": content,
            "columns": CSV_COLUMNS.copy(), "row_count": len(rows), "results": manifest,
            "first_date": rows[0]["trading_date"] if rows else None,
            "last_date": rows[-1]["trading_date"] if rows else None,
            "truncated": batch["truncated"], "auto_adjust": False,
            "byte_count": len(content.encode("utf-8")) if content else 0,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest() if content else None}
