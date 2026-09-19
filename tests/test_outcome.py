import os
from pathlib import Path
import hashlib
import json
import pytest
from jev_sc2.outcome import OutcomeMonitor


def bank(path, result, stamp=20):
    path.write_text(f'<Bank><Section name="Outcome"><Key name="result"><Value string="{result}"/></Key>'
                    '<Key name="engine_time"><Value int="123"/></Key></Section></Bank>')
    os.utime(path, (stamp, stamp))


def test_requires_fresh_active_then_terminal_marker(tmp_path):
    path = tmp_path/'outcome.SC2Bank'
    monitor = OutcomeMonitor(path, started_at=10)
    bank(path, 'victory', stamp=5)
    assert monitor.poll() is None
    bank(path, 'victory')
    assert monitor.poll() is None  # Fresh timestamp alone cannot credit a stale win.
    bank(path, 'active')
    assert monitor.poll() is None
    bank(path, 'victory', stamp=30)
    assert monitor.poll()['status'] == 'victory'
    assert monitor.poll()['credit_enabled'] is False


def test_partial_writes_and_unknown_results_do_not_end_run(tmp_path):
    path = tmp_path/'outcome.SC2Bank'
    monitor = OutcomeMonitor(path, 0)
    assert monitor.poll() is None
    path.write_text('<Bank>')
    assert monitor.poll() is None
    bank(path, 'active')
    monitor.poll()
    bank(path, 'bonus-completed')
    assert monitor.poll() is None
    bank(path, 'defeat')
    assert monitor.poll()['status'] == 'defeat'


def test_manifest_requires_map_integrity_and_restricted_bank_name(tmp_path):
    path = tmp_path/'map.SC2Map'
    path.write_bytes(b'test-map')
    metadata = {'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'outcome_bank':'JevOutcome'+'a'*32}
    manifest = path.with_suffix('.bridge.json')
    manifest.write_text(json.dumps(metadata))
    monitor = OutcomeMonitor.for_map(path, 0, tmp_path)
    assert monitor.path == tmp_path/(metadata['outcome_bank']+'.SC2Bank')
    path.write_bytes(b'modified')
    with pytest.raises(ValueError, match='does not match'):
        OutcomeMonitor.for_map(path, 0, tmp_path)
    metadata['outcome_bank'] = '../another-bank'
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='Invalid'):
        OutcomeMonitor.for_map(path, 0, tmp_path)


def test_resume_can_arm_from_existing_active_but_never_existing_terminal(tmp_path):
    path = tmp_path/'outcome.SC2Bank'
    bank(path, 'victory', stamp=5)
    assert OutcomeMonitor(path, 0).poll() is None
    monitor = OutcomeMonitor(path, 0)
    bank(path, 'active', stamp=5)
    assert monitor.poll() is None
    assert monitor.saw_active
    bank(path, 'defeat', stamp=30)
    assert monitor.poll()['status'] == 'defeat'
