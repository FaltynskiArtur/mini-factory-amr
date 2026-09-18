import math

from amr_monitor.obstacle_monitor import classify_distance


def test_clear_distance():
    assert classify_distance(2.0, 0.45, 0.80) == 'CLEAR'


def test_warning_distance():
    assert classify_distance(0.60, 0.45, 0.80) == 'WARNING'


def test_stop_distance():
    assert classify_distance(0.30, 0.45, 0.80) == 'STOP'


def test_stop_boundary():
    assert classify_distance(0.45, 0.45, 0.80) == 'STOP'


def test_warning_boundary():
    assert classify_distance(0.80, 0.45, 0.80) == 'WARNING'


def test_just_above_warning_boundary():
    assert classify_distance(
        math.nextafter(0.80, math.inf),
        0.45,
        0.80,
    ) == 'CLEAR'
