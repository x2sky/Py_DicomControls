# -*- linkRTStruct.py -*-
"""
link the RT struct set to the current CT set
version 0.0
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
        label2 = QLabel('Import RT Struct file')
        self.text2 = QLineEdit()
        button2 = QPushButton('Browse')
        button5 = QPushButton('&Link')

        # layout of widgets
        qgl = QGridLayout()
        qgl.addWidget(label1, 0, 0, 1, 6)
        qgl.addWidget(self.text1, 1, 0, 1, 6)
        qgl.addWidget(button1, 1, 6)
        qgl.addWidget(label2, 2, 0, 1, 6)
        qgl.addWidget(self.text2, 3, 0, 1, 6)
        qgl.addWidget(button2, 3, 6)
        qgl.addWidget(button5, 4, 3, 1, 2)
        self.setLayout(qgl)

        # define functions of texts and buttons
        button1.clicked.connect(lambda: self.BrowseDir('Select folder of reference CT', self.text1))
        button2.clicked.connect(lambda: self.BrowseFile('Select RT Struct file', self.text2))
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

    def BrowseFile(self, title, activetext):
        global basefolder
        if 'basefolder' in globals():
            if os.path.exists(basefolder):
                rf = QFileDialog.getOpenFileName(self, title, basefolder, 'dicom files (*.dcm);; all files (*.*)')
            else:
                rf = QFileDialog.getOpenFileName(self, title, QDir.current().path(), 'dicom files (*.dcm);; all files (*.*)')
        else:
            rf = QFileDialog.getOpenFileName(self, title, QDir.current().path(), 'dicom files (*.dcm);; all files (*.*)')
        rf = rf[0]
        if os.path.isfile(rf):
            basefolder = os.path.dirname(rf)
            activetext.setText(rf)
            self.parent().statusBar().showMessage('ready')

    def CheckInputs(self):
        if not os.path.exists(self.text1.text()):
            self.parent().statusBar().showMessage('Folder of referenced CT does not exist')
            return

        if not os.path.isfile(self.text2.text()):
            self.parent().statusBar().showMessage('RT struct file does not exist')
            return

        self.LinkFile()

    def LinkFile(self):
        """
        This is the main function that links the RT strcut to the reference CT
        """
        self.parent().statusBar().showMessage('Thinking and running')

        # obtain tag and parameters from the reference CT
        folderref = self.text1.text()
        ffref = glob.glob(os.path.join(folderref, 'CT*.dcm'))
        nslice = len(ffref)
        if nslice<2:
            self.parent().statusBar().showMessage('No dicom files with file name CT*.dcm in referenced CT folder')
            return
        ds = dicom.read_file(ffref[0])
        newforUID = ds.FrameOfReferenceUID
        ssIUID = ds.StudyInstanceUID
        serUID = ds.SeriesInstanceUID
        ptID = ds.PatientID
        ptName = ds.PatientName
        ptBD = ds.PatientBirthDate
        ptSx = ds.PatientSex
        med = ds.ReferringPhysicianName

        attList = []
        suidList = []
        for f in ffref:
            ds = dicom.read_file(f)
            if ds.Modality == 'CT':  # this would exclude RTSTRUCT, which doesn't have ImagePositionPatient
                currSOPUID = ds.SOPInstanceUID
                splitUID = currSOPUID.split('.')
                currCounter =  splitUID[-1] #  use last part of UID as counter
                currz = '{:.2f}'.format(ds.ImagePositionPatient[2])
                suidList.append(currSOPUID)
                attList.append((currCounter, currSOPUID, currz)) #  1st attribute is SOP UID, 2nd is z coordinate
        #reorder the attibute list based on the SOP UID
        attListSorted = sorted(attList, key=lambda att: int(att[0]))

        # create file name to save
        rsfile = self.text2.text()
        file = os.path.basename(rsfile)
        [fn, fext] = os.path.splitext(file)
        pn = os.path.dirname(rsfile)
        filesave = os.path.join(pn,'linked_' + fn + fext)
        if os.path.isfile(filesave):
            cnt = 1
            while os.path.isfile(filesave):
                filesave = os.path.join(pn,'linked_' + fn + str(cnt) + fext)
                cnt = cnt + 1

        # correct the RT Struct information
        ds = dicom.read_file(rsfile)
        if len(ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence) != nslice:
            self.parent().statusBar().showMessage('Number of slices in CT different from number of slices specified in RT struct')
            return
        ds.PatientID = ptID
        ds.PatientName = ptName
        ds.PatientBirthDate = ptBD
        ds.PatientSex = ptSx
        ds.ReferringPhysicianName = med
        ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID = newforUID
        ds.StudyInstanceUID = ssIUID
        ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RefdSOPInstanceUID = ssIUID
        ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].ReferencedSOPInstanceUID = ssIUID
        ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].SeriesInstanceUID = serUID
        # Referenced SOP UIDs don't need to match, will try to make them match anyway...
        for ii in range(0,nslice):  # update all the referenced CT image SOP numbers in the RTstruct header
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].ReferencedSOPInstanceUID = attListSorted[ii][1]
            ds.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[0].RTReferencedSeriesSequence[0].ContourImageSequence[ii].RefdSOPInstanceUID = attListSorted[ii][1]
        ncontour = len(ds.ROIContourSequence)
        for ii in range(0,ncontour):
            ds.StructureSetROISequence[ii].ReferencedFrameOfReferenceUID = newforUID
            nslice_contour = len(ds.ROIContourSequence[ii].ContourSequence)
            for jj in range(0,nslice_contour):
                currSUID = ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID
                if currSUID not in suidList:
                    currz = ds.ROIContourSequence[ii].ContourSequence[jj].ContourData[2]
                    for kk in range(0, nslice):
                        if abs(currz - float(attListSorted[kk][2])) < 0.01:
                            ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].ReferencedSOPInstanceUID = attListSorted[kk][1]
                            ds.ROIContourSequence[ii].ContourSequence[jj].ContourImageSequence[0].RefdSOPInstanceUID = attListSorted[kk][1]
        ds.save_as(filesave)

        self.text1.clear()
        self.text2.clear()
        self.parent().statusBar().showMessage('Ready')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # set background
        self.setWindowTitle('Link the RT Struct set to the current CT set')
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