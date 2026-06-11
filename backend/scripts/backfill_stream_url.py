import os
import sys
sys.path.append(os.getcwd())
from sqlalchemy import inspect, text
from app.core.database import Engine
from app.core.config import settings

inspector = inspect(Engine)
cols = [c['name'] for c in inspector.get_columns('feeds')]
print('Feed cols before:', cols)

with Engine.begin() as conn:
    # Add source_url column if missing
    if 'source_url' not in cols:
        print('Adding source_url column')
        conn.execute(text("ALTER TABLE feeds ADD COLUMN source_url VARCHAR"))
        print('source_url added')
    else:
        print('source_url already present')

    # Refresh inspector columns
    cols = [c['name'] for c in inspector.get_columns('feeds')]

    # Add stream_url column if missing
    if 'stream_url' not in cols:
        print('Adding stream_url column')
        conn.execute(text("ALTER TABLE feeds ADD COLUMN stream_url VARCHAR"))
        print('stream_url added')
    else:
        print('stream_url already present')

    # Backfill stream_url using basename of source_url when possible
    rows = conn.execute(text("SELECT id, source_url, stream_url FROM feeds")).fetchall()
    updates = 0
    for row in rows:
        fid = row[0]
        src = row[1]
        cur = row[2]
        if (cur is None or cur == '') and src:
            fname = os.path.basename(src)
            stream = f"/uploads/{fname}"
            conn.execute(text("UPDATE feeds SET stream_url = :s WHERE id = :id"), {'s': stream, 'id': fid})
            updates += 1
    print('Backfilled', updates, 'rows')

    rows2 = conn.execute(text("SELECT id, source_url, stream_url FROM feeds")).fetchall()
    print('Sample rows:')
    for r in rows2[:10]:
        print(r)

    # Also attempt to map any files in the mock feed directory to feed ids
    try:
        files = os.listdir(settings.MOCK_FEED_DIR)
    except Exception:
        files = []

    file_updates = 0
    for fname in files:
        if not fname.lower().endswith(('.mp4', '.mov', '.mkv', '.avi', '.webm')):
            continue
        name_no_ext = os.path.splitext(fname)[0]
        stream_path = f"/uploads/{fname}"
        # Update feeds whose id matches the filename (no extension) and missing stream_url
        res = conn.execute(text("UPDATE feeds SET stream_url = :s WHERE id = :id AND (stream_url IS NULL OR stream_url='')"), {'s': stream_path, 'id': name_no_ext})
        # Count rows updated if supported (sqlite returns cursor.rowcount)
        try:
            file_updates += res.rowcount or 0
        except Exception:
            file_updates += 0

    print('Mapped', file_updates, 'feeds from files in mock_feeds')
