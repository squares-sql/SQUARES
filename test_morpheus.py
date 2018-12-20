import rpy2.robjects as robjects

##### Input-output constraint
benchmark1_input = robjects.r('''
    dat <- read.table(text="
    round var1 var2 nam        val
    round1   22   33 foo 0.16912201
    round2   11   44 foo 0.18570826
    round1   22   33 bar 0.12410581
    round2   11   44 bar 0.03258235
    ", header=T)
    dat
   ''')

benchmark1_output = robjects.r('''
    dat2 <- read.table(text="
    nam val_round1 val_round2 var1_round1 var1_round2 var2_round1 var2_round2
    bar  0.1241058 0.03258235          22          11          33          44
    foo  0.1691220 0.18570826          22          11          33          44
    ", header=T)
    dat2
   ''')

### Program that we want to synthesize
actual_output = robjects.r('''
    library(dplyr)
    library(tidyr)
    TBL_3=gather(dat,MORPH2,MORPH1, c(2,3,5))
    TBL_1=unite(TBL_3,MORPH159, 3, 1)
    morpheus=spread(TBL_1, 1, 3)
    morpheus
   ''')

print("Input table:\n", benchmark1_input)
print("Expected output table:\n", benchmark1_output)
print("Actual output:\n", actual_output)
