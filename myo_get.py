# -*- coding: utf-8 -*-
from time import sleep
from winsound import Beep
import serial
import threading
from time import time
import struct
import numpy as np

#---settings---
RECORD_SECONDS = 10 #rec time[sec]
bpm = 120 #beat per minute
beeptime = 100 #click time[msec]

bpm_time = 1000.0/(bpm / 60.0) #time/1click[msec]
minus_beeptime = (bpm_time - beeptime)/1000.0 #wait time between clicks[sec]

MYO_OUTPUT_FILENAME1 = "../data/preexperiment/myotest/myo/test1.txt" #myo file name

Myo_Frames1 = [] #Myoelectronical signal colums


#myoelectronical(arduino) setup
ser1 = serial.Serial("COM4",57600) #デバイス名とボーレート（arduino側も同じ数値に要設定）
record_flag = 0
th_start_time = 0.0 #thread start time
th_end_time = 0.0 #thread end time

#define thread class
class control_th():

    def __init__(self):
        self.stop_event = threading.Event() #停止させるかのフラグ

        #スレッドの作成と開始
        self.thread_Myo = threading.Thread(target = self.Myo_get)
        self.thread_Myo.start()

    def Myo_get(self):
        while record_flag == 0:
            data = ser1.read()

        th_start_time = time() #thread start time

        while not self.stop_event.is_set():
            data1 = ser1.read()
            Myo_Frames1.append(data1)
        th_end_time = time() #thread end time
        Myo_Frames1.insert(0, str(th_end_time - th_start_time))

    def stop(self):
        #スレッドを停止させる
        self.stop_event.set()
        self.thread_Myo.join() #スレッドが停止するのを待つ

def Myo_write(MYO_OUTPUT_FILENAME, Myo_Frames):
    f = open(MYO_OUTPUT_FILENAME, "w")

    #outliers = "鈎b魔ﾁiｊｂﾊﾙ" #外れ値群　""の中にどんどん追加していく書式
    f.write(str(Myo_Frames[0])) #write time while Myo get
    f.write("\n")
    for row in Myo_Frames[1:]:
        data = ord(row)
        #負を表す値を-値へ変換
        #if data >= 126:
            #data = data - 255
        f.write(str(data))
        f.write("\n")
    f.close()

#---main program---
if __name__ == "__main__":
    #thread start
    thread_do = control_th()

    #---rec part---
    raw_input("press Enter key for rec start")
    record_flag = 1

    #head margin countdown to rec start
    for count in [4,3,2,1]:
        print count
        Beep(700,beeptime)
        sleep(minus_beeptime)
    print "recording..."

    #指定秒数で録音終了
    click_count = 0
    while True:
        if click_count/(bpm / 60) >= RECORD_SECONDS: #指定秒数でループ終了
            break
        Beep(700,beeptime)
        sleep(minus_beeptime)
        click_count += 1

    print ("finished recording")
    print ("wait...")

    #bottom margin
    for count in [4,3,2,1]:
        Beep(900,beeptime)
        sleep(minus_beeptime) # + (beeptime * 0.001))

    thread_do.stop()
    ser1.close() #シリアルポートのクローズ

    #---output part---

    #Myoelectronical output
    Myo_write(MYO_OUTPUT_FILENAME1, Myo_Frames1)

    print "press Enter key for all finish"
    print "finished"
    Beep(1100,1000)
