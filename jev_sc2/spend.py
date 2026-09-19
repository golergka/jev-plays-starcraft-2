"""Persistent, process-shared soft dollar budget for paid Jev requests."""
import json
import math
import sqlite3
import time
import uuid
from pathlib import Path


class SpendThrottled(Exception):
    def __init__(self, retry_after, spent, limit):
        self.retry_after, self.spent, self.limit = retry_after, spent, limit
        super().__init__(f'Rolling Jev budget ${spent:.4f}/${limit:.4f}; retry in {retry_after:.1f}s')


class RollingSpend:
    def __init__(self, path, limit=0.10, window=300, reserve=0.005, clock=time.time, config_path=None):
        if not all(math.isfinite(v) and v > 0 for v in (limit, window, reserve)):
            raise ValueError('Spend limit, window and reservation must be positive finite numbers')
        self.path, self.base_limit, self.window, self.reserve, self.clock = Path(path), limit, window, reserve, clock
        self.charged = 0.0  # Local pacing accounting, including unknown bills.
        self._pending = {}
        self.config_path = Path(config_path) if config_path else None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS spend (id TEXT PRIMARY KEY, time REAL, cost REAL)')
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY)')

    @property
    def limit(self):
        if self.config_path is None or not self.config_path.exists():
            return self.base_limit
        settings = json.loads(self.config_path.read_text())
        start, target = settings['start_usd_per_5_min'], settings['target_usd_per_5_min']
        duration, began = settings['ramp_seconds'], settings['started_at']
        if not all(math.isfinite(v) for v in (start,target,duration,began)) or min(start,target) <= 0 or duration < 0:
            raise ValueError('Invalid Jev budget ramp configuration')
        progress = min(1,max(0,(self.clock()-began)/duration)) if duration else 1
        return start+(target-start)*progress

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def seed(self, runs):
        """One-time import of recent pre-governor usage; never reset on restart."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM meta WHERE key='seeded'").fetchone():
                return
            cutoff = self.clock()-self.window
            for path in Path(runs).glob('*/events.jsonl'):
                if path.stat().st_mtime < cutoff:
                    continue
                with path.open() as stream:
                    for line in stream:
                        try:
                            row = json.loads(line)
                            if row.get('event') != 'jev' or row.get('time', 0) <= cutoff:
                                continue
                            cost = row['response']['usage'].get('cost')
                            if cost is None:
                                cost = self.reserve
                            if math.isfinite(cost) and cost >= 0:
                                db.execute('INSERT OR IGNORE INTO spend VALUES (?,?,?)',
                                           (f"{path}:{row['time']}", row['time'], cost))
                        except (ValueError, KeyError, TypeError):
                            continue
            db.execute("INSERT INTO meta VALUES ('seeded')")

    def acquire(self):
        now = self.clock()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM spend WHERE time <= ?', (now-self.window,))
            rows = db.execute('SELECT time,cost FROM spend ORDER BY time').fetchall()
            spent = sum(cost for _, cost in rows)
            limit = self.limit
            # Reserve conservatively before dispatch, including concurrent calls.
            estimate = min(limit, max(self.reserve, max((c for _, c in rows), default=0)))
            if spent + estimate > limit + 1e-12:
                remaining = spent
                retry_at = now+self.window
                for at, cost in rows:
                    remaining -= cost
                    if remaining + estimate <= limit + 1e-12:
                        retry_at = at+self.window
                        break
                raise SpendThrottled(max(0.05,retry_at-now),spent,limit)
            token = uuid.uuid4().hex
            db.execute('INSERT INTO spend VALUES (?,?,?)', (token,now,estimate))
            self.charged += estimate
            self._pending[token] = estimate
            return token

    def settle(self, token, cost):
        # Unknown/failed/cancelled responses keep their reservation for the window.
        if cost is None or not math.isfinite(cost) or cost < 0:
            return
        with self.connect() as db:
            db.execute('UPDATE spend SET cost=?, time=? WHERE id=?', (cost,self.clock(),token))
        if token in self._pending:
            self.charged += cost-self._pending.pop(token)
