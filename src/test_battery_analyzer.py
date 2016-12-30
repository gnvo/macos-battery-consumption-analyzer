#!/usr/bin/env python3

import unittest
import datetime
from battery_analyzer import process_event, Event, states, call_pmset, get_data_matrix
import numpy as np



class BatteryAnalyzerTestCase(unittest.TestCase):
    """Tests for `battery_analyzer.py`."""

    # def test_all_charges_parsed_correctly(self):
    #     power_eventlog = call_pmset()
    #     array_power_eventlog = power_eventlog.splitlines()
    #     parsed_events_and_nones = list(map(lambda line: process_event(line), array_power_eventlog))
    #     not_parsed_events = list(filter(lambda pean: type(pean) == str, parsed_events_and_nones))
    #     self.assertEqual(len(not_parsed_events), 0)


    def test_process_event_discharging(self):
        """Is discharging event correctly parsed?"""
        line1 = "2016-12-14 01:36:31 -0500 Wake                	Wake from Normal Sleep [CDNVA] due to EC.LidOpen/Lid Open: Using BATT (Charge:30%)"
        self.assertEqual(process_event(line1),
                         Event(
                            datetime.datetime(2016,12,14,1,36,31, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['discharging'],
                            30)
                         )
        line2 = "2016-12-14 01:38:46 -0500 Assertions          	Summary- [System: DeclUser kDisp] Using Batt(Charge: 40)"
        self.assertEqual(process_event(line2),
                         Event(
                            datetime.datetime(2016,12,14,1,38,46, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['discharging'],
                            40)
                         )
        line3 = "2016-12-14 03:09:52 -0500 Assertions          	Summary- [System: DeclUser SRPrevSleep IntPrevDisp kCPU kDisp] Using Batt(Charge: 100)"
        self.assertEqual(process_event(line3),
                         Event(
                            datetime.datetime(2016,12,14,3,9,52, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['discharging'],
                            100)
                         )
        line4 = "2016-12-14 03:10:05 -0500 Assertions          	Summary- [System: DeclUser IntPrevDisp kDisp] Using Batt(Charge: 89)"
        self.assertEqual(process_event(line4),
                         Event(
                            datetime.datetime(2016,12,14,3,10,5, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['discharging'],
                            89)
                         )
        line5 = "2016-12-15 02:08:09 -0500 Assertions          	Summary- [System: No Assertions] Using Batt(Charge: 72)"
        self.assertEqual(process_event(line5),
                         Event(
                            datetime.datetime(2016,12,15,2,8,9, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['discharging'],
                            72)
                         )


    def test_process_event_charging(self):
        """Is discharging event correctly parsed?"""
        line1 = "2016-12-14 01:56:29 -0500 Assertions          	Summary- [System: PrevIdle PrevDisp DeclUser kDisp] Using AC(Charge: 26)"
        self.assertEqual(process_event(line1),
                         Event(
                            datetime.datetime(2016,12,14,1,56,29, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['charging'],
                            26)
                         )


    def test_process_event_suspended(self):
        """Is discharging event correctly parsed?"""
        line1 = "2016-12-14 03:10:05 -0500 Sleep               	Entering Sleep state due to 'Clamshell Sleep':TCPKeepAlive=inactive Using Batt (Charge:100%) 10805 secs"
        self.assertEqual(process_event(line1),
                         Event(
                            datetime.datetime(2016,12,14,3,10,5, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
                            states['suspended'],
                            100)
                         )

    def test_get_data_matrix(self):
        """Is discharging event correctly parsed?"""
        events = list()
        # 2016-12-16 02:22:24-05:00, Discharging: 78
        # 2016-12-16 04:15:48-05:00, Suspended: 49
        # Elapsed time: 1:53:24, estimate hours: 6.517241
        events.append(Event(
            datetime.datetime(2016,12,14,2,22,24, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
            states['discharging'],
            78))
        events.append(Event(
            datetime.datetime(2016,12,14,4,15,28, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
            states['suspended'],
            49))
        # 2016-12-17 03:25:10-05:00, Discharging: 86
        # 2016-12-17 05:04:53-05:00, Suspended: 60
        # Elapsed time: 1:39:43, estimate hours: 6.392094
        events.append(Event(
            datetime.datetime(2016,12,17,3,25,10, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
            states['discharging'],
            86))
        events.append(Event(
            datetime.datetime(2016,12,17,5,4,53, tzinfo=datetime.timezone(datetime.timedelta(-1, 68400))),
            states['suspended'],
            60))
        matrix_ok = np.matrix('1.88444444 29 6.49808429;  1.66194444 26 6.39209402')
        discharge_periods, matrix_generated = get_data_matrix(events)
        self.assertTrue(np.allclose(matrix_ok, matrix_generated))

if __name__ == '__main__':
    unittest.main()
