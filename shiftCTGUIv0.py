# -*- ShiftCTGUIv0.py -*-
"""
Shift the registered CT to reference CT coordinate based on input translation
Created on Wed May 25 12:34:11 2016

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
        #define directory texts, push button and labels
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

        #layout of widgets
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

        #define functions of texts and buttons
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

        ##obtain info from reference CT set
        folderref = self.text1.text()
        ffref = glob.glob(os.path.join(folderref, 'CT*.dcm'))
        if len(ffref)<2:
            self.parent().statusBar().showMessage('No dicom files with file name CT*.dcm in referenced CT folder')
            return
        ds = dicom.read_file(ffref[0])  # read the first image
        r_ref1 = ds.ImagePositionPatient  # obtain coordinate of first image
        ds = dicom.read_file(ffref[-1])  # read the last image
        r_ref2 = ds.ImagePositionPatient  # obtain coordinate of last image
        x0_ref = r_ref2[0]  # top corner x
        y0_ref = r_ref2[1]  # top corner y
        zM_ref = 0.5 * (r_ref1[2] + r_ref2[2])  # mid point z
        newforUID = ds.FrameOfReferenceUID  # FoR of the original CT set

        ##obtain info from registered CT set
        folderreg = self.text2.text()
        ffreg = glob.glob(os.path.join(folderreg, 'CT*.dcm'))
        if len(ffreg)<2:
            self.parent().statusBar().showMessage('No dicom files with file name CT*.dcm in registered CT folder')
            return
        ds = dicom.read_file(ffreg[0])  # read the first image
        r_reg1 = ds.ImagePositionPatient  # obtain coordinate of first image
        ds = dicom.read_file(ffreg[-1])  # read the last image
        r_reg2 = ds.ImagePositionPatient  # obtain coordinate of last image
        x0_reg = r_reg2[0]  # top corner x
        y0_reg = r_reg2[1]  # top corner y
        zM_reg = 0.5 * (r_reg1[2] + r_reg2[2])  # mid point z

        ##shift of registered CT to coordinates of reference CT:
        xsh = float(self.text31.text()) + x0_ref - x0_reg
        ysh = -float(self.text32.text()) + y0_ref - y0_reg
        zsh = -float(self.text33.text()) + (zM_ref - zM_reg)

        ##create new study and series instance UID#
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
        else:
            ssIUID = ds.StudyInstanceUID


        ##create save folder
        foldersave = folderreg + '_Shifted'
        if not os.path.exists(foldersave):
            os.makedirs(foldersave)
        else:
            cnt = 1
            while os.path.exists(foldersave):
                foldersave = folderreg + '_Shifted' + str(cnt)
                cnt = cnt + 1
            os.makedirs(foldersave)

        ##create new SOP Instance UID
        newStr = ''.join(re.findall(r'[0-9]+', str(datetime.datetime.today())))
        currSUID = re.findall(r'[0-9]+', ds.SOPInstanceUID)
        for i in range(len(currSUID) - 1, 0, -1):
            strLen = min(len(newStr), len(currSUID[i]))
            if strLen > 0:
                temStr = currSUID[i][-strLen:]
                currSUID[i] = temStr.replace(currSUID[i][-strLen:], newStr[-strLen:])
                newStr = newStr[0:-strLen]
        ##perform shift to files in the directory
        ffreg = glob.glob(os.path.join(folderreg, '*.dcm'))
        for f in ffreg:
            ds = dicom.read_file(f)
            if hasattr(ds, 'ImagePositionPatient'):
                ds.ImagePositionPatient[0] = ds.ImagePositionPatient[0] + xsh
                ds.ImagePositionPatient[1] = ds.ImagePositionPatient[1] + ysh
                ds.ImagePositionPatient[2] = ds.ImagePositionPatient[2] + zsh
                ds.FrameOfReferenceUID = newforUID
                ds.StudyInstanceUID = ssIUID
                ds.SeriesInstanceUID = ssIUID
                currSUID[-1] = str(int(currSUID[-1]) + 1)
                ds.SOPInstanceUID = '.'.join(currSUID)
                fs = os.path.join(foldersave, os.path.basename(f))
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
        #set background
        self.setWindowTitle('Apply shift to registered CT to coordinate of referenced CT')
        self.setStyleSheet('QWidget{background-color: white; font: 14px}')
        self.statusBar().showMessage('Ready')

        # set exit action
        ea = QAction('Exit', self)
        ea.setStatusTip('Exit')
        ea.setShortcut('Ctrl+q')
        ea.triggered.connect(qApp.quit)

        #set menu bar
        menu = self.menuBar()
        filemenu = menu.addMenu('File')
        filemenu.addAction(ea)

        #set main canvas
        mc = MainCanvas()
        self.setCentralWidget(mc)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())