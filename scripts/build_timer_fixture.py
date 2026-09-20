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
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    TimerPause(countdown, true);
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    JevTimerWindowSetTimer(window, hidden);
    JevTimerWindowSetTitle(window, StringToText("REPLACED ELAPSED"));
    JevTimerWindowSetStyle(window, c_timerWindowStyleHorizontalTitleTime, true);
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    TimerWindowShow(window, PlayerGroupSingle(1), false);
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    TimerWindowShow(window, PlayerGroupSingle(1), true);
    JevVisibleTimerExport();
    Wait(10.0, c_timeGame);
    JevTimerWindowDestroy(window);
    JevTimerWindowDestroy(secret);
    JevVisibleTimerExport();
    return true;
}
void InitMap () {
    libNtve_InitLib();
    TriggerAddEventMapInit(TriggerCreate("TimerFixture"));
}
'''
diagnostic_copy(a.source,a.destination,a.storm,'include "TriggerLibs/NativeLib"\n'+bridge+fixture)
print(bank)
