"""Verify that an embedded campaign library actually uses adapted objective reads.

Synthetic assertion only: the campaign mission script is replaced in a COPY.
This result can never establish mission completion.
"""
import argparse
from pathlib import Path
import subprocess
import sys
from probe_api_lifetime import diagnostic_copy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path, help='Map produced by build_objective_bridge.py')
parser.add_argument('copy', type=Path)
parser.add_argument('--storm', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
if args.output.exists():
    raise FileExistsError(args.output)
script = '''include "TriggerLibs/NativeLib"
include "TriggerLibs/JevObjectiveBridge"
include "TriggerLibs/CampaignLib"
bool ProbeCampaignBridge (bool testConds, bool runActions) {
    int objective;
    bool passed;
    if (!runActions) { return true; }
    objective = JevObjectiveCreate(StringToText("Library bridge assertion: no campaign credit"), StringToText("Testing native versus adapted reads"), c_objectiveStateCompleted, false);
    libCamp_gv_tS_MissionObjectives[1][1] = 1;
    libCamp_gv_tS_MissionObjObjective[1] = objective;
    passed = ObjectiveGetState(objective) == c_objectiveStateActive;
    passed = passed && libCamp_gf_TS_AllObjectivesCompletedForMission(1);
    Wait(15.0, c_timeGame);
    if (passed) { ObjectiveSetState(objective, c_objectiveStateCompleted); }
    else { ObjectiveSetState(objective, c_objectiveStateFailed); }
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("ProbeCampaignBridge"));
}
'''
diagnostic_copy(args.source, args.copy, args.storm, script)
subprocess.run([sys.executable, str(Path(__file__).with_name('probe_api_lifetime.py')),
                str(args.copy), '--output', str(args.output), '--samples', '4'], check=True)
