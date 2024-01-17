import pandas as pd             
import os
import numpy
import utility


def get_data_file_path():
    '''Lấy đường dẫn tới file data excel'''
    return os.path.abspath(os.getcwd()) + "\\data.xlsx"

def read_sheet(sheetName):
    '''Đọc sheet sheetName trong file data'''
    return pd.read_excel(get_data_file_path(), sheet_name=sheetName)

def read_additional_data(data_file_path):
    sheet = pd.read_excel(data_file_path, sheet_name="ADDITIONAL")
    begin_year          = sheet.loc[0]["VALUE"]
    total_year          = sheet.loc[1]["VALUE"]
    begin_day_timestamp = sheet.loc[2]["VALUE"]
    begin_day           = utility.timestamp_to_day_int(begin_day_timestamp)
    m_cost              = sheet.loc[3]["VALUE"]
    c_cost              = sheet.loc[4]["VALUE"]
    max_c_check         = sheet.loc[5]["VALUE"]
    max_a_check         = sheet.loc[6]["VALUE"]
    start_day_interval  = sheet.loc[7]["VALUE"]
    c_elapsed_time      = sheet.loc[8]["VALUE"]
    return begin_year, total_year, begin_day, m_cost, c_cost, max_c_check, max_a_check, start_day_interval, c_elapsed_time


def read_C_days_not_allowed():
    '''Những ngày không được thực hiện C Check'''
    C_days_not_allowed = set()

    sheet = read_sheet("C_PEAK")
    for i in range(len(sheet)):
        day_start = utility.timestamp_to_day_int(sheet.loc[i][1])
        day_end = utility.timestamp_to_day_int(sheet.loc[i][2])
        for day in range(day_start, day_end + 1):
            C_days_not_allowed.add(day)

    return C_days_not_allowed

def read_C_Check_init_value():
    '''Read C-Check initalize value'''
    sheet = read_sheet("C_INITIAL")
    num_of_aircraft = len(sheet)
    data = numpy.empty((num_of_aircraft, 3), dtype = float)
    interval_data = numpy.empty((num_of_aircraft, 3), dtype= float)
    tolerant_init = numpy.empty((num_of_aircraft, 3), dtype= float)
    tolerant_used = numpy.empty((num_of_aircraft, 3), dtype= float)

    for i in range(num_of_aircraft):
        data[i][0] = sheet.loc[i][4] # DY-C
        data[i][1] = sheet.loc[i][5] # FH-C
        data[i][2] = sheet.loc[i][6] # FC-C

        interval_data[i][0] = sheet.loc[i][7] # C-CI_DY
        interval_data[i][1] = sheet.loc[i][8] # C-CI_FH
        interval_data[i][2] = sheet.loc[i][9] # C-CI_FC

        tolerant_init[i][0] = sheet.loc[i][10] # C-TOL-DY
        tolerant_init[i][1] = sheet.loc[i][11] # C-TOL-FH
        tolerant_init[i][2] = sheet.loc[i][12] # C-TOL-FC

        tolerant_used[i][0] = sheet.loc[i][13] # C-TOLU-DY
        tolerant_used[i][1] = sheet.loc[i][14] # C-TOLU-FH
        tolerant_used[i][2] = sheet.loc[i][15] # C-TOLU-FC
    return data, interval_data, tolerant_init, tolerant_used

def read_A_Check_init_value():
    '''Read A-Check initialize value'''
    sheet = read_sheet("A_INITIAL")
    num_of_aircraft = len(sheet)
    init_A_data = numpy.empty((num_of_aircraft, 3), dtype = float)
    interval_data = numpy.empty((num_of_aircraft, 3), dtype= float)
    tolerant_init = numpy.empty((num_of_aircraft, 3), dtype= float)
    tolerant_used = numpy.empty((num_of_aircraft, 3), dtype= float)

    for i in range(num_of_aircraft):
        init_A_data[i][0] = sheet.loc[i][4] # DY-A
        init_A_data[i][1] = sheet.loc[i][5] # FH-A
        init_A_data[i][2] = sheet.loc[i][6] # FC-A

        interval_data[i][0] = sheet.loc[i][7] # A-CI_DY
        interval_data[i][1] = sheet.loc[i][8] # A-CI_FH
        interval_data[i][2] = sheet.loc[i][9] # A-CI_FC

        tolerant_init[i][0] = sheet.loc[i][10] # A-TOL-DY
        tolerant_init[i][1] = sheet.loc[i][11] # A-TOL-FH
        tolerant_init[i][2] = sheet.loc[i][12] # A-TOL-FC

        tolerant_used[i][0] = sheet.loc[i][13] # A-TOLU-DY
        tolerant_used[i][1] = sheet.loc[i][14] # A-TOLU-FH
        tolerant_used[i][2] = sheet.loc[i][15] # A-TOLU-FC
              
    return init_A_data, interval_data, tolerant_init, tolerant_used
