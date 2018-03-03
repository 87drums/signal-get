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

#---settings---
beep_type_num = 0 #音高

Myo_Frames1 = [] #Myoelectronical signal colums
Myo_Frames2 = [] #Myoelectronical signal colums
MyoRe_frames = []
MyoMean_frames = [] #Myo time & mean velocity colums(Mean values for show) [[time, val],[time, val],...,[time, val]]
Midi_Frames = [] #Midi colums [[time_stamp, velocity],[time_stamp, velocity],...,[time_stamp, velocity]]
MdPF_Frames = []

#myoelectronical(arduino) setup
ser1 = serial.Serial("COM3",57600) #デバイス名とボーレート（arduino側も同じ数値に要設定）
record_flag = 0

#fft by hamming window
def do_fft(sig):
    win = hamming(sig.size)
    sig_spectrum = fft(sig * win)
    return abs(sig_spectrum[: sig.size / 2 + 1])

#plot update. mm_list is myo mean value, m_list is midi's velocity.
def Data_Plot(data):
    plt.rcParams["font.size"] = 24

    #myo mean plot
    plt.subplot(2,2,1)
    plt.cla()
    plt.title('MyoMean')
    #plt.axis("off")
    mm_list_size = len(MyoMean_frames) #myo mean list
    if mm_list_size > 100:
        mm_list_size = 100

    mm_x = np.zeros(1)
    mm_y = np.zeros(1)

    for i, row in enumerate(MyoMean_frames[-(mm_list_size):]):
        if i == 0:
            mm_x[0] = row[0]
            mm_y[0] = row[1]
        else:
            mm_x = np.append(mm_x, mm_x[i-1] + row[0])
            mm_y = np.append(mm_y, row[1])
    mm_im = plt.plot(mm_x, mm_y)

    #midi's velocity plot
    plt.subplot(2,2,2)
    plt.cla()
    plt.title('MIDI')
    #plt.axis("off")
    plt.ylim((0,127)) #velocity is defined number of 0 to 127.

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
    plt.hlines(y=[50,70], xmin = x_min, xmax = x_max, colors = 'r', linestyles = 'dashed', linewidths = 2)
    m_im = plt.plot(m_x, m_y)

    #MdPF plot
    plt.subplot(2,2,3)
    plt.cla()
    plt.title('MdPF')
    #plt.axis("off")

    #plt.ylim((20,500))
    md_list_size = len(MdPF_Frames) #midi list
    if md_list_size > 100:
        md_list_size = 100

    md_im = plt.plot(MdPF_Frames[-(md_list_size)-1:])

#define thread class
class control_th():
    def __init__(self):
        self.stop_event = threading.Event() #停止させるかのフラグ

        #スレッドの作成と開始
        self.thread_click = threading.Thread(target = self.click_get)
        self.thread_Myo = threading.Thread(target = self.Myo_get)
        self.thread_Sample = threading.Thread(target = self.Data_Sample)

        self.thread_click.start()
        self.thread_Myo.start()
        self.thread_Sample.start()

    def Myo_get(self):
        size_count = 0

        dx1 = 0
        dx2 = 0

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

            if record_flag == 2:
                Myo_Frames1.append([indent, t_data3, data1_3])
                Myo_Frames2.append([indent, t_data3, data2_3])

                #resampling
                interval = 1000 #[micro sec]
                if dx1 == 0:
                    MyoRe_frames.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                    dx1 = interval
                elif dx1 + interval > Myo_Frames1[len(Myo_Frames1)-1][1]:
                    dx2 = Myo_Frames1[len(Myo_Frames1)-1][1] - dx1
                    try:
                        MyoRe_frames.append( Myo_Frames1[len(Myo_Frames1)-2][2] + (((Myo_Frames1[len(Myo_Frames1)-1][2] - Myo_Frames1[len(Myo_Frames1)-2][2])) * ((float)(dx1)/(dx1 + dx2))) )
                    except:
                        if dx1 <= dx2:
                            MyoRe_frames.append(Myo_Frames1[len(Myo_Frames1)-2][2])
                        else:
                            MyoRe_frames.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                    dx1 = interval - dx2
                elif dx1 + interval < Myo_Frames1[len(Myo_Frames1)-1][1]:
                    num = ((Myo_Frames1[len(Myo_Frames1)-1][1] - dx1) / interval) + 1
                    dx1_2 = dx1
                    dx2_2 = dx2

                    for i in range(num):
                        dx2 = Myo_Frames1[len(Myo_Frames1)-1][1] - dx1
                        try:
                            MyoRe_frames.append( Myo_Frames1[len(Myo_Frames1)-2][2] + (((Myo_Frames1[len(Myo_Frames1)-1][2] - Myo_Frames1[len(Myo_Frames1)-2][2])) * ((float)(dx1)/(dx1 + dx2))) )
                        except:
                            if dx1 <= dx2:
                                MyoRe_frames.append(Myo_Frames1[len(Myo_Frames1)-2][2])
                            else:
                                MyoRe_frames.append(Myo_Frames1[len(Myo_Frames1)-1][2])
                        dx1 = (interval * (i + 1)) + dx1_2

                    dx1 = interval - dx2


            wait_size = ser1.in_waiting

            if size_count % 1000 == 0:
                #if record_flag is not 2:
                print "data1 = ", data1_3, " data2 = ", data2_3, " time_duration = ", t_data3, " waiting_bytes = ", wait_size
                size_count = 0

            size_count += 1

        Beep(1100, 1000)

    #Myomean and MIDI and MdPF sampling
    def Data_Sample(self):
        while record_flag == 0:
            pass

        pygame.midi.init()
        input_id = 2#pygame.midi.get_default_input_id()
        midi_input = pygame.midi.Input(input_id)

        #print input_id, pygame.midi.get_device_info(input_id)

        index_mm = 0
        index_MdPF = 0
        rate = 1000 #sampling rate
        nyq = rate/2 #ナイキスト周波数

        while not self.stop_event.is_set():
            #MyoMean
            if len(Myo_Frames1) - index_mm >= 100:
                time_sum = 0
                myo_sum = 0
                for row in Myo_Frames1[index_mm:len(Myo_Frames1)-1]:
                    time_sum += row[1]
                    myo_sum += row[2]
                try:
                    MyoMean_frames.append([time_sum, myo_sum/((len(Myo_Frames1) - 1) - index_mm)]) #[ms, mean amplitude]
                except ZeroDivisionError:
                    print("num less!!")
                index_mm = len(Myo_Frames1)-1

            #MIDI
            midi_info = midi_input.read(10) #midi_info[[[x,y,vel], time_stamp],...]
            if len(midi_info) > 0:
                #if (record_flag is not 2) and (len(midi_info) <= 0):
                    #record_flag = 2
                    #print "test"
                for row in midi_info:
                    if row[0][2] > 0:
                        Midi_Frames.append([row[1], row[0][2]])

            #MdPF
            if len(MyoRe_frames) - index_MdPF >= 1000:
                #high pass fir
                fe = 20.0 / nyq #[Hz]
                numtaps = 255 #フィルタ係数（タップの数（要奇数））
                co = spsig.firwin(numtaps, fe, pass_zero=False) #setting coefficient
                high_pass_sig = spsig.lfilter(co, 1, MyoRe_frames[index_MdPF:len(MyoRe_frames)-1])

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

                MdPF_Frames.append(freqList[mid_f])

                index_MdPF = len(MyoRe_frames)-1

        midi_input.close()
        pygame.midi.quit()

    def click_get(self):
        bpm = 120 #beat per minute
        beeptime = 100 #click time[msec]
        bpm_time = 1000.0/(bpm / 60.0) #time/1cl-ick[msec]
        minus_beeptime = (bpm_time - beeptime)/1000.0 #wait time between clicks[sec]

        while record_flag == 0:
            pass
        #click_count = 0
        beep_type = [1100, 700]
        while not self.stop_event.is_set():
            Beep(beep_type[beep_type_num], beeptime/2)
            sleep(minus_beeptime/2)
            #if record_flag == 1:
                #click_count += 1

    def stop(self):
        #スレッドを停止させる
        self.stop_event.set()
        self.thread_Myo.join() #スレッドが停止するのを待つ
        self.thread_Sample.join() #スレッドが停止するのを待つ
        self.thread_click.join()

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
    RECORD_SECONDS = 2 #rec time[sec]
    fig = plt.figure()

    beep_type_num = 0
    record_flag = 0

    #thread start
    thread_do = control_th()
    print "please input any key for continue"

    raw_input()
    record_flag = 1

    #wait time for stabilization
    for count in [5, 4, 3, 2, 1]:
        print str(count) + " seconds before play start"
        sleep(1)
    beep_type_num = 1

    #---rec part---
    print "play start"

    record_flag = 2
    #sleep(RECORD_SECONDS)
    ani = animation.FuncAnimation(fig, Data_Plot, interval = 100)
    plt.show()

    record_flag = 1
    print ("finished recording")
    print ("wait...")

    #thread end
    thread_do.stop()
    ser1.close() #シリアルポートのクローズ

    #---output part---
    filename_head = "..\\..\\data\\preexperiment\\20170823_demotest\\"
    file_num = 1
    MIDI_OUTPUT_FILENAME = filename_head + "midi\\midi_file" + str(file_num) + ".txt" #midi file name
    MYO_OUTPUT_FILENAME1 = filename_head + "myo\\myo_file" + str(file_num) + ".txt" #myo file name
    MYO_OUTPUT_FILENAME2 = filename_head + "myo\\myo_file" + str(file_num) + "_resample.txt" #resample myo file name
    MdPF_OUTPUT_FILENAME = filename_head + "analysis\\mdpf\\mdpf_file" + str(file_num) + "_1kHz.txt"

    #midi output
    Midi_write(MIDI_OUTPUT_FILENAME, Midi_Frames)

    #Myoelectronical output
    Myo_write(MYO_OUTPUT_FILENAME1, Myo_Frames1)
    MyoRe_write(MYO_OUTPUT_FILENAME2, MyoRe_frames)

    #MdPF output
    MdPF_write(MdPF_OUTPUT_FILENAME, MdPF_Frames)

    print "finished"
