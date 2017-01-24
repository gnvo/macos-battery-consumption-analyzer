#!/usr/bin/env python

import os
import re
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil import parser

re_line_splitter = re.compile(r'(\d{4}[-]\d{2}[-]\d{2}\s\d{2}[:]\d{2}[:]\d{2}\s\S+)\s+(wake|sleep|assertions)\s+.*using (batt|ac).*Charge:[ ]*(\d+).*', flags = re.IGNORECASE)


class DischargeEvent(object):
    def __init__(self, start_date_time, start_charge):
        self.start_date_time = start_date_time.replace(tzinfo=None)
        self.start_charge = start_charge
        self.end_date_time = None
        self.end_charge = None
        self.__elapsed_hours = None
        self.__diff_charge = None
        self.__estimated_hours = None
        self.is_complete = False

    def diff_charge(self):
        if self.__diff_charge is None and self.start_charge and self.end_charge:
            self.__diff_charge = self.start_charge - self.end_charge
        return self.__diff_charge

    def elapsed_hours(self):
        if self.__elapsed_hours is None and self.end_date_time and self.start_date_time:
            self.__elapsed_hours = float((self.end_date_time - self.start_date_time).seconds) / 60 / 60
        return self.__elapsed_hours

    def estimated_hours(self):
        if self.__estimated_hours is None and self.elapsed_hours() and self.diff_charge():
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
    if current_discharge_event is None:
        current_discharge_event = DischargeEvent(start_date_time, start_charge)
    return current_discharge_event

def on_ac(current_discharge_event, end_date_time, end_charge):
    if current_discharge_event:
        current_discharge_event.end_date_time = end_date_time.replace(tzinfo=None)
        current_discharge_event.end_charge = end_charge
        if current_discharge_event.diff_charge() > 0: # if no discharge happened, ignore the discharge event
            current_discharge_event.is_complete = True
        else:
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

def add_last_discharge_event_if_still_discharging(discharge_events, current_discharge_event):
    if current_discharge_event and not current_discharge_event.end_date_time:
        charge = int(os.popen("pmset -g batt | grep '%' | sed 's/.*[^0-9]\([0-9]\{1,3\}\)[%].*/\\1/g'").read())
        date_time = datetime.now()
        current_discharge_event = state_functions['wake']['ac'](current_discharge_event, date_time, charge)
        discharge_events.append(current_discharge_event)
    return discharge_events

def get_data_matrix(events):
    discharge_events = list()
    current_discharge_event = None
    for line in events:
        current_discharge_event = process_logevent(line, current_discharge_event)
        if current_discharge_event and current_discharge_event.is_complete:
            discharge_events.append(current_discharge_event)
            current_discharge_event = None
    discharge_events = add_last_discharge_event_if_still_discharging(discharge_events, current_discharge_event)
    matrix = np.asarray(map(lambda de: [de.elapsed_hours(), de.diff_charge(), de.estimated_hours()], discharge_events))
    return discharge_events, matrix

def plot_data(discharge_events, matrix):
    first_date = discharge_events[1].start_date_time.date()
    last_date = discharge_events[-1].start_date_time.date()
    timestamps = np.asarray(map(lambda de: time.mktime(de.start_date_time.timetuple()), discharge_events))
    timestamps_from_cero = np.subtract(timestamps,timestamps.min())
    timestamps_dim = timestamps_from_cero / timestamps_from_cero.max()
    total_elapsed_hours = np.sum(matrix[:,0])
    weights = matrix[:,0]/total_elapsed_hours
    weighted_mean_estimated_hours = np.sum(matrix[:,2] * weights)
    mean_estimated_hours = np.mean(matrix[:,2])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    col = ax.scatter(matrix[:,1], matrix[:,2], s=3000*weights, c=timestamps_dim * 256, cmap=plt.cm.get_cmap('winter'), edgecolors='none', picker=True)
    ax.axhline(y=weighted_mean_estimated_hours, linewidth=2, color = 'm')
    ax.axhline(y=mean_estimated_hours, linewidth=2, color = 'y')
    mesg_means = 'mean (yellow) %.1f hours\nweighted mean (magenta) %.1f hours' % (mean_estimated_hours, weighted_mean_estimated_hours)
    txt = ax.text(.98, .98, mesg_means,
            horizontalalignment='right',
            verticalalignment='top',
            transform=ax.transAxes,
            backgroundcolor='w')
    def onpick(event):
        ind = event.ind[0]
        txt.set_text(mesg_means + '\n\n%s\npercentage discharged: %d%%\ndischarged: %.1f hours\nestimated battery life: %.1f hours' % (discharge_events[ind].start_date_time,np.take(matrix[:,1], ind),np.take(matrix[:,0], ind),np.take(matrix[:,2], ind)))
        plt.draw()
    def onrelease(event):
        txt.set_text(mesg_means)
        plt.draw()
    fig.canvas.mpl_connect('button_release_event', onrelease)
    fig.canvas.mpl_connect('pick_event', onpick)
    cbar = plt.colorbar(mappable=col, ax=ax, ticks=[0, 256])
    cbar.ax.set_yticklabels([first_date, last_date])
    ax.grid()
    plt.title(r'Battery history usage')
    plt.ylabel('Estimated battery life in hours')
    plt.xlabel('Battery percentage used')
    plt.show()

# pmset -g log|grep -e " Sleep  " -e " Wake  " -e "Using AC" -e "Using Batt"

if __name__ == '__main__':
    power_eventlog = call_pmset()
    events = power_eventlog.splitlines()
    discharge_events, matrix = get_data_matrix(events)
    plot_data(discharge_events,  matrix)
