# -*- coding: utf-8 -*-
from time import sleep
from winsound import Beep
import serial
import threading
from threading import Timer
from time import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pygame.midi

import scipy.signal as spsig
from scipy.fftpack import fft, fftfreq
from scipy import hamming

#---settings---#
Myo_Frames1 = [] #Myoelectronical signal colums
Myo_Frames2 = [] #Myoelectronical signal colums
Midi_Frames = [] #Midi colums [[time_stamp, velocity],[time_stamp, velocity],...,[time_stamp, velocity]]

record_flag = 0 #0:none 1:wait 2:do

#score setup
score = 0 #max = 30, in case of miss:-2 in case of hit:+1
up_limit = 90 #upper limit
bo_limit = 70 #bottom limit

#fft by hamming window
def do_fft(sig):
    win = hamming(sig.size)
    sig_spectrum = fft(sig * win)
    return abs(sig_spectrum[: sig.size / 2 + 1])

#plot update. mm_list is myo mean value, m_list is midi's velocity.
def Data_Plot(data):
    plt.rcParams["font.size"] = 24

    #midi's velocity plot
    #plt.subplot(1, 2, 1)
    plt.cla()
    plt.title("MIDI")
    plt.ylim((0,129)) #velocity is defined number of 0 to 127.

    m_list_size = len(Midi_Frames) #midi list
    if m_list_size > 10:
        m_list_size = 10

    m_x = np.zeros(1)
    m_y = np.zeros(1)

    x_min = 0
    x_max = 1

    for j, row in enumerate(Midi_Frames[-(m_list_size)-1:]):
        if j == 0:
            m_x[0] = row[0]
            x_min = row[0]
            m_y[0] = row[1]
        else:
            m_x = np.append(m_x, row[0])
            x_max = row[0]
            m_y = np.append(m_y, row[1])
    plt.hlines(y=[bo_limit, up_limit], xmin = x_min, xmax = x_max, colors = 'r', linestyles = 'dashed', linewidths = 2) #present upper limit & bottom limit
    m_im = plt.plot(m_x, m_y)

    """#point plot
    plt.subplot(1, 2, 2)
    plt.cla()
    plt.title("point")
    plt.ylim((-3, 33))
    #plt.figure(figsize=(1, 4)) #縦横比変更，default is 8:6
    s_im = plt.bar(0, score)
    """

#define thread class
class control_th():
    def __init__(self):
        self.stop_event = threading.Event() #停止させるかのフラグ

        #スレッドの作成と開始
        #self.thread_click = threading.Thread(target = self.click_get)
        self.thread_Myo = threading.Thread(target = self.Myo_get)
        self.thread_Sample = threading.Thread(target = self.Data_Sample)

        #self.thread_click.start()
        self.thread_Myo.start()
        self.thread_Sample.start()

    def Myo_get(self):
        size_count = 0

        ser1 = serial.Serial("COM3",57600) #デバイス名とボーレート（arduino側も同じ数値に要設定）

        while not self.stop_event.is_set():
            indent = ord(ser1.read())
            data1_1 = ord(ser1.read())
            data1_2 = ord(ser1.read())
            data2_1 = ord(ser1.read())
            data2_2 = ord(ser1.read())

            t_data1 = ord(ser1.read())
            t_data2 = ord(ser1.read())

            data1_3 = (data1_1 << 8) + data1_2
            data2_3 = (data2_1 << 8) + data2_2

            t_data3 = (t_data1 << 8) + t_data2

            if (record_flag == 2) and (len(Midi_Frames) > 0):
                Myo_Frames1.append([indent, t_data3, data1_3])
                Myo_Frames2.append([indent, t_data3, data2_3])

                """#resampling ex
                if dx1_1 == 0:
                    MyoRe_frames1.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                    dx1_1 = interval
                elif dx1_1 + interval > Myo_Frames1[len(Myo_Frames1)-1][1]:
                    dx1_2 = Myo_Frames1[len(Myo_Frames1)-1][1] - dx1_1
                    try:
                        MyoRe_frames1.append( Myo_Frames1[len(Myo_Frames1)-2][2] + (((Myo_Frames1[len(Myo_Frames1)-1][2] - Myo_Frames1[len(Myo_Frames1)-2][2])) * ((float)(dx1_1)/(dx1_1 + dx1_2))) )
                    except:
                        if dx1_1 <= dx1_2:
                            MyoRe_frames1.append(Myo_Frames1[len(Myo_Frames1)-2][2])
                        else:
                            MyoRe_frames1.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                    dx1_1 = interval - dx1_2
                elif dx1_1 + interval < Myo_Frames1[len(Myo_Frames1)-1][1]:
                    num = ((Myo_Frames1[len(Myo_Frames1)-1][1] - dx1_1) / interval) + 1
                    dx1_1_2 = dx1_1
                    dx1_2_2 = dx1_2

                    for i in range(num):
                        dx1_2 = Myo_Frames1[len(Myo_Frames1)-1][1] - dx1_1
                        try:
                            MyoRe_frames1.append( Myo_Frames1[len(Myo_Frames1)-2][2] + (((Myo_Frames1[len(Myo_Frames1)-1][2] - Myo_Frames1[len(Myo_Frames1)-2][2])) * ((float)(dx1_1)/(dx1_1 + dx1_2))) )
                        except:
                            if dx1_1 <= dx1_2:
                                MyoRe_frames1.append(Myo_Frames1[len(Myo_Frames1)-2][2])
                            else:
                                MyoRe_frames1.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                        dx1_1 = (interval * (i + 1)) + dx1_1_2

                    dx1_1 = interval - dx1_2

                #resampling fl
                if dx2_1 == 0:
                    MyoRe_frames2.append(Myo_Frames2[len(Myo_Frames2)-1][2])
                    dx2_1 = interval
                elif dx2_1 + interval > Myo_Frames2[len(Myo_Frames2)-1][1]:
                    dx2_2 = Myo_Frames2[len(Myo_Frames2)-1][1] - dx2_1
                    try:
                        MyoRe_frames2.append( Myo_Frames2[len(Myo_Frames2)-2][2] + (((Myo_Frames2[len(Myo_Frames2)-1][2] - Myo_Frames2[len(Myo_Frames2)-2][2])) * ((float)(dx2_1)/(dx2_1 + dx2_2))) )
                    except:
                        if dx2_1 <= dx2_2:
                            MyoRe_frames2.append(Myo_Frames2[len(Myo_Frames2)-2][2])
                        else:
                            MyoRe_frames2.append(Myo_Frames2[len(Myo_Frames2)-1][2])
                    dx2_1 = interval - dx2_2
                elif dx2_1 + interval < Myo_Frames2[len(Myo_Frames2)-1][1]:
                    num = ((Myo_Frames2[len(Myo_Frames2)-1][1] - dx2_1) / interval) + 1
                    dx2_1_2 = dx2_1
                    dx2_2_2 = dx2_2

                    for i in range(num):
                        dx2_2 = Myo_Frames2[len(Myo_Frames2)-1][1] - dx2_1
                        try:
                            MyoRe_frames2.append( Myo_Frames2[len(Myo_Frames2)-2][2] + (((Myo_Frames2[len(Myo_Frames2)-1][2] - Myo_Frames2[len(Myo_Frames2)-2][2])) * ((float)(dx2_1)/(dx2_1 + dx2_2))) )
                        except:
                            if dx2_1 <= dx2_2:
                                MyoRe_frames2.append(Myo_Frames2[len(Myo_Frames2)-2][2])
                            else:
                                MyoRe_frames2.append(Myo_Frames2[len(Myo_Frames2)-1][2])
                        dx2_1 = (interval * (i + 1)) + dx2_1_2

                    dx2_1 = interval - dx2_2
                """


            wait_size = ser1.in_waiting

            if size_count % 100 == 0:
                #if record_flag is not 2:
                print "data1 = ", data1_3, " data2 = ", data2_3, " time_duration = ", t_data3, " waiting_bytes = ", wait_size
                size_count = 0

            size_count += 1

        ser1.close() #シリアルポートのクローズ
        Beep(1100, 1000) #end beep sound

    #Myomean and MIDI and MdPF sampling
    def Data_Sample(self):
        while record_flag == 0:
            pass

        pygame.midi.init()
        input_id = 2#pygame.midi.get_default_input_id()
        midi_input = pygame.midi.Input(input_id)

        calc_score = 30

        while not self.stop_event.is_set():
            #MIDI
            midi_info = midi_input.read(10) #midi_info[[[x,y,vel], time_stamp],...]
            if len(midi_info) > 0:
                #if (record_flag is not 2) and (len(midi_info) <= 0):
                    #record_flag = 2
                    #print "test"
                for row in midi_info:
                    if row[0][2] > 0:
                        Midi_Frames.append([row[1], row[0][2]])
                        if (row[0][2] > up_limit) or (row[0][2] < bo_limit):
                            calc_score -= 2
                        elif (calc_score > 0) and (calc_score < 30):
                            calc_score += 1
                        else:
                            pass
                    print calc_score
                    if calc_score <= 0:
                        break
                if calc_score <= 0:
                    break

            """#MdPF ex
            if len(MyoRe_frames1) - index_MdPF1 >= 1000:
                #high pass fir
                fe = 20.0 / nyq #[Hz]
                numtaps = 255 #フィルタ係数（タップの数（要奇数））
                co = spsig.firwin(numtaps, fe, pass_zero=False) #setting coefficient
                high_pass_sig = spsig.lfilter(co, 1, MyoRe_frames1[index_MdPF1:len(MyoRe_frames1)-1])

                power_spectrum = do_fft(high_pass_sig)
                freqList = fftfreq(high_pass_sig.size, d = 1.0 / rate)  #周波数の分解能計算

                # --- 表示周波数帯制限 ---
                #low cut
                List_count_low = 0
                for row in freqList:
                    if row > 20: #20Hz以上
                        break
                    List_count_low += 1

                #high cut
                List_count_high = 0
                for row in freqList:
                    if row >= 500: #500Hz以下
                        break
                    List_count_high += 1

                spectrum_sum = np.sum(power_spectrum[List_count_low:List_count_high])

                find_mid = 0
                i = List_count_low

                while find_mid < spectrum_sum / 2:
                    find_mid += power_spectrum[i]
                    i += 1
                mid_f = i - 1

                MdPF_Frames1.append(freqList[mid_f])

                index_MdPF1 = len(MyoRe_frames1)-1

            #MdPF fl
            if len(MyoRe_frames2) - index_MdPF2 >= 1000:
                #high pass fir
                fe = 20.0 / nyq #[Hz]
                numtaps = 255 #フィルタ係数（タップの数（要奇数））
                co = spsig.firwin(numtaps, fe, pass_zero=False) #setting coefficient
                high_pass_sig = spsig.lfilter(co, 1, MyoRe_frames2[index_MdPF2:len(MyoRe_frames2)-1])

                power_spectrum = do_fft(high_pass_sig)
                freqList = fftfreq(high_pass_sig.size, d = 1.0 / rate)  #周波数の分解能計算

                # --- 表示周波数帯制限 ---
                #low cut
                List_count_low = 0
                for row in freqList:
                    if row > 20: #20Hz以上
                        break
                    List_count_low += 1

                #high cut
                List_count_high = 0
                for row in freqList:
                    if row >= 500: #500Hz以下
                        break
                    List_count_high += 1

                spectrum_sum = np.sum(power_spectrum[List_count_low:List_count_high])

                find_mid = 0
                i = List_count_low

                while find_mid < spectrum_sum / 2:
                    find_mid += power_spectrum[i]
                    i += 1
                mid_f = i - 1

                MdPF_Frames2.append(freqList[mid_f])

                index_MdPF2 = len(MyoRe_frames2)-1
            """
        Beep(1100, 1000) #end beep sound
        midi_input.close()
        pygame.midi.quit()

    def stop(self):
        #スレッドを停止させる
        self.stop_event.set()
        self.thread_Myo.join() #スレッドが停止するのを待つ
        self.thread_Sample.join() #スレッドが停止するのを待つ
        #self.thread_click.join()

#myo resample to 1kHz: interval is resampling rate[micro sec]
def Myo_resample(Myo_Frames, interval):
    dx1 = 0
    dx2 = 0

    #resampling
    MyoRe_frames = []

    for i in range(len(Myo_Frames)):
        #リサンプリング周期よりサンプル周期が早い場合
        if interval > Myo_Frames[i][1]:
            #サンプリングとリサンプリングが合致
            if dx1 == 0:
                dx2 = 0
                MyoRe_frames.append(Myo_Frames[i][2])
                dx1 = interval - Myo_Frames[i][1]
            #サンプリング間にリサンプリング点が収まらない場合　・ |   　|  ・
            elif (dx2 + Myo_Frames[i][1]) < interval:
                dx2 += Myo_Frames[i][1]
                dx1 = interval - dx2 - Myo_Frames[i][1]
            #サンプリング間にリサンプリング点が収まる場合        | ・  |
            elif dx2 + Myo_Frames[i][1] > interval:
                dx2 = Myo_Frames[i][1] - dx1
                try:
                    MyoRe_frames.append( Myo_Frames[i-1][2] + (((Myo_Frames[i][2] - Myo_Frames[i-1][2])) * ((float)(dx1)/(dx1 + dx2))) )
                except:
                    if dx1 <= dx2:
                        MyoRe_frames.append(Myo_Frames[i-1][2])
                    else:
                        MyoRe_frames.append(Myo_Frames[i][2])

                dx1 = interval - dx2

        #リサンプリング周期よりサンプル周期が遅い場合
        else:
            #サンプリングとリサンプリングが合致
            if dx1 == 0:
                MyoRe_frames.append(Myo_Frames[i][2])
                dx2 = 0
                dx1 = interval
            #サンプリング間にリサンプリング点が1つ
            elif dx1 + interval > Myo_Frames[i][1]:
                dx2 = Myo_Frames[i][1] - dx1
                try:
                    MyoRe_frames.append( Myo_Frames[i-1][2] + (((Myo_Frames[i][2] - Myo_Frames[i-1][2])) * ((float)(dx1)/(dx1 + dx2))) )
                except:
                    if dx1 <= dx2:
                        MyoRe_frames.append(Myo_Frames[i-1][2])
                    else:
                        MyoRe_frames.append(Myo_Frames[i][2])
                dx1 = interval - dx2
            #サンプリング間にリサンプリング点が2つ以上
            elif dx1 + interval < Myo_Frames[i][1]:
                num = ((Myo_Frames[i][1] - dx1) / interval) + 1
                dx1_2 = dx1
                dx2_2 = dx2

                for j in range(num):
                    dx2 = Myo_Frames[i][1] - dx1
                    try:
                        MyoRe_frames.append( Myo_Frames[i-1][2] + (((Myo_Frames[i][2] - Myo_Frames[i-1][2])) * ((float)(dx1)/(dx1 + dx2))) )
                    except:
                        if dx1 <= dx2:
                            MyoRe_frames.append(Myo_Frames[i-1][2])
                        else:
                            MyoRe_frames.append(Myo_Frames[i][2])
                    dx1 = (interval * (j + 1)) + dx1_2

                dx1 = interval - dx2
    return MyoRe_frames

"""#myo resample to 1kHz: interval is resampling rate[micro sec]
def Myo_resample(Myo_Frames, interval):
    dx1 = 0
    dx2 = 0

    #resampling
    MyoRe_frames = []

    for i in range(len(Myo_Frames)):
        #サンプリングとリサンプリングが合致
        if dx1 == 0:
            MyoRe_frames.append(Myo_Frames[i][2])
            dx2 = 0
            dx1 = interval
        #サンプリング間にリサンプリング点が1つ
        elif dx1 + interval > Myo_Frames[i][1]:
            dx2 = Myo_Frames[i][1] - dx1
            try:
                MyoRe_frames.append( Myo_Frames[i-1][2] + (((Myo_Frames[i][2] - Myo_Frames[i-1][2])) * ((float)(dx1)/(dx1 + dx2))) )
            except:
                if dx1 <= dx2:
                    MyoRe_frames.append(Myo_Frames[i-1][2])
                else:
                    MyoRe_frames.append(Myo_Frames[i][2])
            dx1 = interval - dx2
        #サンプリング間にリサンプリング点が2つ以上
        elif dx1 + interval < Myo_Frames[i][1]:
            num = ((Myo_Frames[i][1] - dx1) / interval) + 1
            dx1_2 = dx1
            dx2_2 = dx2

            for j in range(num):
                dx2 = Myo_Frames[i][1] - dx1
                try:
                    MyoRe_frames.append( Myo_Frames[i-1][2] + (((Myo_Frames[i][2] - Myo_Frames[i-1][2])) * ((float)(dx1)/(dx1 + dx2))) )
                except:
                    if dx1 <= dx2:
                        MyoRe_frames.append(Myo_Frames[i-1][2])
                    else:
                        MyoRe_frames.append(Myo_Frames[i][2])
                dx1 = (interval * (j + 1)) + dx1_2

            dx1 = interval - dx2
    return MyoRe_frames
"""
#MdPF calc
def MdPF_calc(Myo_Frames):
    pass
    """
    index_MdPF1 = 0
    index_MdPF2 = 0
    rate = 1000 #sampling rate
    nyq = rate/2 #ナイキスト周波数

    #MdPF ex
    if len(MyoRe_frames1) - index_MdPF1 >= 1000:
        #high pass fir
        fe = 20.0 / nyq #[Hz]
        numtaps = 255 #フィルタ係数（タップの数（要奇数））
        co = spsig.firwin(numtaps, fe, pass_zero=False) #setting coefficient
        high_pass_sig = spsig.lfilter(co, 1, MyoRe_frames1[index_MdPF1:len(MyoRe_frames1)-1])

        power_spectrum = do_fft(high_pass_sig)
        freqList = fftfreq(high_pass_sig.size, d = 1.0 / rate)  #周波数の分解能計算

        # --- 表示周波数帯制限 ---
        #low cut
        List_count_low = 0
        for row in freqList:
            if row > 20: #20Hz以上
                break
            List_count_low += 1

        #high cut
        List_count_high = 0
        for row in freqList:
            if row >= 500: #500Hz以下
                break
            List_count_high += 1

        spectrum_sum = np.sum(power_spectrum[List_count_low:List_count_high])

        find_mid = 0
        i = List_count_low

        while find_mid < spectrum_sum / 2:
            find_mid += power_spectrum[i]
            i += 1
        mid_f = i - 1

        MdPF_Frames1.append(freqList[mid_f])

        index_MdPF1 = len(MyoRe_frames1)-1
    """

#midi save
def Midi_write(MIDI_OUTPUT_FILENAME, Midi_Frames):
    f = open(MIDI_OUTPUT_FILENAME, "w")
    for row in Midi_Frames:
        if row[1] > 0:
            f.write(str(row[0])) #時間
            f.write("\t")
            f.write(str(row[1])) #音量
            f.write("\n")
    f.close()

def Myo_write(MYO_OUTPUT_FILENAME, Myo_Frames):
    f = open(MYO_OUTPUT_FILENAME, "w")
    for row in Myo_Frames:
        f.write(str(row[0]))
        f.write("\t")
        f.write(str(row[1]))
        f.write("\t")
        f.write(str(row[2]))
        f.write("\n")
    f.close()

def MdPF_write(MdPF_OUTPUT_FILENAME, MdPF_Frames):
    f = open(MdPF_OUTPUT_FILENAME, "w")
    for row in MdPF_Frames:
        f.write(str(row))
        f.write("\n")
    f.close()

def MyoRe_write(MyoRe_OUTPUT_FILENAME, MyoRe_Frames):
    f = open(MyoRe_OUTPUT_FILENAME, "w")
    for row in MyoRe_Frames:
        f.write(str(row))
        f.write("\n")
    f.close()

#---main program---
if __name__ == "__main__":
    filename_head = "..\\..\\data\\preexperiment\\test\\" #record file path head
    print "file path = ", filename_head

    print "input num that \"file_num\""
    file_num = raw_input()

    fig = plt.figure()

    record_flag = 0

    #thread start
    thread_do = control_th()
    print "please input any key for continue"

    raw_input()
    record_flag = 1

    #wait time for stabilization
    for count in [3, 2, 1]:
        print str(count) + " seconds before play start"
        sleep(1)

    #---rec part---
    print "play start"

    record_flag = 2 #start record
    ani = animation.FuncAnimation(fig, Data_Plot, interval = 100)
    plt.show()

    record_flag = 1
    print ("finished recording")
    print ("wait...")

    #thread end
    thread_do.stop()

    #---output part---
    MIDI_OUTPUT_FILENAME = filename_head + "midi\\midi_file" + str(file_num) + ".txt" #midi file name

    MYO_OUTPUT_FILENAME1 = filename_head + "myo\\myo_file" + str(file_num) + "ex.txt" #myo file name extensor muscle
    MYO_OUTPUT_FILENAME1_re = filename_head + "myo\\myo_file" + str(file_num) + "ex_resample.txt" #resample myo file name extensor muscle
    MdPF_OUTPUT_FILENAME1 = filename_head + "analysis\\mdpf\\mdpf_file" + str(file_num) + "ex_1kHz.txt"

    MYO_OUTPUT_FILENAME2 = filename_head + "myo\\myo_file" + str(file_num) + "fl.txt" #myo file name flexor muscle
    MYO_OUTPUT_FILENAME2_re = filename_head + "myo\\myo_file" + str(file_num) + "fl_resample.txt" #resample myo file name flexor muscle
    MdPF_OUTPUT_FILENAME2 = filename_head + "analysis\\mdpf\\mdpf_file" + str(file_num) + "fl_1kHz.txt"

    #midi output
    Midi_write(MIDI_OUTPUT_FILENAME, Midi_Frames)

    #Myoelectronical output
    #resampling interval
    interval = 1000 #[micro sec]

    MyoRe_frames1 = []
    MyoRe_frames2 = []

    MyoRe_frames1 = Myo_resample(Myo_Frames1, interval)
    Myo_write(MYO_OUTPUT_FILENAME1, Myo_Frames1)
    MyoRe_write(MYO_OUTPUT_FILENAME1_re, MyoRe_frames1)

    MyoRe_frames2 = Myo_resample(Myo_Frames2, interval)
    Myo_write(MYO_OUTPUT_FILENAME2, Myo_Frames2)
    MyoRe_write(MYO_OUTPUT_FILENAME2_re, MyoRe_frames2)

    #MdPF output
    MdPF_Frames1 = []
    MdPF_Frames2 = []

    MdPF_Frames1 = MdPF_calc(MyoRe_frames1)
    MdPF_Frames2 = MdPF_calc(MyoRe_frames2)

    MdPF_write(MdPF_OUTPUT_FILENAME1, MdPF_Frames1)
    MdPF_write(MdPF_OUTPUT_FILENAME2, MdPF_Frames2)

    print "finished"
