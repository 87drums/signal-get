# -*- coding: utf-8 -*-
import pyaudio
import wave
from time import sleep
from winsound import Beep
import serial
import threading
from time import time
import pygame.midi

#---settings---
MYO_OUTPUT_FILENAME = "../data/preexperiment/test/myo/myo_filetest1_1.txt" #myo file name

Myo_Frames = [] #Myoelectronical signal colums

#myoelectronical(arduino) setup
ser = serial.Serial("COM3",115200) #デバイス名とボーレート（arduino側も同じ数値に要設定）

#define thread class
class control_th():

    def __init__(self):
        self.stop_event = threading.Event() #停止させるかのフラグ

        #スレッドの作成と開始
        #print "time = " + str(time())
        self.thread_Myo = threading.Thread(target = self.Myo_get)
        self.thread_Myo.start()

    def Myo_get(self):
        count = 0
        th_start_time = time() #thread start time
        while not self.stop_event.is_set():
            data = ser.read()
            Myo_Frames.append(data)
            if count >= 10000:
                now = time()
                #print "time = " + str(time())
                print "pc time = " + str(time() - th_start_time)
                count = 0
                th_start_time = now
            else:
                count += 1

    def stop(self):
        #スレッドを停止させる
        self.stop_event.set()
        self.thread_Myo.join() #スレッドが停止するのを待つ
        #self.thread_Midi.join() #スレッドが停止するのを待つ

#---main program---
if __name__ == "__main__":
    audio = pyaudio.PyAudio()

    #---rec part---
    raw_input("press Enter key for rec start")

    th_start_time = time() #thread start time

    #thread start
    thread_do = control_th()

    print ("recording...")
    raw_input("press enter key for rec end") #rec end by press enter
    print ("finished recording")
    print ("wait...")

    #thread end
    thread_do.stop()

    #---output part---
    ser.close() #シリアルポートのクローズ

    print "finished"
