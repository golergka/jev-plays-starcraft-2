"""Build an ignored diagnostic map, never a campaign completion candidate."""
import argparse
import uuid
from pathlib import Path
from probe_api_lifetime import diagnostic_copy

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
p.add_argument('--storm',type=Path,required=True)
a=p.parse_args()
bank='JevTimerFixture'+uuid.uuid4().hex
bridge=Path(__file__).with_name('visible_timer_bridge.galaxy').read_text().replace('TIMER_BANK_NAME',bank)
fixture='''
void FixtureSnapshot (string stage) {
    JevVisibleTimerExport();
    BankValueSetFromInt(JevVisibleTimerBank, stage, "count", BankValueGetAsInt(JevVisibleTimerBank, "Context", "count"));
    BankValueSetFromFlag(JevVisibleTimerBank, stage, "timer_section", BankSectionExists(JevVisibleTimerBank, "Timer0"));
    if (BankSectionExists(JevVisibleTimerBank, "Timer0")) {
        BankValueSetFromText(JevVisibleTimerBank, stage, "title", BankValueGetAsText(JevVisibleTimerBank, "Timer0", "title"));
        BankValueSetFromFixed(JevVisibleTimerBank, stage, "value", BankValueGetAsFixed(JevVisibleTimerBank, "Timer0", "value"));
        BankValueSetFromFlag(JevVisibleTimerBank, stage, "elapsed", BankValueGetAsFlag(JevVisibleTimerBank, "Timer0", "elapsed"));
    }
    BankSave(JevVisibleTimerBank);
}
bool TimerFixture (bool testConds, bool runActions) {
    timer countdown;
    timer hidden;
    int window;
    int secret;
    if (!runActions) { return true; }
    JevVisibleTimerInit(1);
    countdown = TimerCreate();
    hidden = TimerCreate();
    TimerStart(countdown, 60.0, false, c_timeGame);
    TimerStart(hidden, 999.0, false, c_timeGame);
    window = JevTimerWindowCreate(countdown, StringToText("VISIBLE FIXTURE 60"), true, false);
    secret = JevTimerWindowCreate(hidden, StringToText("HIDDEN FIXTURE"), false, false);
    FixtureSnapshot("created");
    Wait(10.0, c_timeGame);
    TimerPause(countdown, true);
    FixtureSnapshot("paused");
    Wait(10.0, c_timeGame);
    FixtureSnapshot("still_paused");
    Wait(10.0, c_timeGame);
    JevTimerWindowSetTimer(window, hidden);
    JevTimerWindowSetTitle(window, StringToText("REPLACED ELAPSED"));
    JevTimerWindowSetStyle(window, c_timerWindowStyleHorizontalTitleTime, true);
    FixtureSnapshot("replaced");
    Wait(10.0, c_timeGame);
    TimerWindowShow(window, PlayerGroupSingle(1), false);
    FixtureSnapshot("hidden");
    Wait(10.0, c_timeGame);
    TimerWindowShow(window, PlayerGroupSingle(1), true);
    FixtureSnapshot("shown");
    Wait(10.0, c_timeGame);
    JevTimerWindowDestroy(window);
    JevTimerWindowDestroy(secret);
    FixtureSnapshot("destroyed");
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("TimerFixture"));
}
'''
diagnostic_copy(a.source,a.destination,a.storm,'include "TriggerLibs/NativeLib"\n'+bridge+fixture)
print(bank)
