# -*- shiftCT.py -*-
"""
Shift the registered CT to reference CT coordinate based on input translation

Created on Mon May 23 15:41:59 2016

@author: ch4jm
"""
import os, glob, re, datetime
import dicom
from tkinter import *
from tkinter.filedialog import askdirectory
###############################

###############################
def openDir(winTitle):
    global baseFolder
    POPWin = Tk()
    POPWin.withdraw()
    POPWin.update()
    if 'baseFolder' in globals():
        if os.path.exists(baseFolder):
            folderName = askdirectory(title=winTitle,initialdir=baseFolder)
        else:
            folderName = askdirectory(title=winTitle)
    else:
        folderName = askdirectory(title=winTitle)
    POPWin.destroy()
    baseFolder = os.path.dirname(folderName)
    return folderName
###############################
def shiftCT():
    ##obtain info from reference CT set
    folderRef = openDir('Select folder of reference CT')
    ffRef = glob.glob(os.path.join(folderRef,'CT*.dcm'))
    ds = dicom.read_file(ffRef[0]) #read the first image
    r_ref1 = ds.ImagePositionPatient #obtain coordinate of first image
    ds = dicom.read_file(ffRef[-1]) #read the last image
    r_ref2 = ds.ImagePositionPatient #obtain coordinate of last image
    x0_ref = r_ref2[0] #top corner x
    y0_ref = r_ref2[1] #top corner y
    zM_ref = 0.5*(r_ref1[2]+r_ref2[2]) #mid point z
    newforUID = ds.FrameOfReferenceUID #FoR of the original CT set
    
    ##obtain info from registered CT set
    folderReg = openDir('Select folder of registered CT')
    ffReg = glob.glob(os.path.join(folderReg,'CT*.dcm'))
    ds = dicom.read_file(ffReg[0]) #read the first image
    r_reg1 = ds.ImagePositionPatient #obtain coordinate of first image
    ds = dicom.read_file(ffReg[-1]) #read the last image
    r_reg2 = ds.ImagePositionPatient #obtain coordinate of last image
    x0_reg = r_reg2[0] #top corner x
    y0_reg = r_reg2[1] #top corner y
    zM_reg = 0.5*(r_reg1[2]+r_reg2[2]) #mid point z

    #shift of registered CT to coordinates of reference CT:
    shift0 = [(x0_ref-x0_reg),(y0_ref-y0_reg),(zM_ref-zM_reg)]
    shift = [(-11.38+shift0[0]),(8.79+shift0[1]),(21.74+shift0[2])]

    ########################################################
    ########################################################
    #create new study and series instance UID#
    newStr = ''.join(re.findall(r'[0-9]+',str(datetime.datetime.today())))
    currSUID = re.findall(r'[0-9]+',ds.StudyInstanceUID)
    for i in range(len(currSUID)-1):
        strLen = min(len(newStr),len(currSUID[i]))
        if strLen > 0:
            temStr = currSUID[i][0:strLen]
            currSUID[i] = temStr.replace(currSUID[i][0:strLen],newStr[0:strLen])
            newStr = newStr[strLen:]
    SsIUID = '.'.join(currSUID)
    ########################################################

    ##create save folder
    folderSave = folderReg + '_Shifted'
    if not os.path.exists(folderSave):
        os.makedirs(folderSave)
    else:
        cnt = 1
        while os.path.exists(folderSave):
            folderSave = folderReg + '_Shifted' + str(cnt)
            cnt = cnt+1
        os.makedirs(folderSave)
    
    ##create new SOP Instance UID
    newStr = ''.join(re.findall(r'[0-9]+',str(datetime.datetime.today())))
    currSUID = re.findall(r'[0-9]+',ds.SOPInstanceUID)
    for i in range(len(currSUID)-1,0,-1):
        strLen = min(len(newStr),len(currSUID[i]))
        if strLen > 0:
            temStr = currSUID[i][-strLen:]
            currSUID[i] = temStr.replace(currSUID[i][-strLen:],newStr[-strLen:])
            newStr = newStr[0:-strLen]
            
    ##perform shift to files in the directory
    ffReg = glob.glob(os.path.join(folderReg,'*.dcm'))      
    for f in ffReg:
        ds = dicom.read_file(f)
        ds.ImagePositionPatient[0] = ds.ImagePositionPatient[0]+shift[0]
        ds.ImagePositionPatient[1] = ds.ImagePositionPatient[1]+shift[1]
        ds.ImagePositionPatient[2] = ds.ImagePositionPatient[2]+shift[2]
        ds.FrameOfReferenceUID = newforUID
        ds.StudyInstanceUID = SsIUID
        ds.SeriesInstanceUID = SsIUID
        currSUID[-1] = str(int(currSUID[-1])+1)
        ds.SOPInstanceUID = '.'.join(currSUID)
        
        fs = os.path.join(folderSave,os.path.basename(f))
        ds.save_as(fs)
###############################
if __name__ == "__main__":
    print('start shift CT')
    shiftCT()
    print('finish shift CT')