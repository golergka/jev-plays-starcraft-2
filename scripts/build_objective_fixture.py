"""Build an ignored diagnostic map to test visible objective export."""
import argparse
import uuid
from pathlib import Path
from probe_api_lifetime import diagnostic_copy
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
p.add_argument('--storm',type=Path,required=True)
a=p.parse_args()
name='JevObjectiveFixture'+uuid.uuid4().hex
bridge=Path(__file__).with_name('objective_state_bridge.galaxy').read_text()
fixture='''
bank fixtureBank;
void Snapshot (string stage) {
    JevVisibleObjectiveExport(fixtureBank, 1);
    BankValueSetFromInt(fixtureBank, stage, "count", BankValueGetAsInt(fixtureBank, "Objectives", "count"));
    BankValueSetFromFlag(fixtureBank, stage, "section", BankSectionExists(fixtureBank, "Objective0"));
    if (BankSectionExists(fixtureBank, "Objective0")) {
        BankValueSetFromText(fixtureBank, stage, "name", BankValueGetAsText(fixtureBank, "Objective0", "name"));
        BankValueSetFromInt(fixtureBank, stage, "state", BankValueGetAsInt(fixtureBank, "Objective0", "state"));
    }
    BankSave(fixtureBank);
}
bool Fixture (bool testConds, bool runActions) {
    int objective;
    int secret;
    if (!runActions) { return true; }
    fixtureBank = BankLoad("FIXTURE_BANK", 1);
    objective = JevObjectiveCreate(StringToText("Visible objective"), StringToText("Visible detail"), c_objectiveStateActive, true);
    secret = JevObjectiveCreateForPlayers(StringToText("HIDDEN SECRET"), StringToText("HIDDEN DETAIL"), c_objectiveStateActive, false, PlayerGroupSingle(2));
    ObjectiveShow(objective, PlayerGroupSingle(1), true);
    Snapshot("created");
    JevObjectiveSetName(objective, StringToText("Updated objective"));
    Snapshot("renamed");
    JevObjectiveSetState(objective, c_objectiveStateCompleted);
    Snapshot("completed");
    ObjectiveShow(objective, PlayerGroupSingle(1), false);
    Snapshot("hidden");
    ObjectiveShow(objective, PlayerGroupSingle(1), true);
    Snapshot("shown");
    JevObjectiveDestroy(objective);
    Snapshot("destroyed");
    objective = JevObjectiveCreate(StringToText("Replacement"), StringToText("Replacement detail"), c_objectiveStateActive, false);
    ObjectiveShow(objective, PlayerGroupSingle(1), true);
    Snapshot("replacement");
    JevObjectiveRegister(objective);
    Snapshot("registered_twice");
    JevObjectiveSetState(objective, c_objectiveStateFailed);
    Snapshot("failed");
    ObjectiveSetPlayerGroup(objective, PlayerGroupSingle(2));
    Snapshot("other_player");
    ObjectiveSetPlayerGroup(objective, PlayerGroupSingle(1));
    ObjectiveShow(objective, PlayerGroupSingle(1), true);
    Snapshot("returned_player");
    JevObjectiveDestroyAll(PlayerGroupSingle(1));
    Snapshot("destroy_all");
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("Fixture"));
}
'''.replace('FIXTURE_BANK',name)
diagnostic_copy(a.source,a.destination,a.storm,'include "TriggerLibs/NativeLib"\n'+bridge+fixture)
print(name)
