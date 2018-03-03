# -*-coding:utf-8-*-
import numpy as np

def missed_check(filename):
    content = np.loadtxt(filename)

    content_index = content[0][0]
    for i,row in enumerate(content[1:]):
        if (row[0] >= (content_index + 2)) or (row[0] <= content_index):
            if row[0] <= 0:
                pass
            else:
                print "!!!missed warning!!! ", i - 1, " line"
        content_index = row[0]
    print "check finish"

if __name__ == "__main__":
    filename_head = "../../data/mainexperiment/2/myo/"
    filename = filename_head + "myo_file0ex.txt"
    missed_check(filename)
