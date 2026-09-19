"""Verify native-bank ending telemetry in a synthetic map copy, never campaign credit."""
import argparse
import asyncio
import json
from pathlib import Path
import time
from probe_api_lifetime import diagnostic_copy
from jev_sc2.outcome import OutcomeMonitor
from jev_sc2.sc2 import SC2
from s2clientprotocol import sc2api_pb2 as sc


async def main(args):
    if args.output.exists():
        raise FileExistsError(args.output)
    ending = 'JevOutcomeRecord("victory");' if args.result == 'victory' else 'JevGameOver(1, c_gameOverDefeat, true, false);'
    script = '''include "TriggerLibs/NativeLib"
include "TriggerLibs/JevObjectiveBridge"
bool ProbeOutcome (bool testConds, bool runActions) {
    if (!runActions) { return true; }
    Wait(5.0, c_timeGame);
    ENDING
    return true;
}
void InitMap () {
    JevOutcomeInit();
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("ProbeOutcome"));
}
'''.replace('ENDING', ending)
    diagnostic_copy(args.source,args.copy,args.storm,script)
    monitor = OutcomeMonitor.for_map(args.source, time.time())
    if monitor is None:
        raise ValueError('Source must have outcome instrumentation')
    client = await SC2.connect(5001)
    records = []
    try:
        await client.request('ping',sc.RequestPing())
        await client.start(args.copy)
        for _ in range(25):
            result = monitor.poll()
            records.append({'time':time.time(),'saw_active':monitor.saw_active,'result':result})
            if result:
                break
            await asyncio.sleep(1)
    finally:
        await client.ws.close()
        args.output.write_text(json.dumps({'campaign_credit':False,'expected':args.result,'records':records},indent=2)+'\n')
    if not records[-1]['result'] or records[-1]['result']['status'] != args.result:
        raise RuntimeError('Native outcome telemetry did not match expectation')
    print(json.dumps(records[-1]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('copy', type=Path)
    parser.add_argument('--storm', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--result', choices=('victory','defeat'), required=True)
    asyncio.run(main(parser.parse_args()))
