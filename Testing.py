import timeit
import numpy
import pandas as pd             
import os
import datareader
from environment import Environment
from datetime import date
from datetime import timedelta

path = os.path.abspath(os.getcwd())                 # Lấy đường dẫn tới thư mục hiện tại
data_file_path = path + "\\data.xlsx"

#environment = Environment()
#environment.init_environment()

