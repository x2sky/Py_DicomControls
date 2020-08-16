# -*- ShiftCTGUI.py -*-
"""
Shift the registered CT to reference CT coordinate based on input translation
version 1.0
add feature that also shifts RT structure
updated on 5th July 2016

@author: Becket Hui
"""
import datetime, dicom, glob, os, re, sys, time
from PyQt5.QtWidgets import QAction, qApp, QApplication, QCheckBox, QFileDialog, QGridLayout, QLineEdit, QLabel, \
    QMainWindow, QPushButton, QWidget
from PyQt5.QtCore import QDir

class MainCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # define directory texts, push button and labels
        label1 = QLabel('Import directory of referenced CT set')
        self.text1 = QLineEdit()
        button1 = QPushButton('Browse')
        label2 = QLabel('Import directory of registered CT set')
        self.text2 = QLineEdit()
        button2 = QPushButton('Browse')
        label30 = QLabel('Effective translation (mm): (as in velocity)')
        label31 = QLabel('x:')
        self.text31 = QLineEdit()
        self.text31.setText('0')
        label32 = QLabel('y:')
        self.text32 = QLineEdit()
        self.text32.setText('0')
        label33 = QLabel('z:')
        self.text33 = QLineEdit()
        self.text33.setText('0')
        self.cbox4 = QCheckBox()
        self.cbox4.setChecked(True)
        label41 = QLabel('Create new study & series UID')
        button5 = QPushButton('&Shift')

        # layout of widgets
        qgl = QGridLayout()
        qgl.addWidget(label1, 0, 0, 1, 6)
        qgl.addWidget(self.text1, 1, 0, 1, 6)
        qgl.addWidget(button1, 1, 6)
        qgl.addWidget(label2, 2, 0, 1, 6)
        qgl.addWidget(self.text2, 3, 0, 1, 6)
        qgl.addWidget(button2, 3, 6)
        qgl.addWidget(label30, 4, 0, 1, 6)
        qgl.addWidget(label31, 5, 0)
        qgl.addWidget(self.text31, 5, 1)
        qgl.addWidget(label32, 5, 2)
        qgl.addWidget(self.text32, 5, 3)
        qgl.addWidget(label33, 5, 4)
        qgl.addWidget(self.text33, 5, 5)
        qgl.addWidget(self.cbox4, 6, 0)
        qgl.addWidget(label41, 6, 1, 1, 3)
        qgl.addWidget(button5, 7, 6)
        self.setLayout(qgl)

        # define functions of texts and buttons
        button1.clicked.connect(lambda: self.BrowseDir('Select folder of reference CT', self.text1))
        button2.clicked.connect(lambda: self.BrowseDir('Select folder of registered CT', self.text2))
        button5.clicked.connect(self.CheckInputs)

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
            basefolder = os.path.dirname(rd)
            activetext.setText(rd)
            self.parent().statusBar().showMessage('ready')

    def CheckInputs(self):
        if not os.path.exists(self.text1.text()):
            self.parent().statusBar().showMessage('Folder of referenced CT does not exist')
            return

        if not os.path.exists(self.text2.text()):
            self.parent().statusBar().showMessage('Folder of registered folder does not exist')
            return

        try:
            float(self.text31.text())
        except:
            self.parent().statusBar().showMessage('Shift in x is not a float variable')
            return
        try:
            float(self.text32.text())
        except:
            self.parent().statusBar().showMessage('Shift in y is not a float variable')
            return
        try:
            float(self.text33.text())
        except:
            self.parent().statusBar().showMessage('Shift in z is not a float variable')
            return

        self.ShiftCT()

    def ShiftCT(self):
        """
        This is the main function that performs the shift on the registered CT and save to new files
        """
        self.parent().statusBar().showMessage('Thinking and running')

        # obtain info from reference CT set
        folderref = self.text1.text()
        ffref = glob.glob(os.path.join(folderref, 'CT*'))
        if len(ffref)<2:
            self.parent().statusBar().showMessage('No dicom files with file name CT* in referenced CT folder')
            return
        # find the z range of referenced CT slices
        ds = dicom.read_file(ffref[0])  # read the first image
        zref_min = ds.ImagePositionPatient[2]
        zref_max = ds.ImagePositionPatient[2]
        for f in ffref:
            ds = dicom.read_file(f)  # read the image
            r_ref = ds.ImagePositionPatient  # obtain coordinate of first image
            if zref_min > r_ref[2]:
                zref_min = r_ref[2]
                x0_ref = r_ref[0]  # top corner x
                y0_ref = r_ref[1]  # top corner y
                newforUID = ds.FrameOfReferenceUID  # FoR of the original CT set
                FOV_ref = float(ds.ReconstructionDiameter)  # FOV length
            if zref_max < r_ref[2]:
                zref_max = r_ref[2]
                x0_ref = r_ref[0]  # top corner x
                y0_ref = r_ref[1]  # top corner y
                newforUID = ds.FrameOfReferenceUID  # FoR of the original CT set
                FOV_ref = float(ds.ReconstructionDiameter)  # FOV length
        zM_ref = 0.5 * (zref_min + zref_max)  # mid point z
        xM_ref = x0_ref + 0.5 * FOV_ref  # mid point x
        yM_ref = y0_ref + 0.5 * FOV_ref  # mid point y

        # obtain info from registered CT set
        folderreg = self.text2.text()
        ffreg = glob.glob(os.path.join(folderreg, 'CT*'))
        if len(ffreg)<2:
            self.parent().statusBar().showMessage('No dicom files with file name CT* in registered CT folder')
            return
        nslice = len(ffreg)
        # find the z range of referenced CT slices
        ds = dicom.read_file(ffreg[0])  # read the first image
        zreg_min = ds.ImagePositionPatient[2]
        zreg_max = ds.ImagePositionPatient[2]
        for f in ffreg:
            ds = dicom.read_file(f)  # read the image
            r_reg = ds.ImagePositionPatient  # obtain coordinate of first image
            if zreg_min > r_reg[2]:
                zreg_min = r_reg[2]
                x0_reg = r_reg[0]  # top corner x
                y0_reg = r_reg[1]  # top corner y
                FOV_reg = float(ds.ReconstructionDiameter)  # FOV length
            if zreg_max < r_reg[2]:
                zreg_max = r_reg[2]
                x0_reg = r_reg[0]  # top corner x
                y0_reg = r_reg[1]  # top corner y
                FOV_reg = float(ds.ReconstructionDiameter)  # FOV length
        zM_reg = 0.5 * (zreg_min + zreg_max)  # mid point z
        xM_reg = x0_reg + 0.5 * FOV_reg  # mid point x
        yM_reg = y0_reg + 0.5 * FOV_reg  # mid point y

        # shift of registered CT to coordinates of reference CT:
        xsh = float(self.text31.text()) + (xM_ref - xM_reg)
        ysh = -float(self.text32.text()) + (yM_ref - yM_reg)
        zsh = -float(self.text33.text()) + (zM_ref - zM_reg)

        # create new study and series instance UID#
        if self.cbox4.isChecked():
            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
            time.sleep(0.5)
            newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3]) + newStr
            time.sleep(0.3)
            newStr = newStr + ''.join(re.findall(r'[0-9]+', str(datetime.datetime.now().time()))[3])
            currSUID = re.findall(r'[0-9]+', ds.StudyInstanceUID)
            for i in range(len(currSUID) - 1):
                strLen = min(len(newStr), len(currSUID[i]))
                if strLen > 0:
                    temStr = currSUID[i][0:strLen]
                    currSUID[i] = temStr.replace(currSUID[i][0:strLen], newStr[0:strLen])
                    newStr = newStr[strLen:]
            ssIUID = '.'.join(currSUID)
            serUID = ssIUID
        else:
            ssIUID = ds.StudyInstanceUID
            serUID = ds.SeriesInstanceUID

        # create save folder
        foldersave = folderreg + '_Shifted'
        if not os.path.exists(foldersave):
            os.makedirs(foldersave)
        else:
            cnt = 1
            while os.path.exists(foldersave):
                foldersave = folderreg + '_Shifted' + str(cnt)
                cnt = cnt + 1
            os.makedirs(foldersave)

        # create new SOP Instance UID
        newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
        currSUID = re.findall(r'[0-9]+', ds.SOPInstanceUID)
        for i in range(len(currSUID) - 1, 0, -1):
            strLen = min(len(newStr), len(currSUID[i]))
            if strLen > 0:
                temStr = currSUID[i][-strLen:]
                currSUID[i] = temStr.replace(currSUID[i][-strLen:], newStr[-strLen:])
                newStr = newStr[0:-strLen]

        # perform shift to CT and dose files in the directory
        ffreg = glob.glob(os.path.join(folderreg, '*'))
        suidOldList = []
        suidNewList = []
        for f in ffreg:
            ds = dicom.read_file(f)
            if ds.Modality == 'CT':  # this would exclude RTSTRUCT, which doesn't have ImagePositionPatient
                ds.ImagePositionPatient[0] = ds.ImagePositionPatient[0] + xsh
                ds.ImagePositionPatient[1] = ds.ImagePositionPatient[1] + ysh
                ds.ImagePositionPatient[2] = ds.ImagePositionPatient[2] + zsh
                ds.SliceLocation = ds.ImagePositionPatient[2] + zsh
                ds.FrameOfReferenceUID = newforUID
                ds.StudyInstanceUID = ssIUID
                ds.SeriesInstanceUID = serUID
                currSUID[-1] = str(int(currSUID[-1]) + 1)
                suidOldList.append(ds.SOPInstanceUID)
                ds.SOPInstanceUID = '.'.join(currSUID)
                suidNewList.append(ds.SOPInstanceUID)
                fs = os.path.join(foldersave, os.path.basename(f))
                ds.save_as(fs)
            elif ds.Modality == 'RTDOSE':
                ds.ImagePositionPatient[0] = ds.ImagePositionPatient[0] + xsh
                ds.ImagePositionPatient[1] = ds.ImagePositionPatient[1] + ysh
                ds.ImagePositionPatient[2] = ds.ImagePositionPatient[2] + zsh
                ds.FrameOfReferenceUID = newforUID
                ds.StudyInstanceUID = ssIUID
                ds.SeriesInstanceUID = serUID
                # may not need to used new SOP instance UID for dose
                # currSUID[-1] = str(int(currSUID[-1]) + 1)
                # ds.SOPInstanceUID = '.'.join(currSUID)
                fs = os.path.join(foldersave, os.path.basename(f))
                ds.save_as(fs)
            elif ds.Modality == 'RTSTRUCT':
                fstruct = f  # save to process later

        if 'fstruct' in vars():
            ds = dicom.read_file(fstruct)
            if len(ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence) != nslice:
                self.parent().statusBar().showMessage('Number of slices in CT different from number of slices specified in RT struct')
                return
            ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = newforUID
            ds.StudyInstanceUID = ssIUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RefdSOPInstanceUID = ssIUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = ssIUID
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = serUID
            # Referenced SOP UIDs don't need to match, but if they match in original file, will try to make them match...
            for ii in range(0,nslice):  # update all the referenced CT image SOP numbers in the RTstruct header
                currSUID = ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].ReferencedSOPInstanceUID
                if currSUID in suidOldList:
                    idx = suidOldList.index(currSUID)
                    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].ReferencedSOPInstanceUID = suidNewList[idx]
                    ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].RefdSOPInstanceUID = suidNewList[idx]
                else:
                    break
            ncontour = len(ds.ROIContourSequence)
            for ii in range(0,ncontour):
                ds.StructureSetROISequence[ii].ReferencedFrameOfReferenceUID = newforUID
                nslice_contour = len(ds.ROIContourSequence[ii].ContourSequence)
                for jj in range(0,nslice_contour):
                    currSUID = ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID
                    if currSUID in suidOldList:
                        idx = suidOldList.index(currSUID)
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID = suidNewList[idx]
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].RefdSOPInstanceUID = suidNewList[idx]
                    npts_contour = ds.ROIContourSequence[ii].ContourSequence[jj].NumberOfContourPoints
                    for kk in range(0,npts_contour):
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 0] = ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 0] + xsh
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 1] = ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 1] + ysh
                        ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 2] = ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[kk * 3 + 2] + zsh
            fs = os.path.join(foldersave, os.path.basename(fstruct))
            ds.save_as(fs)

        self.text1.clear()
        self.text2.clear()
        self.text31.setText('0')
        self.text32.setText('0')
        self.text33.setText('0')
        self.parent().statusBar().showMessage('Ready')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # set background
        self.setWindowTitle('Apply shift to registered CT to coordinate of referenced CT')
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