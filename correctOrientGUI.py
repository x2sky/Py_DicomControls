# -*- correctOrientGUI -*-#
"""
SYNOPSIS
    correct the dicom tag of images when the orientation is not tagged correctly

DESCRIPTION
    import the CT data set, pick the correct orientation, and correct for it

EXAMPLES
    Show some examples of how to use this script.

VERSION 0.0
AUTHOR
    ch4jm on 10/2/2017
    
"""

import datetime, dicom, glob, os, re, sys, time
from numpy import fliplr, flipud
from PyQt5.QtWidgets import QAction, qApp, QApplication, QCheckBox, QComboBox, QFileDialog, QGridLayout, QLineEdit, QLabel, \
    QMainWindow, QPushButton, QWidget
from PyQt5.QtCore import QDir


class MainCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # define directory texts, push button and labels
        label1 = QLabel('Import directory of image data set')
        button1 = QPushButton('Browse')
        self.text1 = QLineEdit()
        label2 = QLabel('Choose correct scanned patient orientation')
        self.dropmenu2 = QComboBox()
        self.dropmenu2.addItem('Head First Supine', 'HFS')
        self.dropmenu2.addItem('Feet First Supine', 'FFS')
        self.dropmenu2.addItem('Feet First Prone', 'FFP')
        self.dropmenu2.addItem('Head First Prone', 'HFP')
        self.cbox3 = QCheckBox()
        self.cbox3.setChecked(True)
        label3 = QLabel('Create new study & series UID')
        blank4 = QLabel('')
        button5 = QPushButton('&Correct')

        # layout of widgets
        qgl = QGridLayout()
        qgl.addWidget(label1, 0, 0, 1, 5)
        qgl.addWidget(button1, 0, 5)
        qgl.addWidget(self.text1, 1, 0, 1, 6)
        qgl.addWidget(label2, 2, 0, 1, 6)
        qgl.addWidget(self.dropmenu2, 3, 0, 1, 6)
        qgl.addWidget(self.cbox3, 4, 0)
        qgl.addWidget(label3, 4, 1, 1, 3)
        qgl.addWidget(label3, 4, 1, 1, 3)
        qgl.addWidget(blank4, 5, 1)
        qgl.addWidget(button5, 6, 2, 1, 2)
        self.setLayout(qgl)

        # define functions of texts and buttons
        button1.clicked.connect(lambda: self.BrowseDir('Select folder of image data set', self.text1))
        button5.clicked.connect(self.correctTag)

    def BrowseDir(self, title, activetext):
        global basefolder
        if 'basefolder' in globals():
            if os.path.exists(basefolder):
                rd = QFileDialog.getExistingDirectory(self, title, basefolder, QFileDialog.ShowDirsOnly)
            else:
                rd = QFileDialog.getExistingDirectory(self, title, QDir.current().path(), QFileDialog.ShowDirsOnly)
        else:
            rd = QFileDialog.getExistingDirectory(self, title, QDir.current().path(), QFileDialog.ShowDirsOnly)
        if os.path.exists(rd):
            rd = os.path.abspath(rd)
            basefolder = os.path.dirname(rd)
            activetext.setText(rd)
            self.parent().statusBar().showMessage('ready')

    def correctTag(self):
        if not os.path.exists(self.text1.text()):
            self.parent().statusBar().showMessage('Folder of images does not exist')
            return

        """
        This is the main function that performs the image correction
        """
        self.parent().statusBar().showMessage('Thinking and running')

        # obtain info from CT set
        folder = self.text1.text()
        ff = glob.glob(os.path.join(folder, '*'))
        try:
            ds = dicom.read_file(ff[0])  # read the first image
        except:
            self.parent().statusBar().showMessage('First file is not dicom file, Abort!')
            return

        # check consistency of all dicom images
        for f in ff:
            # test if file is dicom
            try:
                ds = dicom.read_file(f)  # read the image
            except:
                isDicom = False
                print('%s is not a dicom file.' %f)
            else:
                isDicom = True
            # gather dicom info
            if isDicom:
                if ds.Modality == 'CT' or ds.Modality == 'MR':
                    try:
                        forUID0
                    except NameError:  # if reference is not defined yet
                        forUID0 = ds.FrameOfReferenceUID  # frame of reference UID
                        studyiUID0 = ds.StudyInstanceUID  # study instance UID
                        seriesiUID0 = ds.SeriesInstanceUID  # series instance UID
                        sopiUID0 = ds.SOPInstanceUID
                        orient0 = ds.PatientPosition  # orientation
                        if orient0 != 'HFS' and orient0 != 'FFP' and orient0 != 'HFP' and orient0 !='FFS':  # if not canonical orient
                            orientIsOrdinary = False
                            orient0 = self.dropmenu2.itemData(self.dropmenu2.currentIndex())  # original orient will go to the chosen correct orient as default
                        else:
                            orientIsOrdinary = True
                        iop0 = ds.ImageOrientationPatient  # image orientation patient
                    if ds.FrameOfReferenceUID != forUID0:
                        self.parent().statusBar().showMessage('Discrepancy in image coordinates, Abort!')
                        return

        # create new study and series instance UID
        if self.cbox3.isChecked():
            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
            time.sleep(0.5)
            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3]) + newStr
            time.sleep(0.3)
            newStr = newStr + ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3])
            currSUID = re.findall(r'[0-9]+', studyiUID0)
            for i in range(len(currSUID) - 1):
                strLen = min(len(newStr), len(currSUID[i]))
                if strLen > 0:
                    temStr = currSUID[i][0:strLen]
                    currSUID[i] = temStr.replace(currSUID[i][0:strLen], newStr[0:strLen])
                    newStr = newStr[strLen:]
            newStudyiUID = '.'.join(currSUID)

            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
            time.sleep(0.5)
            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3]) + newStr
            time.sleep(0.3)
            newStr = newStr + ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3])
            currSUID = re.findall(r'[0-9]+', seriesiUID0)
            for i in range(len(currSUID) - 1):
                strLen = min(len(newStr), len(currSUID[i]))
                if strLen > 0:
                    temStr = currSUID[i][0:strLen]
                    currSUID[i] = temStr.replace(currSUID[i][0:strLen], newStr[0:strLen])
                    newStr = newStr[strLen:]
            newSeriesiUID = '.'.join(currSUID)
        else:
            newStudyiUID = studyiUID0
            newSeriesiUID = seriesiUID0

        # prepare new orientation, iop and patient position
        newOrient = self.dropmenu2.itemData(self.dropmenu2.currentIndex())
        if newOrient == 'HFS':
            newIOP = [1, 0, 0, 0, 1, 0]
        if newOrient == 'FFS':
            newIOP = [-1, 0, 0, 0, 1, 0]
        if newOrient == 'HFP':
            newIOP = [-1, 0, 0, 0, -1, 0]
        if newOrient == 'FFP':
            newIOP = [1, 0, 0, 0, -1, 0]
        if newOrient[0] != orient0[0]:  # if head and feet first was incorrect
            corrZ = -1
            corrX = -1
        else:
            corrZ = 1
            corrX = 1
        if newOrient[2] != orient0[2]:  # if supine and prone was incorrect
            corrY = -1
            corrX = -1
        else:
            corrY = 1
            corrX = 1

        # flip images if iop doesn't match patient orientation (instead the image is flipped to match unorthodox setting)
        needFlipLR = False
        needFlipUD = False
        if orientIsOrdinary:
            if orient0 == 'HFS':
                if iop0[0] < 0:
                    needFlipLR = True
                    corrX = -1*corrX
                if iop0[5] < 0:
                    needFlipUD = True
                    corrY = -1 * corrY
            if orient0 == 'FFS':
                if iop0[0] > 0:
                    needFlipLR = True
                    corrX = -1 * corrX
                if iop0[5] < 0:
                    needFlipUD = True
                    corrY = -1 * corrY
            if orient0 == 'HFP':
                if iop0[0] > 0:
                    needFlipLR = True
                    corrX = -1 * corrX
                if iop0[5] > 0:
                    needFlipUD = True
                    corrY = -1 * corrY
            if orient0 == 'FFP':
                if iop0[0] < 0:
                    needFlipLR = True
                    corrX = -1 * corrX
                if iop0[5] > 0:
                    needFlipUD = True
                    corrY = -1 * corrY

        # create save folder
        foldersave = folder + '_' + newOrient
        if not os.path.exists(foldersave):
            os.makedirs(foldersave)

        # create new SOP Instance UID (disambled) and new reference UID
        newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
        newSOPUID = re.findall(r'[0-9]+', sopiUID0)
        for i in range(len(newSOPUID) - 1, 0, -1):
            strLen = min(len(newStr), len(newSOPUID[i]))
            if strLen > 0:
                temStr = newSOPUID[i][-strLen:]
                newSOPUID[i] = temStr.replace(newSOPUID[i][-strLen:], newStr[-strLen:])
                newStr = newStr[0:-strLen]

        newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
        currSUID = re.findall(r'[0-9]+', forUID0)
        for i in range(len(currSUID) - 1, 0, -1):
            strLen = min(len(newStr), len(currSUID[i]))
            if strLen > 0:
                temStr = currSUID[i][-strLen:]
                currSUID[i] = temStr.replace(currSUID[i][-strLen:], newStr[-strLen:])
                newStr = newStr[0:-strLen]
        newFoRUID = '.'.join(currSUID)

        # start correction on image data
        suidOldList = []
        suidNewList = []
        for f in ff:
            ds = dicom.read_file(f)
            if ds.Modality == 'CT' or ds.Modality == 'MR':  # this would exclude RTSTRUCT, which doesn't have ImagePositionPatient
                ds.PatientPosition = newOrient
                ds.ImageOrientationPatient = newIOP
                ds.FrameOfReferenceUID = newFoRUID
                if needFlipLR:
                    arrayTemp = fliplr(ds.pixel_array)
                    ds.PixelData = arrayTemp.tostring()
                if needFlipUD:
                    arrayTemp = flipud(ds.pixel_array)
                    ds.PixelData = arrayTemp.tostring()
                ds.ImagePositionPatient[0] = corrX*ds.ImagePositionPatient[0]
                ds.ImagePositionPatient[1] = corrY*ds.ImagePositionPatient[1]
                ds.ImagePositionPatient[2] = corrZ*ds.ImagePositionPatient[2]
                ds.StudyInstanceUID = newStudyiUID
                ds.SeriesInstanceUID = newSeriesiUID
                suidOldList.append(ds.SOPInstanceUID)
                newSOPUID[-1] = str(int(newSOPUID[-1]) + 1)
                ds.SOPInstanceUID = '.'.join(newSOPUID)
                suidNewList.append(ds.SOPInstanceUID)
                fs = os.path.join(foldersave, os.path.basename(f))
                ds.save_as(fs)
            elif ds.Modality == 'RTSTRUCT':
                fstruct = f  # save to process later

        # correct struct file if available
        if 'fstruct' in vars():
            ds = dicom.read_file(fstruct)
            if ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID != forUID0:
                print('Input structure does not have same coordinate system as image')
                self.text1.clear()
                self.parent().statusBar().showMessage('Done')
                return
            ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = newFoRUID
            ds.StudyInstanceUID = newStudyiUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RefdSOPInstanceUID = newStudyiUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = newStudyiUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = newSeriesiUID
            # Referenced SOP UIDs don't need to match, but if they match in original file, will try to make them match...
            for ii in range(0,len(suidOldList)):  # update all the referenced CT image SOP numbers in the RTstruct header
                currSUID = ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].ReferencedSOPInstanceUID
                if currSUID in suidOldList:
                    idx = suidOldList.index(currSUID)
                    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].ReferencedSOPInstanceUID = suidNewList[idx]
                    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].RefdSOPInstanceUID = suidNewList[idx]
                else:
                    break
            ncontour = len(ds.ROIContourSequence)
            for ii in range(0,ncontour):
                ds.StructureSetROISequence[ii].ReferencedFrameOfReferenceUID = newFoRUID
                nslice_contour = len(ds.ROIContourSequence[ii].ContourSequence)
                for jj in range(0,nslice_contour):
                    currSUID = ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID
                    if currSUID in suidOldList:
                        idx = suidOldList.index(currSUID)
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID = suidNewList[idx]
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].RefdSOPInstanceUID = suidNewList[idx]
                    npts_contour = ds.ROIContourSequence[ii].ContourSequence[jj].NumberOfContourPoints
                    for kk in range(0,npts_contour):
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 0] = corrX*ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 0]
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 1] = corrY*ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 1]
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 2] = corrZ*ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 2]
            if 'SpecificCharacterSet' in ds:  # correct for character set for new dicom standard
                if ds.SpecificCharacterSet == 'Not Supplied':
                    ds.SpecificCharacterSet = 'ISO_IR 6'
            fs = os.path.join(foldersave, os.path.basename(fstruct))
            ds.save_as(fs)

        self.text1.clear()
        self.parent().statusBar().showMessage('Done')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # set background
        self.setWindowTitle('Correct dicom patient orientation')
        self.setStyleSheet('QWidget{background-color: white; font: 14px}')
        self.statusBar().showMessage('Ready')

        # set exit action
        ea = QAction('Exit', self)
        ea.setStatusTip('Exit')
        ea.setShortcut('Ctrl+q')
        ea.triggered.connect(qApp.quit)

        # set menu bar
        menu = self.menuBar()
        filemenu = menu.addMenu('File')
        filemenu.addAction(ea)

        # set main canvas
        mc = MainCanvas()
        self.setCentralWidget(mc)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())