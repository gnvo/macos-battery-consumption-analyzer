# MacOS battery consumption analyzer
This is a battery consumption analyzer for MacOS to be run from the console without admin rights. It scans the battery logs from **/var/log/powermanagement** for changes in battery events; finding the periods when the laptop was running on battery. It then builds a plot of the all these periods with matplotlib.

## Requirements
* Python 3
* numpy
* matplotlib

## Current state
![alt tag](https://raw.githubusercontent.com/gnvo/macos-battery-consumption-analyzer/master/docs/images/0.1%20screenshot.png)
