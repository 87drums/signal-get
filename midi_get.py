# -*- coding:utf-8 -*-
import pygame.midi
"""
# --- port number check ---
pygame.init()
pygame.midi.init()
count = pygame.midi.get_count()
print("get_default_input_id:%d" % pygame.midi.get_default_input_id())
print("get_default_output_id:%d" % pygame.midi.get_default_output_id())
print("No:(interf, name, input, output, opened)")
for i in range(count):
    print("%d:%s" % (i, pygame.midi.get_device_info(i)))
"""
"""
# result
get_default_input_id:1
get_default_output_id:0
No:(interf, name, input, output, opened)
1:('MMSystem', 'MIDI (OCTA-CAPTURE)', 1, 0, 0)
5:('MMSystem', 'MIDI (OCTA-CAPTURE)', 0, 1, 0)
"""
MIDI_OUTPUT_FILENAME = "../Midi_file.txt"
Midi_Frames = []

#pygame.init()
pygame.midi.init()
input_id = pygame.midi.get_default_input_id()
print("input MIDI:%d" % input_id)
i = pygame.midi.Input(input_id)

raw_input("press Enter key for rec start")
print ("starting")
print ("full midi_events:[[[status,data1,data2,data3],timestamp],...]")

going = True
count = 0
while going:
    if i.poll():
        midi_events = i.read(10)
        Midi_Frames.append(midi_events)
        #print "full midi_events:" + str(midi_events)
        count += 1
    if count >= 10:
        going = False

i.close()
pygame.midi.quit()
pygame.quit()

print Midi_Frames
#print Midi_Frames
fm = open(MIDI_OUTPUT_FILENAME, "w")
for colum1 in Midi_Frames:
    for colum2 in colum1:
        if colum2[0][2] > 0:
            print colum2[0][2]
            fm.write(str(colum2[1]))
            fm.write(",")
            fm.write(str(colum2[0][2])) #ファイルに書き込み"""
            fm.write("\n")

exit()
