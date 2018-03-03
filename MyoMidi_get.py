# -*- coding: utf-8 -*-
import wave
from time import sleep
from winsound import Beep
import serial
import threading
from threading import Timer
from time import time
import struct
import pygame.midi
import pygame
import pyaudio
import win32gui

#---settings---
#window size
SCREEN_SIZE_x = 1200
SCREEN_SIZE_y = 800

x_tick = [int(SCREEN_SIZE_x/4), int(SCREEN_SIZE_x/4)*2, int(SCREEN_SIZE_x/4)*3] #叩打表示のx軸刻み幅（3個分表示を仮定）
color_tick = [(150, 150, 150), (50, 50 , 50), (200, 0, 0)] #叩打音量における過去データを薄く表示

base_vel = 64 #midi velocity
base_tick = int(SCREEN_SIZE_y/127) #0~127のmidi記号ベロシティに対応した画面の刻み幅計算
base_height = 8 #音量基準線の幅

RECORD_SECONDS = 30 #rec time[sec]
bpm = 120 #beat per minute
beeptime = 100 #click time[msec]

beep_type = [1100, 700]
beep_type_num = 0

bpm_time = 1000.0/(bpm / 60.0) #time/1cl-ick[msec]
minus_beeptime = (bpm_time - beeptime)/1000.0 #wait time between clicks[sec]

filename_head = "../data/preexperiment/test/"
file_num = "1"

MIDI_OUTPUT_FILENAME = filename_head + "midi/midi_file" + str(file_num) + ".txt" #midi file name
MYO_OUTPUT_FILENAME1 = filename_head + "myo/myo_file" + str(file_num) + "-1.txt" #myo file name
MYO_OUTPUT_FILENAME2 = filename_head + "myo/myo_file" + str(file_num) + "-2.txt" #myo file name

Myo_Frames1 = [] #Myoelectronical signal colums
Myo_Frames2 = [] #Myoelectronical signal colums
Midi_Frames = [] #Midi's time & velocity colums

#myoelectronical(arduino) setup
ser1 = serial.Serial("COM3",57600) #デバイス名とボーレート（arduino側も同じ数値に要設定）
ser2 = serial.Serial("COM4",57600) #デバイス名とボーレート（arduino側も同じ数値に要設定）
record_flag = 0
th_start_time = 0.0 #thread start time
th_end_time = 0.0 #thread end time

#screen update
def screen_update(screen, vel):
    #画面クリア
    screen.fill((255, 255, 255)) #必要なところだけ白に戻した方が軽い説もあるので後で試す
    #基準線描画
    pygame.draw.line(screen, (0, 0, 0), (0, base_tick * (base_vel - base_height)), (SCREEN_SIZE_x, base_tick * (base_vel - base_height)))
    pygame.draw.line(screen, (0, 0, 0), (0, base_tick * (base_vel + base_height)), (SCREEN_SIZE_x, base_tick * (base_vel + base_height)))
    pygame.draw.line(screen, (0, 0, 0), (x_tick[len(x_tick)-1], 0), (x_tick[len(x_tick)-1], SCREEN_SIZE_y))
    #演奏ベロシティ描画
    for i in range(len(x_tick)):
        pygame.draw.circle(screen, color_tick[i], (x_tick[i], base_tick * (127 - vel[i][0][0][2])), base_tick * base_height/3)

    pygame.display.update()

#define thread class
class control_th():

    def __init__(self):
        self.stop_event = threading.Event() #停止させるかのフラグ

        #スレッドの作成と開始
        self.thread_click = threading.Thread(target = self.click_get)
        self.thread_Myo = threading.Thread(target = self.Myo_get)
        self.thread_Midi = threading.Thread(target = self.Midi_get)

        self.thread_click.start()
        self.thread_Myo.start()
        self.thread_Midi.start()

    def Myo_get(self):
        size_count = 0
        while record_flag == 0:
            data = ser1.read()
            data = ser2.read()

        th_start_time = time() #thread start time
        while not self.stop_event.is_set():
            #size_count += 1
            data1 = ser1.read()
            data2 = ser2.read()
            th_now_time = time()
            Myo_Frames1.append([th_now_time-th_start_time, data1])
            Myo_Frames2.append([th_now_time-th_start_time, data2])

        th_end_time = time() #thread end time
        Myo_Frames1.insert(0, str(th_end_time - th_start_time))
        Myo_Frames2.insert(0, str(th_end_time - th_start_time))
        Beep(1100, 1000)

    #use if you need velocity and tap intervals from midi command by pygame
    def Midi_get(self):
        pygame.init()
        pygame.midi.init()
        input_id = pygame.midi.get_default_input_id()
        wm_info = pygame.display.get_wm_info()
        handle = wm_info["window"]

        win32gui.MoveWindow(handle,200,-1000,SCREEN_SIZE_x,SCREEN_SIZE_y,1) #window表示位置指定

        screen = pygame.display.set_mode([SCREEN_SIZE_x, SCREEN_SIZE_y])

        pygame.display.set_caption("test")

        for i in range(len(x_tick)):
            Midi_Frames.append([[[0,0,base_vel]]])
        screen_update(screen, Midi_Frames[len(Midi_Frames)-len(x_tick):])

        midi_input = pygame.midi.Input(input_id)
        while not self.stop_event.is_set():
            if midi_input.poll():
                vel = midi_input.read(1)
                if vel[0][0][2] > 0:
                    Midi_Frames.append(vel)
                    screen_update(screen, Midi_Frames[len(Midi_Frames)-len(x_tick):])

        midi_input.close()
        pygame.midi.quit()
        pygame.quit()

    def click_get(self):
        click_count = 0
        while not self.stop_event.is_set():
            Beep(beep_type[beep_type_num], beeptime/2)
            sleep(minus_beeptime/2)
            if record_flag == 1:
                click_count += 1

    def stop(self):
        #スレッドを停止させる
        self.stop_event.set()
        self.thread_Myo.join() #スレッドが停止するのを待つ
        self.thread_Midi.join() #スレッドが停止するのを待つ

def Midi_write(MIDI_OUTPUT_FILENAME, Midi_Frames):
    f = open(MIDI_OUTPUT_FILENAME, "w")
    for colum1 in Midi_Frames:
        for colum2 in colum1:
            if colum2[0][2] > 0:
                f.write(str(round(colum2[1], 3))) #時間
                f.write(",")
                f.write(str(colum2[0][2])) #音量
                f.write("\n")
    f.close()

def Myo_write(MYO_OUTPUT_FILENAME, Myo_Frames):
    f = open(MYO_OUTPUT_FILENAME, "w")

    #outliers = "鈎b魔ﾁiｊｂﾊﾙ" #外れ値群　""の中にどんどん追加していく書式
    f.write(str(Myo_Frames[0])) #write time while Myo get
    f.write("\n")
    for row in Myo_Frames[1:]:
        if type(row[1]) == float:
            data = row[1]
        else:
            data = ord(row[1])

        f.write(str(row[0]))
        f.write(",")
        f.write(str(data))
        f.write("\n")

    f.close()

#---main program---
if __name__ == "__main__":
    print "wait"
    beep_type_num = 0
    #thread start
    thread_do = control_th()

    #wait time for stabilization
    #wait time for stabilization
    for count in [5, 4, 3, 2, 1]:
        print str(count) + " seconds before play start"
        #Beep(700,beeptime)
        sleep(1)
    beep_type_num = 1

    #---rec part---
    #raw_input("press Enter key for rec start")
    print "play start"
    #sleep(5)

    record_flag = 1

    sleep(RECORD_SECONDS)

    #raw_input() #rec end by press enter
    print ("finished recording")
    print ("wait...")

    #thread end
    thread_do.stop()
    ser1.close() #シリアルポートのクローズ
    ser2.close() #シリアルポートのクローズ

    #---output part---

    #midi output
    Midi_write(MIDI_OUTPUT_FILENAME, Midi_Frames[len(x_tick):])

    #Myoelectronical output
    Myo_write(MYO_OUTPUT_FILENAME1, Myo_Frames1)
    Myo_write(MYO_OUTPUT_FILENAME2, Myo_Frames2)

    print "finished"
