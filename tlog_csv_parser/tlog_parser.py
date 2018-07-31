import sys
import os
import csv
from PyQt5.QtWidgets import (QWidget, QApplication, QAction,
                             QVBoxLayout, QLabel, QFileDialog,
                             QDesktopWidget, QMainWindow,
                             QPushButton, qApp, QHBoxLayout,
                             QListWidget, QShortcut, QTreeWidget,
                             QTreeWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from collections import defaultdict

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 900


class ParserGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        # Data structures
        self.outListSet = set()
        self.outParamDict = defaultdict(set)

        self.save_file = ""

        # ______Actions______
        setSaveLoc = QAction('&Save...', self)
        setSaveLoc.setShortcut('Ctrl+S')
        setSaveLoc.setStatusTip('Set Save Location and Name')
        setSaveLoc.triggered.connect(self.saveFile)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit Application')
        exitAction.triggered.connect(qApp.quit)

        # ______MenuBar______
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(setSaveLoc)
        fileMenu.addAction(exitAction)

        # ______Push Buttons______
        chooseLogBtn = QPushButton('Open log file...')
        chooseLogBtn.clicked.connect(self.openFile)
        parseBtn = QPushButton('Parse!')
        parseBtn.clicked.connect(self.parser)

        # ______Labels______
        paramLabel = QLabel('Log Parameters', self)
        outParamLabel = QLabel('Selected Parameters', self)

        # ______QTreeVWidget_________
        self.paramList = QTreeWidget(self)
        self.outList = QTreeWidget(self)

        # ______Actions______

        # Add and subtract items on double click
        self.paramList.itemDoubleClicked.connect(self.addParam)
        self.outList.itemDoubleClicked.connect(self.deleteParam)

        # Map return key to adding to second list
        self.addItem = QShortcut(QKeySequence(Qt.Key_Return),
                                 self.paramList)
        self.addItem.activated.connect(lambda: self.addParam(
                                       self.paramList.currentItem()))

        # Map delete key for removing from second list
        self.deleteItem = QShortcut(QKeySequence(Qt.Key_Delete),
                                    self.outList)
        self.deleteItem.activated.connect(lambda: self.deleteParam(
                                          self.outList.currentItem()))

        centralWidget = QWidget()

        # ______Layout______

        # Create horizontal box layout
        hbox1 = QHBoxLayout()
        hbox1.addWidget(paramLabel)
        hbox1.addWidget(outParamLabel)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.paramList)
        hbox2.addWidget(self.outList)

        # Create vertical box layout
        vbox = QVBoxLayout()
        vbox.addWidget(chooseLogBtn)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addWidget(parseBtn)

        centralWidget.setLayout(vbox)

        self.setCentralWidget(centralWidget)

        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.center()

        self.setWindowTitle('Mission Planner TLog Parser')
        # self.setWindowIcon(QIcon('web.png'))
        self.show()

        self.setupParams()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def openFile(self):
        error_message = "Bad file type or corrupted file."

        try:
            self.log_file = QFileDialog.getOpenFileName(self, 'Open file',
                                                        None)[0]
            self.log_chosen = 1
        except ValueError:
            QMessageBox.information(self, "Error", error_message,
                                 QMessageBox.Ok, QMessageBox.Ok)
        finally:
            if not self.log_file.lower().endswith(".csv"):
                QMessageBox.information(self, "Error", "Not a CSV file!", 
                                 QMessageBox.Ok, QMessageBox.Ok)
    
    def saveFile(self):
        self.save_file = QFileDialog.getSaveFileName(self, 'Save File')[0]
 
    def parser(self):

        header_row = []
        header_row.append("Timestamp")
        row = {"Timestamp": 0}

        # Check to see if save file name and location set
        # Otherwise, set to default directory and name
        if os.path.exists(os.path.dirname(self.save_file)):
            csvfile = open(self.save_file, "w")
        else:
            print(self.log_file)
            csvfile = open(self.log_file.split(".")[0] + "_parsed.csv", "w")

        for key in self.outParamDict:
            for item in self.outParamDict[key]:
                header_row.append(key + "." + item)
                row[key + "." + item] = 0

        csvwriter = csv.writer(csvfile, delimiter=",")
        csvwriter.writerow(header_row)

        try:
            with open (self.log_file, "r") as lf:
                for line in lf:
                    values = line.split(",")
                    # Timestamp
                    row["Timestamp"] = values[0]
                    for key in values:
                        if key in self.outParamDict:
                            for item in self.outParamDict[key]:
                                    index = values.index(item) + 1
                                    row[key + "." + item] = values[index]
                    csvwriter.writerow(row.values())

            QMessageBox.information(self, "Info", "Finished!",
                         QMessageBox.Ok, QMessageBox.Ok)
        except UnicodeDecodeError:
            QMessageBox.information(self, "Error", "Bad file type or corrupted file", QMessageBox.Ok, QMessageBox.Ok)    

    def setupParams(self):
        parent_text = ""

        with open("tlog_params.txt") as f:
            for line in f:
                values = line.rstrip().split(".")

                if values[1].lstrip("_") != parent_text:
                    child_text = values[0].rstrip("_")
                    parent_text = values[1].lstrip("_")
                    parent = QTreeWidgetItem(self.paramList)
                    parent.setText(0, parent_text)
                    child = QTreeWidgetItem(parent)
                    child.setText(0, child_text)
                else:
                    child_text = values[0].rstrip("_")
                    child = QTreeWidgetItem(parent)
                    child.setText(0, child_text)

        self.paramList.show()

    def addParam(self, parameter):
            # Check that item has a parent (is a child)
            if parameter.parent():
                if parameter.parent().text(0) not in self.outParamDict:
                    self.parent = QTreeWidgetItem(self.outList)
                    self.parent.setText(0, parameter.parent().text(0))
                    self.child = QTreeWidgetItem(self.parent)
                    self.child.setText(0, parameter.text(0))
                # Check to see if child is not already in outParamDict values
                elif not any(parameter.text(0) in values for values in self.outParamDict.values()):
                    parent_text = parameter.parent().text(0)
                    parent_item = self.outList.findItems(parent_text, Qt.MatchContains)[0]
                    self.child = QTreeWidgetItem(parent_item)
                    self.child.setText(0, parameter.text(0))    

                self.outParamDict[parameter.parent().text(0)].add(parameter.text(0))

            # If it's a parent item
            else:
                child_count = parameter.childCount()
                if parameter.text(0) not in self.outParamDict:
                    self.parent = QTreeWidgetItem(self.outList)
                    self.parent.setText(0, parameter.text(0))

                    # Get number of children, iterate through all children and add them to the outList
                    for i in range(0, child_count):
                        child = QTreeWidgetItem(self.parent)
                        child.setText(0, parameter.child(i).text(0))
                        self.outParamDict[parameter.text(0)].add(parameter.child(i).text(0))

                else:
                    # Clear current contents
                    for i in reversed(range(child_count)):
                        self.parent.removeChild(self.parent.child(i))

                    # Rewrite all children in correct order
                    for i in range(0, child_count):
                        child = QTreeWidgetItem(self.parent)
                        child.setText(0, parameter.child(i).text(0))
                        self.outParamDict[parameter.text(0)].add(parameter.child(i).text(0))

            print(self.outParamDict)

    def deleteParam(self, parameter):
        # If it has a parent (is a child)
        if parameter.parent():
            self.outParamDict[parameter.parent().text(0)].remove(parameter.text(0))
            parameter.parent().removeChild(parameter)

        else:
            # If it's a parent
            root = self.outList.invisibleRootItem()
            root.removeChild(parameter)
            del self.outParamDict[parameter.text(0)]

        print(self.outParamDict)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    gui = ParserGUI()
    sys.exit(app.exec_())