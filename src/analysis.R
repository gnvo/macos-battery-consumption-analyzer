
mydata = read.csv("/Users/pichurri/Documents/development/mac/macos-battery-consumption-analyzer/test_data.csv")
total_elapsed_hours = sum(mydata["elapsed_hours"])
sum((mydata["elapsed_hours"]/total_elapsed_hours) * mydata["estimated_hours"])
plot(mydata["elapsed_hours"], mydata["estimated_hours"])
