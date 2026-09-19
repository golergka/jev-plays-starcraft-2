"""Reproduce objective/API-result behavior in an isolated copy, never campaign progress."""
import argparse
import subprocess
import sys
from pathlib import Path
from probe_api_lifetime import diagnostic_copy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('copy', type=Path)
parser.add_argument('--storm', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--state', choices=['Active','Failed','Completed'], default='Failed')
parser.add_argument('--hide-before-update', action='store_true',
                    help='Diagnostic: test whether invisible objectives still terminate API control')
args = parser.parse_args()
if args.output.exists():raise FileExistsError(args.output)
script = '''include "TriggerLibs/NativeLib"
bool ProbeObjective (bool testConds, bool runActions) {
    int objective;
    if (!runActions) { return true; }
    ObjectiveCreate(StringToText("Diagnostic main stays active"), StringToText("No campaign credit"), c_objectiveStateActive, true);
    ObjectiveCreate(StringToText("Diagnostic optional objective"), StringToText("No campaign credit"), c_objectiveStateActive, false);
    objective = ObjectiveLastCreated();
    Wait(5.0, c_timeGame);
    HIDE_OBJECTIVE
    ObjectiveSetState(objective, c_objectiveStateSTATE);
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("ProbeObjective"));
}
'''.replace('c_objectiveStateSTATE', 'c_objectiveState'+args.state).replace(
    'HIDE_OBJECTIVE', 'ObjectiveShow(objective, PlayerGroupAll(), false);'
    if args.hide_before_update else '')
diagnostic_copy(args.source,args.copy,args.storm,script)
subprocess.run([sys.executable,str(Path(__file__).with_name('probe_api_lifetime.py')),
                str(args.copy),'--output',str(args.output),'--samples','4'],check=True)
