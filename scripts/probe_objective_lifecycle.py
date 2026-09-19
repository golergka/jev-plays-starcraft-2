"""Live lifecycle checks for the experimental objective adapter, no campaign credit."""
import argparse
from pathlib import Path
import subprocess
import sys
from probe_api_lifetime import diagnostic_copy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('copy', type=Path)
parser.add_argument('--storm', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
if args.output.exists():
    raise FileExistsError(args.output)
bridge = Path(__file__).with_name('objective_state_bridge.galaxy').read_text()
script = '''include "TriggerLibs/NativeLib"
BRIDGE
bool ProbeLifecycle (bool testConds, bool runActions) {
    int objective;
    int resultObjective;
    bool passed = true;
    if (!runActions) { return true; }
    objective = JevObjectiveCreate(StringToText("Terminal creation"), StringToText("Test"), c_objectiveStateCompleted, false);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateCompleted;
    passed = passed && ObjectiveLastCreated() == objective;
    JevObjectiveSetState(objective, c_objectiveStateFailed);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateFailed;
    JevObjectiveSetName(objective, StringToText("Renamed failed objective"));
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateFailed;
    Wait(5.0, c_timeGame);
    JevObjectiveSetState(objective, c_objectiveStateHidden);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateHidden;
    JevObjectiveSetState(objective, c_objectiveStateActive);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateActive;
    JevObjectiveDestroy(objective);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateUnknown;
    objective = JevObjectiveCreateForPlayers(StringToText("Scoped creation"), StringToText("Test"), c_objectiveStateFailed, false, PlayerGroupSingle(2));
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateFailed;
    JevObjectiveDestroyAll(PlayerGroupSingle(2));
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateUnknown;
    objective = JevObjectiveCreate(StringToText("Fresh objective after destruction"), StringToText("Test"), c_objectiveStateActive, false);
    passed = passed && JevObjectiveGetState(objective) == c_objectiveStateActive;
    // Create the result carrier after DestroyAll, which also removes globally
    // visible objectives associated with that group.
    resultObjective = ObjectiveCreate(StringToText("Lifecycle diagnostic: no campaign credit"), StringToText("Waiting for checks"), c_objectiveStateActive, true);
    Wait(10.0, c_timeGame);
    if (passed) { ObjectiveSetState(resultObjective, c_objectiveStateCompleted); }
    else { ObjectiveSetState(resultObjective, c_objectiveStateFailed); }
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("ProbeLifecycle"));
}
'''.replace('BRIDGE', bridge)
diagnostic_copy(args.source, args.copy, args.storm, script)
subprocess.run([sys.executable, str(Path(__file__).with_name('probe_api_lifetime.py')),
                str(args.copy), '--output', str(args.output), '--samples', '4'], check=True)
