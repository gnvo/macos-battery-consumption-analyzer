#!/usr/bin/env python

import unittest
from datetime import datetime
from battery_analyzer import process_logevent, get_data_matrix
import numpy as np
from dateutil.tz import tzoffset


class BatteryAnalyzerTestCase(unittest.TestCase):
    """Tests for `battery_analyzer.py`."""

    def test_process_logevent(self):
        """Is discharging event correctly parsed?"""
        line = "2016-12-14 01:36:31 -0500 Wake                	Wake from Normal Sleep [CDNVA] due to EC.LidOpen/Lid Open: Using BATT (Charge:30%)"
        discharge_event = process_logevent(line, None)
        line = "2016-12-14 01:56:29 -0500 Assertions          	Summary- [System: PrevIdle PrevDisp DeclUser kDisp] Using AC(Charge: 26)"
        discharge_event = process_logevent(line, discharge_event)
        self.assertEqual(discharge_event.start_date_time, datetime(2016, 12, 14, 1, 36, 31, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.start_charge, 30)
        self.assertEqual(discharge_event.end_date_time, datetime(2016, 12, 14, 1, 56, 29, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.end_charge, 26)
        self.assertEqual(discharge_event.elapsed_hours(), 0.33277777777777773)
        self.assertEqual(discharge_event.diff_charge(), 4)
        self.assertEqual(discharge_event.estimated_hours(), 8.319444444444443)

        line = "2016-12-15 01:38:46 -0500 Assertions          	Summary- [System: DeclUser kDisp] Using Batt(Charge: 40)"
        discharge_event = process_logevent(line, None)
        line = "2016-12-15 03:10:05 -0500 Sleep               	Entering Sleep state due to 'Clamshell Sleep':TCPKeepAlive=inactive Using Batt (Charge:20%) 10805 secs"
        discharge_event = process_logevent(line, discharge_event)
        self.assertEqual(discharge_event.start_date_time, datetime(2016, 12, 15, 1, 38, 46, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.start_charge, 40)
        self.assertEqual(discharge_event.end_date_time, datetime(2016, 12, 15, 3, 10, 5, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.end_charge, 20)
        self.assertEqual(discharge_event.elapsed_hours(), 1.5219444444444443)
        self.assertEqual(discharge_event.diff_charge(), 20)
        self.assertEqual(discharge_event.estimated_hours(), 7.609722222222222)

        line = "2016-12-14 03:09:52 -0500 Assertions          	Summary- [System: DeclUser SRPrevSleep IntPrevDisp kCPU kDisp] Using Batt(Charge: 100)"
        discharge_event = process_logevent(line, None)
        self.assertEqual(discharge_event.start_date_time, datetime(2016, 12, 14, 3, 9, 52, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.start_charge, 100)

        line = "2016-12-14 03:10:05 -0500 Assertions          	Summary- [System: DeclUser IntPrevDisp kDisp] Using Batt(Charge: 89)"
        discharge_event = process_logevent(line, None)
        self.assertEqual(discharge_event.start_date_time, datetime(2016, 12, 14, 3, 10, 5, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.start_charge, 89)

        line = "2016-12-15 02:08:09 -0500 Assertions          	Summary- [System: No Assertions] Using Batt(Charge: 72)"
        discharge_event = process_logevent(line, None)
        self.assertEqual(discharge_event.start_date_time, datetime(2016, 12, 15, 2, 8, 9, tzinfo=tzoffset(None, -18000)))
        self.assertEqual(discharge_event.start_charge, 72)

    def test_get_data_matrix(self):
        """Is discharging event correctly parsed?"""
        events = []
        events.append("2016-12-14 01:36:31 -0500 Wake                	Wake from Normal Sleep [CDNVA] due to EC.LidOpen/Lid Open: Using BATT (Charge:30%)")
        events.append("2016-12-14 01:56:29 -0500 Assertions          	Summary- [System: PrevIdle PrevDisp DeclUser kDisp] Using AC(Charge: 26)")
        events.append("2016-12-15 01:38:46 -0500 Assertions          	Summary- [System: DeclUser kDisp] Using Batt(Charge: 40)")
        events.append("2016-12-15 03:10:05 -0500 Sleep               	Entering Sleep state due to 'Clamshell Sleep':TCPKeepAlive=inactive Using Batt (Charge:20%) 10805 secs")
        matrix_ok = np.matrix('0.332777777778 4. 8.31944444444 ; 1.52194444444 20. 7.60972222222')
        self.assertTrue(np.allclose(matrix_ok, get_data_matrix(events)))

if __name__ == '__main__':
    unittest.main()
