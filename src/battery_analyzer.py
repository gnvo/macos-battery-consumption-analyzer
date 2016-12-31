#!/usr/bin/env python

import os
import multiprocessing
import re
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser

re_line_splitter = re.compile(r'(\d{4}[-]\d{2}[-]\d{2}\s\d{2}[:]\d{2}[:]\d{2}\s\S+)\s+(wake|sleep|assertions)\s+.*using (batt|ac).*Charge:[ ]*(\d+).*', flags = re.IGNORECASE)

class DischargeEvent(object):
    def __init__(self, start_date_time, start_charge):
        self.start_date_time = start_date_time
        self.start_charge = start_charge
        self.end_date_time = None
        self.end_charge = None
        self.__elapsed_hours = None
        self.__diff_charge = None
        self.__estimated_hours = None
    def diff_charge(self):
        if self.__diff_charge == None and self.start_charge and self.end_charge:
            self.__diff_charge = self.start_charge - self.end_charge
        return self.__diff_charge
    def elapsed_hours(self):
        if self.__elapsed_hours == None and self.end_date_time and self.start_date_time:
            self.__elapsed_hours = float((self.end_date_time - self.start_date_time).seconds) / 60 / 60
        return self.__elapsed_hours
    def estimated_hours(self):
        if self.__estimated_hours == None and self.elapsed_hours() and self.diff_charge():
            self.__estimated_hours = 100 * (self.elapsed_hours() / self.diff_charge())
        return self.__estimated_hours
    def __str__(self):
        return "start_date_time: " + str(self.start_date_time) + "\n" + \
               "start_charge: " + str(self.start_charge) + "\n" + \
               "end_date_time: " + str(self.end_date_time) + "\n" + \
               "end_charge: " + str(self.end_charge) + "\n" + \
               "elapsed_hours: " + str(self.elapsed_hours()) + "\n" + \
               "diff_charge: " + str(self.diff_charge()) + "\n" + \
               "estimated_hours: " + str(self.estimated_hours())
        # return start.__str__() + "\n" + end.__str__() + "\nElapsed time: %s, estimate hours: %f" % (discharge_period.elapsed_time(), discharge_period.estimated_hours())
        # return "%f,%d,%f,%f" % (self.start_timestamp_as_utc(),self.diff_charge(), self.elapsed_hours(), self.estimated_hours())

def call_pmset():
    return os.popen("pmset -g log").read()

def on_battery(current_discharge_event, start_date_time, start_charge):
    if current_discharge_event == None:
        current_discharge_event = DischargeEvent(start_date_time, start_charge)
    return current_discharge_event

def on_ac(current_discharge_event, end_date_time, end_charge):
    if current_discharge_event:
        current_discharge_event.end_date_time = end_date_time
        current_discharge_event.end_charge = end_charge
        if current_discharge_event.diff_charge() <= 0: # if no discharge happened, ignore the discharge event
            current_discharge_event = None
    return current_discharge_event

state_functions = {'wake':      {'batt': on_battery, 'ac': on_ac},
                   'sleep':     {'batt': on_ac,      'ac': on_ac},
                   'assertions':{'batt': on_battery, 'ac': on_ac}}

def process_logevent(line, current_discharge_event):
    m = re_line_splitter.match(line)
    if m:
        event_group = m.group(2).lower()
        description_group = m.group(3).lower()
        date_time = parser.parse(m.group(1))
        charge = int(m.group(4))
        current_discharge_event = state_functions[event_group][description_group](current_discharge_event, date_time, charge)
    return current_discharge_event

def get_data_matrix(events):
    discharge_events = list()
    current_discharge_event = None
    for line in events:
        current_discharge_event = process_logevent(line, current_discharge_event)
        if current_discharge_event and current_discharge_event.end_date_time:
            discharge_events.append(current_discharge_event)
            current_discharge_event = None
    matrix = np.asarray(map(lambda de: [de.elapsed_hours(), de.diff_charge(), de.estimated_hours()], discharge_events))
    return discharge_events, matrix

def plot_data(discharge_events, matrix):
    datetimes = map(lambda de: de.start_date_time, discharge_events)#Still not sure why this is necessary
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
        ind = event.ind[0]
        print ('On %s, %d%% battery discharged over: %f hours, at the same rate the full charge would have lasted: %f\n' % (discharge_events[ind].start_date_time,np.take(matrix[:,1], ind),np.take(matrix[:,0], ind),np.take(matrix[:,2], ind)))
    fig.canvas.mpl_connect('pick_event', onpick)
    ax.grid()
    plt.title(r'Battery history usage')
    plt.xlabel('Estimated hours')
    plt.ylabel('Battery percentage used')
    plt.show()

# pmset -g log|grep -e " Sleep  " -e " Wake  " -e "Using AC" -e "Using Batt"

if __name__ == '__main__':
    power_eventlog = call_pmset()
    events = power_eventlog.splitlines()
    discharge_events, matrix = get_data_matrix(events)
    plot_data(discharge_events,  matrix)
