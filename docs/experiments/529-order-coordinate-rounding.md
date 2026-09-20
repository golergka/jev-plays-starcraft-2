# Lab 529: exact float equality misses engine-rounded order destinations

Trial527 repeated attack-move at loops8344,9432,11213. Recorded current target
x=153.333251953125; submitted protobuf target x=153.3333282470703; y=48 in both.
Difference7.62939453125e-05 map units. Diagnostic logging confirms actual observed
Attack Attack ability23, so this case is not an ability-ID mismatch.

Use absolute per-axis tolerance0.0001, with zero relative tolerance, for point
target matching. This is a deliberately tiny engineering tolerance supported
by the observed pair, not a claim about all engine coordinate quantization.
Unit targets still match exactly; multiple queued orders and production remain
excluded. A regression test uses the actual observed values and verifies a
0.001 target change is not preserved. Eight focused tests pass.

The active trial527 imported its framework helper at controller startup and
retains exact comparison. This commit does not retroactively activate the fix
or justify restarting an unfinished mission. The next controller run will use
this tolerance. Therefore zero preservation events so far do not evaluate the
corrected rule's gameplay effect.
