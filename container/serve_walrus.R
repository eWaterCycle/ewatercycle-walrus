library(remotebmi)
## basic example code

source('/r-scripts/walrus-bmi.r')
model <- WalrusBmi$new()

remotebmi::serve(model)
