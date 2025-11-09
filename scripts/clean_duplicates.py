#!/usr/bin/env python3
import os
import re
import sqlite3
from urllib.parse import urlparse, urlunparse

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'decimal_scraped_data.db')
DB_PATH = os.path.abspath(DB_PATH)


def make_dedupe_key(url: str) -> str:
    try:
        parsed = urlparse(url)
        scheme = (parsed.scheme or 'http').lower()
        netloc = (parsed.netloc or '').lower()
        path = parsed.path or '/'
        # Collapse multiple trailing slashes to single and ensure at least '/'
        if path != '/':
            path = re.sub(r'/+$', '/', path)
        else:
            path = '/'
        return urlunparse((scheme, netloc, path, '', '', ''))
    except Exception:
        return url


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create index if not present
    cur.execute("CREATE INDEX IF NOT EXISTS idx_scraped_url ON scraped_data(url)")

    # Load all ids and urls
    cur.execute("SELECT id, url FROM scraped_data ORDER BY id ASC")
    rows = cur.fetchall()

    keep_id_by_key = {}
    ids_by_key = {}
    updates = []

    for row_id, url in rows:
        url = url or ''
        key = make_dedupe_key(url)
        if key not in keep_id_by_key:
            keep_id_by_key[key] = row_id
        ids_by_key.setdefault(key, []).append(row_id)
        # If stored URL differs from canonical key, schedule update for the kept row
        if row_id == keep_id_by_key[key] and url != key:
            updates.append((key, row_id))

    # Determine duplicates to delete (all but the earliest per key)
    to_delete = []
    for key, ids in ids_by_key.items():
        ids_sorted = sorted(ids)
        to_delete.extend(ids_sorted[1:])

    print(f"Found {len(rows)} total rows")
    print(f"Canonical keys: {len(keep_id_by_key)}")
    print(f"Rows to delete (duplicates): {len(to_delete)}")
    print(f"Rows to update (set canonical URL): {len(updates)}")

    # Apply updates in a transaction
    try:
        conn.execute('BEGIN')
        if updates:
            cur.executemany("UPDATE scraped_data SET url = ? WHERE id = ?", updates)
        if to_delete:
            # Delete in chunks to avoid parameter limits
            chunk = 500
            for i in range(0, len(to_delete), chunk):
                batch = to_delete[i:i+chunk]
                q = f"DELETE FROM scraped_data WHERE id IN ({','.join('?' for _ in batch)})"
                cur.execute(q, batch)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Cleanup complete.")


if __name__ == '__main__':
    main()
