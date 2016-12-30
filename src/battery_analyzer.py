#!/usr/bin/env python3

import os
import multiprocessing
import re
import datetime
import numpy as np
import matplotlib.pyplot as plt


re_line_splitter = re.compile(r'(\d{4}[-]\d{2}[-]\d{2}\s\d{2}[:]\d{2}[:]\d{2}\s\S+)\s+(\S+)\s+(.*)')
re_extract_charge = re.compile(r'.*Charge:[ ]*(\d+).*')
datetime_format = "%Y-%m-%d %H:%M:%S %z"
states = {'discharging' : "Discharging", 'charging': "Charging", 'suspended': "Suspended"}
class Event(object):
    def __init__(self, timestamp, state, charge):
        self.timestamp = timestamp
        self.state = state
        self.charge = charge
    def __repr__(self):
        return "%s, %s: %s" % (self.timestamp, self.state, self.charge)
    def __str__(self):
        return "%s, %s: %s" % (self.timestamp, self.state, self.charge)
    def __eq__(self, other):
        return type(other) == Event and \
               self.timestamp == other.timestamp and \
               self.state == other.state and \
               self.charge == other.charge

class DischargePeriod(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def diff_charge(self):
        return self.start.charge - self.end.charge
    def diff_time(self):
        return self.end.timestamp - self.start.timestamp
    def elapsed_hours(self):
        return self.diff_time().seconds / 60 / 60
    def elapsed_time(self):
        m, s = divmod(self.diff_time().seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    def estimated_hours(self):
        return 100 * self.diff_time().seconds / self.diff_charge() / 60 / 60
    def start_timestamp_as_utc(self):
        return self.start.timestamp.astimezone(tz=datetime.timezone.utc).timestamp()
    def __str__(self):
        # return start.__str__() + "\n" + end.__str__() + "\nElapsed time: %s, estimate hours: %f" % (discharge_period.elapsed_time(), discharge_period.estimated_hours())
        return "%f,%d,%f,%f" % (self.start_timestamp_as_utc(),self.diff_charge(), self.elapsed_hours(), self.estimated_hours())

def call_pmset():
    return os.popen("pmset -g log").read()

def process_event(line):
    m = re_line_splitter.match(line)
    if m:
        event_type = m.group(2)
        description = m.group(3)
        state = None
        if event_type == "Wake" and "Using BATT" in description or \
          event_type == "Assertions" and "using batt" in description.lower():
            state = states['discharging']
        elif event_type == "Sleep" and "using batt" in description.lower():
            state = states['suspended']
        elif event_type == "Assertions" and "using ac" in description.lower() or \
          event_type in ["Wake","Sleep"] and "using ac" in description.lower():
           state = states['charging']
        if state:
            m2 = re_extract_charge.match(description)
            if m2:
                timestamp = datetime.datetime.strptime(m.group(1), datetime_format)
                charge = int(m2.group(1))
                return Event(timestamp, state, charge)
            else:
                return line
    return None

def get_battery_change_events():
    power_eventlog = call_pmset()
    array_power_eventlog = power_eventlog.splitlines()
    parsed_events_and_nones = list(map(lambda line: process_event(line), array_power_eventlog))
    return list(filter(lambda pean: type(pean) == Event, parsed_events_and_nones))

# TODO: reduce the number of loops through all the logdata.
def get_data_matrix(events):
    discharge_periods = list()
    discharging = False
    start = None
    for e in events:
        if e.state == states['discharging']:
            if not discharging:
                start = e
                discharging = True
        elif start:
            end = e
            discharge_period = DischargePeriod(start, end)
            if discharge_period.diff_charge() > 0:
                discharge_periods.append(discharge_period)
            start = None
            discharging = False
    number_of_events = len(discharge_periods)
    matrix = np.zeros(shape=(number_of_events,3))
    for i, dp in enumerate(discharge_periods):
        matrix[i, 0] = dp.elapsed_hours()
        matrix[i, 1] = dp.diff_charge()
        matrix[i, 2] = dp.estimated_hours()
    return discharge_periods, matrix

def plot_data(discharge_periods, matrix):
    datetimes = np.asarray(list(map(lambda dp: dp.start.timestamp, discharge_periods))) #TODO:remove this hacky line!!
    total_elapsed_hours = np.sum(matrix[:,0])
    weights = matrix[:,0]/total_elapsed_hours
    weighted_mean_estimated_hours = np.sum(matrix[:,2] * weights)
    mean_estimated_hours = np.mean(matrix[:,2])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    col = ax.scatter(matrix[:,2], matrix[:,1], s=3000*weights, edgecolors='none', picker=True)
    ax.axvline(x=weighted_mean_estimated_hours, linewidth=2, color = 'r')
    ax.axvline(x=mean_estimated_hours, linewidth=2, color = 'g')
    ax.annotate('weighted mean %s' % weighted_mean_estimated_hours,
                xy=(np.max(matrix[:,2]),np.max(matrix[:,1])),
                xytext=(-10, 0), ha='right', color = 'r',
                textcoords='offset points')
    ax.annotate('mean %s' % mean_estimated_hours,
                xy=(np.max(matrix[:,2]),np.max(matrix[:,1])),
                xytext=(-10, -20), ha='right', color = 'g',
                textcoords='offset points')
    def onpick(event):
        ind = event.ind
        print ('Date and time: %s\nPercentage of battery discharge: %d\nDuration of period: %f\nEstimated battery life: %f\n\n' % (datetimes[ind][0],np.take(matrix[:,1], ind),np.take(matrix[:,0], ind),np.take(matrix[:,2], ind)))
    fig.canvas.mpl_connect('pick_event', onpick)
    ax.grid()
    plt.title(r'Battery history usage')
    plt.xlabel('Estimated hours')
    plt.ylabel('Battery percentage used')
    plt.show()


# pmset -g log|grep -e " Sleep  " -e " Wake  " -e "Using AC" -e "Using Batt"

if __name__ == '__main__':
    events = get_battery_change_events()
    discharge_periods, matrix = get_data_matrix(events)
    plot_data(discharge_periods, matrix)
