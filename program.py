import pandas as pd             
import os
import datareader
from environment import Environment
from time import perf_counter
import numpy

#==================== ENVIRONMENT SETUP ================#
t0 = perf_counter()
environment = Environment()
environment.init_environment()
t1 = perf_counter()
print("Environment init.....", round((t1 - t0) * 1000, 0), "ms")
#==================== COMPUTING ================#
t2 = perf_counter()
for loop in range(3):
    print("################################")
    for i in range(45):
        a_t = [i, 1]
        environment.respone(a_t, False)
t3 = perf_counter()
print("Environment respones C checks in.....", round((t3 - t2) * 1000, 0), "ms")
# a_t = [3, 1]
# environment.respone(a_t, True)
# t4 = perf_counter()
# print("Environment respone in.....", round((t4 - t3) * 1000, 0), "ms")
t2 = perf_counter()
for loop in range(25):
    print("################################")
    for i in range(45):
        a_t = [i, 0]
        environment.respone(a_t, False)
t3 = perf_counter()
print("Environment respones A checks in.....", round((t3 - t2) * 1000, 0), "ms")
#print(environment.prev_C_checks)
#environment.read_data_from_file(data_file_path)
#print(environment.m)
#print(datareader.day_int_to_timestamp(environment.T))
