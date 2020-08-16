# -*- zeroGantryTilt -*-#
"""
SYNOPSIS
    Summary of Script
    
DESCRIPTION
    Description of Script
    
EXAMPLES
    Show some examples of how to use this script.

VERSION 0.0
    Version history and ...
AUTHOR
    ch4jm in 2018/03
    
"""
import datetime, glob, os, re, sys, time
import numpy as np
import pydicom as dcm

def main(folder):
    ff = glob.glob(os.path.join(folder, '*'))
    foldersave = folder + '_NoTilt'
    if not os.path.exists(foldersave):
        os.makedirs(foldersave)

    ds = dcm.read_file(ff[0])
    sopiUID0 = ds.SOPInstanceUID
    newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
    newSOPUID = re.findall(r'[0-9]+', sopiUID0)
    for i in range(len(newSOPUID) - 1, 0, -1):
        strLen = min(len(newStr), len(newSOPUID[i]))
        if strLen > 0:
            temStr = newSOPUID[i][-strLen:]
            newSOPUID[i] = temStr.replace(newSOPUID[i][-strLen:], newStr[-strLen:])
            newStr = newStr[0:-strLen]

    for f in ff:
        ds = dcm.read_file(f)
        if ds.Modality == 'CT' or ds.Modality == 'MR':  # this would exclude RTSTRUCT, which doesn't have ImagePositionPatient
            tiltAng = ds.GantryDetectorTilt
            # shouldn't need to change any ImagePositionPatient or slicethickness
            newSOPUID[-1] = str(int(newSOPUID[-1]) + 1)
            ds.SOPInstanceUID = '.'.join(newSOPUID)
            ds.GantryDetectorTilt = 0.0
            ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
            fs = os.path.join(foldersave, os.path.basename(f))
            ds.save_as(fs)

if __name__ == '__main__':
    folder = 'C:\\Users\\ch4jm\\Desktop\\PatientCT'
    main(folder)
    sys.exit()