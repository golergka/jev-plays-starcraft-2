"""Trace accepted joint boarding requests to observed cargo, without inferring deaths."""
import json
import sys
from pathlib import Path


def observed_units(row):
    if row.get('event') != 'jev':
        return None
    units = row.get('state', {}).get('units')
    if isinstance(units, dict) and 'columns' in units and 'rows' in units:
        return [dict(zip(units['columns'], values)) for values in units['rows']]
    return units if isinstance(units, list) else None


def report(rows):
    observations = [(r['time'], units) for r in rows
                    if (units := observed_units(r)) is not None]
    jobs = []
    for row in rows:
        if row.get('event') != 'exclusive_job_coordination':
            continue
        for command in row.get('accepted_jobs', []):
            actor, target = command['unit_tag'], command['target_tag']
            entry = {'loop': row['loop'], 'command': command,
                     'status': 'not_confirmed_in_recorded_cargo'}
            for timestamp, units in observations:
                if timestamp <= row['time']:
                    continue
                carrier = next((u for u in units if u['tag'] == actor), None)
                if carrier is None:
                    continue
                passenger = next((p for p in carrier.get('cargo', {}).get('passengers', [])
                                  if p['tag'] == target), None)
                if passenger:
                    entry.update(status='observed_in_selected_carrier', passenger=passenger,
                                 seconds_until_observed=round(timestamp-row['time'], 3))
                    break
            jobs.append(entry)
    return {'scope': 'Accepted joint requests correlated with later logged unit cargo. '
                     'Observation confirms presence, not causation. Missing observations do not prove failure or death.',
            'jobs': jobs, 'accepted': len(jobs),
            'observed_in_selected_carrier': sum(j['status']=='observed_in_selected_carrier' for j in jobs)}


if __name__ == '__main__':
    rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
    print(json.dumps(report(rows), indent=2))
