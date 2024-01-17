import datareader
import numpy
import math
from time import perf_counter
import utility
class Environment:
    def __init__(self, m=None, M=None, DY=None, FH=None, FC=None, sigmaDY=None, sigmaFH=None, 
                 sigmaFC=None, D=None, u=None, y=None, z=None, g=None, G=None, L=None, delta=None,
                 H=None):
        self.m = m
        self.M = M
        self.DY = DY
        self.FH = FH
        self.FC = FC
        self.D = D
        self.u = u
        self.y = y
        self.z = z
        self.g = g
        self.G = G
        self.L = L
        self.delta = delta
        self.H = H
        
        # Add data
        # self.hangars_C = 3
        # self.hangars_A = 1
        self.hangars_number = 4
        self.check_types = 2
        # C check == 0, A check == 1
        self.aircrafts_number = 45

    #################### INITIAL SETUP ####################
    # Biến tùy chỉnh của môi trường
    def read_additional_data_from_file(self, data_file_path):
        self.data_file_path = data_file_path
        self.begin_year, self.total_year, self.t0, self.m_cost, self.c_cost, self.max_c_check, self.max_a_check, \
        self.start_day_interval, self.c_elapsed_time = datareader.read_additional_data(data_file_path)

    # Đặt kích thước các biến ban đầu của môi trường 
    def create_data_format(self):
        # Is a type k check can be performed in hangar h on day t
        self.m = numpy.empty((self.hangars_number, self.T), dtype=int)

        # Is enough hangar availability for type k checks on a specific day t
        self.M = numpy.empty((self.check_types, self.T), dtype=int)    

        self.H = numpy.empty((self.aircrafts_number, self.check_types, self.T), dtype=int)
        # h = hangar m có xếp lịch bảo dưỡng C vào ngày T không
        self.h = numpy.empty((self.hangars_number, self.T), dtype=int)
        self.h.fill(1)  
        self.prev_C_checks = []
        for i in range(self.aircrafts_number):
            self.prev_C_checks.append([])
        # Cumulative usages on each aircrafts for each day
        self.DY = numpy.empty((self.aircrafts_number, self.check_types, self.T), dtype=float)
        self.FH = numpy.empty((self.aircrafts_number, self.check_types, self.T), dtype=float)
        self.FC = numpy.empty((self.aircrafts_number, self.check_types, self.T), dtype=float)
        # Interval 
        self.I_DY = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.I_FH = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.I_FC = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)

        # Max tolerance
        self.TOL_DY = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.TOL_FH = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.TOL_FC = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        
        # Tolerance used last type
        self.TOLU_DY = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.TOLU_FH = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)
        self.TOLU_FC = numpy.empty((self.aircrafts_number, self.check_types), dtype=float)

        # Due date
        self.D = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)  
        self.u = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)

        # Ngayf cuối cùng thực hiện check trước đấy
        self.y = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)
        self.y.fill(self.t0 - 1)
        self.z = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)

        self.g = numpy.empty((self.aircrafts_number, self.check_types, self.T), dtype=bool)     # Grounded aircraft?
        self.G = numpy.empty((self.check_types, self.T), dtype=bool)     # Type k check starting

        # A check == 1 days
        # C check == 15 days
        self.L = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)
        
        self.avgFH = 10.5
        self.avgFC = 4.7
        self.delta = numpy.empty((self.aircrafts_number), dtype=float)

    #################### COMPUTE INITIAL VALUES ####################
    def compute_init_m(self):
        self.m.fill(1)       # m: [hangars][T_day]
        self.M.fill(1)       # M: [Checktypes][T_day]

        C_days_not_allowed = datareader.read_C_days_not_allowed()
        C_Check = 1 # C Check
        for day in C_days_not_allowed :
            if(self.t0 <= day <= self.T):
                self.M[C_Check][day] = 0
                for i in range(self.hangars_number):
                    self.h[i][day] = 0

    ##### Compute H, L and G #####           
    def compute_init_HLG(self):

        for aircraft in range(self.aircrafts_number):
            self.L[aircraft][0] = 1    # A check
            self.L[aircraft][1] = 15   # C check

        self.H.fill(1)
                        
        # Compute G
        self.G.fill(True)
        self.g.fill(False)

        self.update_HG(self.t0, self.T)

    def update_HG(self, start_date, end_date):
        A_check = 0
        C_check = 1
        C_check_duration = 15 # HARDCODE
        if(start_date != self.t0):
            start_date = max(start_date - C_check_duration, self.t0)
            end_date = min(end_date + C_check_duration, self.T) + 1

        # A-check
        for day in range(start_date, end_date):
            total_hangar_free = 0
            for hangar in range(self.hangars_number):
                if self.m[hangar][day] == 1:
                    total_hangar_free += 1

            if(total_hangar_free == 0):
                for i in range(self.aircrafts_number):
                    self.H[i][A_check][day] = 0
            else:
                for i in range(self.aircrafts_number):
                    self.H[i][A_check][day] = 1

        
        for hangar in range(self.hangars_number):
            for day in range(start_date, end_date):
                if self.m[hangar][day] == 0:
                    leftIndent = max(self.t0, day - C_check_duration)
                    for day_cant_schedule in range(leftIndent, day+1):
                        self.h[hangar][day_cant_schedule] = 0

        for day in range(start_date, end_date):
            count = 0
            for hangar in range(self.hangars_number):
                if self.h[hangar][day] == 1:
                    count += 1
                    break
                    
            if count == 0:
                for i in range(self.aircrafts_number):
                    self.H[i][C_check][day] = 0
        pass

    ##### Compute DY, FH, FC #####
    def compute_init_DY_FH_FC(self):
        # Init value from data file
        A_check_init_data, A_interval_init, A_tol, A_tol_used = datareader.read_A_Check_init_value()
        check_type = 0 # A - check
        for i in range(len(A_check_init_data)):
            self.DY[i][check_type][0] = A_check_init_data[i][0]
            self.FH[i][check_type][0] = A_check_init_data[i][1]
            self.FC[i][check_type][0] = A_check_init_data[i][2]
            
            self.I_DY[i][check_type] = A_interval_init[i][0]
            self.I_FH[i][check_type] = A_interval_init[i][1]
            self.I_FC[i][check_type] = A_interval_init[i][2]

            self.TOL_DY[i][check_type] = A_tol[i][0]
            self.TOL_FH[i][check_type] = A_tol[i][1]
            self.TOL_FC[i][check_type] = A_tol[i][2]

            self.TOLU_DY[i][check_type] = A_tol_used[i][0]
            self.TOLU_FH[i][check_type] = A_tol_used[i][1]
            self.TOLU_FC[i][check_type] = A_tol_used[i][2]
        
        C_check_init_data, C_interval, C_tol, C_tol_used = datareader.read_C_Check_init_value()
        check_type = 1 # C - check
        for i in range(len(C_check_init_data)):
            self.DY[i][check_type][0] = C_check_init_data[i][0]
            self.FH[i][check_type][0] = C_check_init_data[i][1]
            self.FC[i][check_type][0] = C_check_init_data[i][2]

            self.I_DY[i][check_type] = C_interval[i][0]
            self.I_FH[i][check_type] = C_interval[i][1]
            self.I_FC[i][check_type] = C_interval[i][2]

            self.TOL_DY[i][check_type] = C_tol[i][0]
            self.TOL_FH[i][check_type] = C_tol[i][1]
            self.TOL_FC[i][check_type] = C_tol[i][2]

            self.TOLU_DY[i][check_type] = C_tol_used[i][0]
            self.TOLU_FH[i][check_type] = C_tol_used[i][1]
            self.TOLU_FC[i][check_type] = C_tol_used[i][2]

        #print(self.DY)
        # Compute intire array
        for aircraft in range(self.aircrafts_number):
            for check in range(2):
                for t in range(self.t0 + 1, self.T):
                    self.DY[aircraft][check][t] = self.DY[aircraft][check][t - 1] + 1
                    self.FH[aircraft][check][t] = self.avgFH + self.FH[aircraft][check][t - 1]
                    self.FC[aircraft][check][t] = self.avgFC + self.FC[aircraft][check][t - 1]

    def compute_init_Di(self):
        '''Tính toán ngày tới hạn bảo dưỡng'''
        # d_DY loop == Due date using date
        self.d_DY = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)
        for aircraft in range(self.aircrafts_number):
            for check in range(self.check_types):
                for day in range(self.t0, self.T):
                    if(self.DY[aircraft][check][day] >= self.I_DY[aircraft][check]):
                        self.d_DY[aircraft][check] = day
                        break

        # d_FH loop  == Ngày tới hạn sử dụng số giờ bay
        self.d_FH = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)             
        for aircraft in range(self.aircrafts_number):
            for check in range(self.check_types):
                for day in range(self.t0, self.T):
                    if(self.FH[aircraft][check][day] >= self.I_FH[aircraft][check]):
                        self.d_FH[aircraft][check] = day
                        break
        
        # d_FC loop == Ngày tới hạn sử dụng số lần cất hạ
        self.d_FC = numpy.empty((self.aircrafts_number, self.check_types), dtype=int)
        for aircraft in range(self.aircrafts_number):
            for check in range(self.check_types):
                for day in range(self.t0, self.T):
                    if(self.FC[aircraft][check][day] >= self.I_FC[aircraft][check]):
                        self.d_FC[aircraft][check] = day
                        break

        for aircraft in range(self.aircrafts_number):
            for check_types in range(self.check_types):
                self.D[aircraft][check_types] = min(self.d_DY[aircraft][check_types], 
                                                    self.d_FC[aircraft][check_types], 
                                                    self.d_FH[aircraft][check_types])

    def compute_init_value(self):
        # Compute m value from C_not_allowed, public_holidays, A_not_allowed
        self.compute_init_m()
        self.compute_init_HLG()
        self.compute_init_DY_FH_FC()
        self.compute_init_Di()       

    def init_environment(self):
        '''Khởi tạo giá trị ban đầu cho môi trường'''
        self.read_additional_data_from_file(datareader.get_data_file_path())
        self.T = self.t0 + self.total_year * 365

        self.create_data_format()

        self.compute_init_value()

    #################### COMPUTE RESPOND FROM AGENT ####################
    
    def print_log1(self, aircraft, check_type, hangar_chosen, day_mtc_start, day_mtc_end, lost_FH, lost_DY):
        print("A/C", aircraft + 1, "check", check_type, "day", day_mtc_start, "hangar", hangar_chosen, "FH Lost:", round(lost_FH, 2), "DY Lost:", lost_DY)
        pass

    # Calc repair date
    def calc_repair_date(self, aircraft: int, check_type: int):
        '''Tìm ngày đặt lịch sửa chữa cho máy bay'''
        day_aog_start = -1  # Ngày quá hạn tolerant, máy bay không được bay
        day_aog_end = -1    # Ngày trước khi đưa vào hangar
        setdate = -1
        is_merged = False
        hangar_chosen = -1
        D_aircraft = self.D[aircraft][check_type] 

        # Check for possible merge A using due date
        
        if(check_type == 0): # A check
            for days in self.prev_C_checks[aircraft]:
                different_days = D_aircraft - days[1]
                if(0 <= different_days <= 14):
                    is_merged = True
                    setdate = days[0]    # Start maintance day
                    return setdate, day_aog_start, day_aog_end, is_merged, days[2]

        # Tìm ngày đặt lịch không sử dụng Tolerance
        for day in reversed(range(self.y[aircraft][check_type] + 1, D_aircraft + 1)):
            #print("Checking day", day)
            if self.H[aircraft][check_type][day] and self.G[check_type][day]:
                #print("Aircraft: ", aircraft, "checktype: ", check_type, "schedule day: ", day, "-", datareader.day_int_to_timestamp(day))
                setdate = day
                break

        if(setdate != -1 and check_type == 0):
            for days in self.prev_C_checks[aircraft]:
                different_days = setdate - days[1]
                if(0 <= different_days <= 30):
                    is_merged = True
                    setdate = days[0]    # Start maintance day
                    return setdate, day_aog_start, day_aog_end, is_merged, days[2]

        # Phải sử dụng Tolerance của máy bay
        tolerant_limit = 0
        if setdate == -1:
            tolerant_DY = self.TOL_DY[aircraft][check_type] - self.TOLU_DY[aircraft][check_type]
            tolerant_FH = math.floor((self.TOL_FH[aircraft][check_type] - self.TOLU_FH[aircraft][check_type]) / self.avgFH)
            tolerant_FC = math.floor((self.TOL_FC[aircraft][check_type] - self.TOLU_FC[aircraft][check_type]) / self.avgFC)
            tolerant_limit = min(tolerant_DY, tolerant_FC, tolerant_FH)
            for day in range(D_aircraft + 1, D_aircraft + tolerant_limit + 1):
                if self.H[aircraft][check_type][day] and self.G[check_type][day]:
                    print("Aircraft: ", aircraft, "checktype: ", check_type, "schedule day: ", day, "-", utility.day_int_to_timestamp(day))
                    setdate = day
                    break
        
        # Máy bay phải nằm đất tới khi có ngày có thể thực hiện bảo dưỡng
        if setdate == -1:
            for day in range(D_aircraft+ tolerant_limit + 1, self.T):
                if self.H[aircraft][check_type][day] and self.G[check_type][day]:
                    print("Aircraft: ", aircraft, "checktype: ", check_type, "schedule day: ", day, "-", utility.day_int_to_timestamp(day))
                    setdate = day
                    day_aog_start = D_aircraft + tolerant_limit + 1 
                    day_aog_end = day - 1   
                    break

        if setdate == -1:
            # Không thể tìm được ngày kể cả nằm đất tới ngày cuối cùng
            print("Cant find date until last day")

        return setdate, day_aog_start, day_aog_end, is_merged, hangar_chosen

    def calc_hangar_chose(self, check_type: int, day: int):
        '''Tìm hangar để lên lịch vào ngày day'''

        C_check = 1
        if check_type == C_check:
            for hangar in range(self.hangars_number):
                if self.h[hangar][day] == 1:
                    return hangar
                
            ## CANT FIND HANGAR, SOMETHING WRONG
            print("DEAD END HANGAR")
            return -1

        # A check
        for hangar in range(self.hangars_number):
            if(self.h[hangar][day] == 0 and self.m[hangar][day]):    # Ưu tiên chọn ngày không thể thực hiện C check
                return hangar
        
        for hangar in range(self.hangars_number):
            if(self.m[hangar][day]):
                return hangar

    def fronze_AoG(self, aircraft : int, check_type: int, day_start:int, day_end:int, is_other_checktype: bool):
        '''Tính toán lại thông số do máy bay nằm đất'''
        # DY, FC, FH giống với ngày trước khi nằm đất
        for day in range(day_start, day_end + 1):   
            self.DY[aircraft][check_type][day] = self.DY[aircraft][check_type][day_start - 1]   
            self.FC[aircraft][check_type][day] = self.FC[aircraft][check_type][day_start - 1]
            self.FH[aircraft][check_type][day] = self.FH[aircraft][check_type][day_start - 1]

        # DY, FC, FH sau AoG cộng dồn tương ứng với trung bình từng ngày
        for day in range(day_end + 1, self.T):
            self.DY[aircraft][check_type][day] = self.DY[aircraft][check_type][day - 1] + 1
            self.FC[aircraft][check_type][day] = self.FC[aircraft][check_type][day - 1] + self.avgFC
            self.FH[aircraft][check_type][day] = self.FH[aircraft][check_type][day - 1] + self.avgFH

        # Update lại due date của checktype không thực hiện bảo dưỡng
        # Nếu thực hiện C check -> tính lại due date cho A-check
        # Số ngày cộng thêm tương ứng số ngày AoG
        AoG_days = day_end - day_start + 1
        if(is_other_checktype):
            self.d_DY[aircraft][check_type] += AoG_days
            self.d_FC[aircraft][check_type] += AoG_days
            self.d_FH[aircraft][check_type] += AoG_days
            
        pass

    def update_environment(self, aircraft: int, check_type: int, day_mtc_start: int, hangar_chosen: int, day_aog_start, day_aog_end,
                           log_performance: bool, is_merged: bool):
        '''Update dữ liệu môi trường dựa trên máy bay đã xếp lịch'''
        
        
        duration = self.L[aircraft][check_type]
        if(check_type == 0 and is_merged):
            print("MERGED")
            duration = 15
        day_mtc_end = day_mtc_start + duration - 1
        day_new_interval = day_mtc_end + 1
        
        if(check_type == 1):
            other_check_type = 0 
            if(day_aog_start > -1):
                self.prev_C_checks[aircraft].append([day_aog_start, day_mtc_end, hangar_chosen])
            else:
                self.prev_C_checks[aircraft].append((day_mtc_start, day_mtc_end, hangar_chosen))
        else:
            other_check_type = 1

        # Aircraft on ground - thông số của máy bay không đổi
        # Ví dụ ở checktype == 1 (C-check)
        if(not is_merged):
            if(day_aog_start > -1): # Máy bay phải nằm đất do quá tolerant
                self.fronze_AoG(aircraft, check_type, day_aog_start, day_aog_end, False)       # C-Check không đổi trong những ngày nằm đất
                self.fronze_AoG(aircraft, other_check_type, day_aog_start, day_mtc_end, True) # A-Check k0 đổi từ ngày nằm đất tới khi kết thúc bảo dưỡng
            else:
                self.fronze_AoG(aircraft, other_check_type, day_mtc_start, day_mtc_end, True) # A-Check k đổi từ ngày bảo dưỡng bắt đầu tới kết thúc
            
        for day in range(day_mtc_start, day_mtc_end + 1): 
            self.m[hangar_chosen][day] = 0
            self.g[aircraft][check_type][day] = 1

        if log_performance:
            t0 = perf_counter()
        self.update_HG(day_mtc_start, day_mtc_end)

        if log_performance:
            t1 = perf_counter()
            print("Env update - update_HG():", round((t1 - t0) * 1000, 0), "ms")
        ### Update tolerant
        # LOST
        lost_DY = self.I_DY[aircraft][check_type] - self.DY[aircraft][check_type][day_mtc_start - 1]
        lost_FH = self.I_FH[aircraft][check_type] - self.FH[aircraft][check_type][day_mtc_start - 1]
        lost_FC = self.I_FC[aircraft][check_type] - self.FC[aircraft][check_type][day_mtc_start - 1]
        # print("Lost DY", lost_DY, "lost_FH", lost_FH, "lost_FC", lost_FC)
        
        if(lost_DY < 0):
            self.TOLU_DY[aircraft][check_type] -= lost_DY # lost_DY < 0
        if(lost_FH < 0):
            self.TOLU_FH[aircraft][check_type] -= lost_FH
        if(lost_FC < 0):
            self.TOLU_FC[aircraft][check_type] -= lost_FC

        ### Update DY, FH, FC
        # Cho checktype hiện tại
        for day in range(day_new_interval, self.T):
            self.DY[aircraft][check_type][day] -= self.DY[aircraft][check_type][day_mtc_end]
            self.FC[aircraft][check_type][day] -= self.FC[aircraft][check_type][day_mtc_end]
            self.FH[aircraft][check_type][day] -= self.FH[aircraft][check_type][day_mtc_end]
        
        for day in range(day_mtc_start, day_mtc_end + 1):
            self.DY[aircraft][check_type][day] = 0
            self.FC[aircraft][check_type][day] = 0
            self.FH[aircraft][check_type][day] = 0
            
        if log_performance:
            t2 = perf_counter()
            print("Env update - update DY, FC, FH:", round((t2 - t1) * 1000, 0), "ms")
        ### Update due date d
        for day in range(day_new_interval, self.T):
            if(self.DY[aircraft][check_type][day] >= self.I_DY[aircraft][check_type]):
                self.d_DY[aircraft][check_type] = day
                break

        # d_FH loop  == Ngày tới hạn sử dụng số giờ bay          
        for day in range(day_new_interval, self.T):
            if(self.FH[aircraft][check_type][day] >= self.I_FH[aircraft][check_type]):
                self.d_FH[aircraft][check_type] = day
                break
        
        # d_FC loop == Ngày tới hạn sử dụng số lần cất hạ
        for day in range(day_new_interval, self.T):
            if(self.FC[aircraft][check_type][day] >= self.I_FC[aircraft][check_type]):
                self.d_FC[aircraft][check_type] = day
                break

        self.D[aircraft][check_type] = min(self.d_DY[aircraft][check_type], 
                                           self.d_FC[aircraft][check_type], 
                                           self.d_FH[aircraft][check_type])

        ### Update y
        self.y[aircraft, check_type] = day_mtc_end
        ### Update G
        if(check_type == 1):
            min_day = max(self.t0, day_mtc_start - 3)
            max_day = min(self.T, day_mtc_start + 3)
            for day in range(min_day, max_day + 1):
                self.G[check_type][day] = 0
            pass

        self.print_log1(aircraft, check_type, hangar_chosen, day_mtc_start, day_mtc_end, lost_FH, lost_DY)


    def respone(self, value_from_agent, log_performance = False):
        '''Phản hồi tới agent'''
        aircraft = value_from_agent[0]
        check_type = value_from_agent[1]
        if log_performance:
            t0 = perf_counter()
            
        set_date, day_aog_start, day_aog_end, is_merged, hangar_chosen = self.calc_repair_date(aircraft, check_type)
        if set_date == -1: # Không tìm được ngày
            return
        if log_performance:
            t1 = perf_counter()
            utility.performance_log("Calc repair date time", t0, t1)

        if(hangar_chosen == -1):
            hangar_chosen= self.calc_hangar_chose(check_type, set_date)
       
        if log_performance:
            t2 = perf_counter()
            utility.performance_log("Calc hangar time", t1, t2)

        if(hangar_chosen == -1):
            print("ERROR: CANT FIND A HANGAR IN DAY", set_date, "SOMETHING WRONG!")
            
        self.update_environment(aircraft, check_type, set_date, hangar_chosen, day_aog_start, day_aog_end, log_performance, is_merged)
        if log_performance:
            t3 = perf_counter()
            utility.performance_log("Update env time:", t2, t3)
        
