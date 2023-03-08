from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import matplotlib.pyplot as pyplot
from matplotlib.widgets import MultiCursor

import json

import os
import sys

from highlighter import VHDLHighlighter
from line_number import QTextEditHighlighter
import error

import cli
import vcd_dump

from  typing import List, Dict

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Editor")
        self.setWindowIcon(QIcon("./res/images/vhdl.png"))
        self.setGeometry(100, 100, 800, 400)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.config = {}
        
        self.buffer = ''
        self.editor = QTextEditHighlighter()
        self.errorbox = QListWidget()
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.myFont = QFont("Consolas", 10)
        self.editor.setFont(self.myFont)
        highlight = VHDLHighlighter(self.editor.document())
        # font = QFontDatabase.systemFont()
        # font.setPointSize(11)
        # self.editor.setFont(font)
        if (not os.path.exists('./editor.conf')):
            with open('./editor.conf','w') as conf:
                self.config["lastActiveFile"] = "./"
                conf.write(str(self.config))
        conf_file = open('./editor.conf','r+')
        # configs = conf_file.read()
        try:
            self.config = eval(conf_file.read())
        except:
            self.config = {}
        try:
            self.config["lastActiveFile"]
        except:
            self.config["lastActiveFile"] = "./"
            conf_file.write(str(self.config))
        conf_file.close()

        self.filePath = self.config["lastActiveFile"]
        if self.filePath != "./":
            self.open_file(True)
        else:
            self.new_file()

        self.errorbox.addItem(QListWidgetItem("No Errors"))
        
        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        layout.addWidget(self.errorbox)

        self.container = QWidget(self)
        self.container.setLayout(layout)
        self.setCentralWidget(self.container)
        # self.container.setMouseTracking(True)
        # self.setMouseTracking(True)

        self.status = QStatusBar(self)
        self.setStatusBar(self.status)

        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(14,14))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        self.add_action(file_toolbar, file_menu, "New File",'document-new.svg',"Ctrl+n", self.new_file)
        self.add_action(file_toolbar, file_menu, "Open File",'document-open.svg',"Ctrl+o", self.open_file)
        self.add_action(file_toolbar, file_menu, "Save File",'document-save.svg',"Ctrl+s", self.save_file)
        self.add_action(file_toolbar, file_menu, "Save File As",'document-save-as.svg',"Ctrl+Shift+s", self.save_file_as)
        self.add_action(file_toolbar, file_menu, "Compile",'builder-build-symbolic.svg',"Ctrl+Shift+s", self.compile)
        self.add_action(file_toolbar, file_menu, "Simulate",'builder-run-start-symbolic.svg',"Ctrl+Shift+s", self.execute)

        self.update_title()
        self.show()
        self.arches = []
    
    def add_action(self, file_toolbar: QToolBar, file_menu: QMenu, name, iconPath, hotkey, actionHandler):
        action = QAction(QIcon(os.path.join('res/images',iconPath)),  name , self)
        action.setStatusTip(name)
        action.triggered.connect(actionHandler)
        action.setShortcut(QKeySequence(QCoreApplication.translate("QKeySequence",hotkey)))
        file_menu.addAction(action)
        file_toolbar.addAction(action)
        

    def new_file(self):
        if self.filePath is not None and self.filePath != './':
            self.file_close()
            self.editor.clear()
            self.buffer = ''
            self.filePath = './'
            self.update_title()


    def open_file(self, autoOpen: bool = False):
        if not autoOpen:
            self.filePath, _ = QFileDialog.getOpenFileName(self, "Open File ", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
        if self.filePath:
            with open(self.filePath, 'r') as f:
                text = f.read()
                self.editor.setPlainText(text)
                self.buffer = text
                self.update_title()
                self.config["lastActiveFile"] = self.filePath

    def save_file(self):
        if not self.filePath or self.filePath == './':
            self.filePath, _ = QFileDialog.getSaveFileName(self, "Save File ", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
        if self.filePath:
            with open(self.filePath, 'w') as f:
                text = self.editor.toPlainText()
                self.buffer = text
                f.write(text)
                self.update_title()
                self.config["lastActiveFile"] = self.filePath

    def save_file_as(self):
        self.filePath, _ = QFileDialog.getSaveFileName(self, "Save File As", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
        if self.filePath:
            with open(self.filePath, 'w') as f:
                text = self.editor.toPlainText()
                self.buffer  = text
                f.write(text)
                self.update_title()
                self.config["lastActiveFile"] = self.filePath

    def update_title(self):
        self.setWindowTitle("%s - VHDL Editor" %(os.path.basename(self.filePath) if self.filePath and self.filePath != './' else "Untitled - VHDL Editor"))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.file_close()
        return super().closeEvent(event)

    def file_close(self):
        if self.buffer != self.editor.toPlainText():
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Do you want to save the changes to this file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.save_file()

    def __del__(self):
        with open('./editor.conf', 'w') as conf_file:
            conf_file.write(str(self.config))

    # def contextMenuEvent(self, e):
    #     context= QMenu(self)
    #     context.addAction(QAction("test 1", self))
    #     context.addAction(QAction("test 2", self))
    #     context.addAction(QAction("test 3", self))
    #     context.exec(e.globalPos())

    
    def compile(self):
        self.errorbox.clear()
        error.errno.clear()
        self.save_file()
        print("Trying to compile", self.config["lastActiveFile"])
        self.arches = cli.compile(self.config["lastActiveFile"])
        

        def errorbox_error_clicked(item):
            index = self.errorbox.row(item)
            print("Clicked", index)

            # errno has the row and col get them
            # here set the cursor to error place
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)

            row, col = cli.error.errno[index].line - 1, cli.error.errno[index].col - 1
            print(row, col)
            for _ in range(row):
                self.editor.moveCursor(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor)
            for _ in range(col):
                self.editor.moveCursor(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor)
            self.editor.setFocus()

        self.errorbox.itemClicked.connect(errorbox_error_clicked)
        self.errorbox.setResizeMode(QListView.ResizeMode.Adjust)
        self.errorbox.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.errorbox.setMaximumHeight(100)
        self.errorbox.setStyleSheet("::item {border: 1px solid black} ::item:hover {background: rgba(0,0, 100, 0.3)} ::item:selected {color: black; background:rgba(0,100,0, 0.3)}")

        for i in cli.error.errno:
            self.errorbox.addItem(f"ERROR {i.line}:{i.col} {i.msg}")
            row, col = i.line - 1, i.col - 1
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)
            for _ in range(row):
                self.editor.moveCursor(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor)
            for _ in range(col):
                self.editor.moveCursor(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor)
            self.editor.moveCursor(QTextCursor.MoveOperation.EndOfWord, QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(65,65,127,127))
            self.editor.textCursor().setCharFormat(fmt)


    def execute(self):
        cli.execute(self.arches)
        times = [] # time steps 0 1 2 3 4
        values: List[List[str]] = [] # [a: [], b: [], g: []]
        signals  = [] # a, b, g

        for v in vcd_dump.variable_values.keys():
            print("Keys: ", v)
            values.append([])
            signals.append(v)


        first = True
        for time in vcd_dump.values_over_time:
            # print("time", time[0])
            times.append(time[0])
            if first:
                first = False
            else:
                times.append(time[0])
            for index, value in enumerate(time[1]):
                # print("v:", value, end=" ")
                values[index].append(value)
                values[index].append(value)
        for v in values:
            v.pop()
        
        figure, axis = pyplot.subplots(len(signals))
        for i, v in enumerate(axis):
            axis[i].plot(times, values[i])
        multi = MultiCursor(figure.canvas, tuple(axis), color='r', lw=1)
        pyplot.show()
        # vcd_dump.output.close()
        vcd_dump.VcdWriter = None

        vcd_dump.current_time = 0
        # vcd_dump.variables = {}
        vcd_dump.variable_values = {}
        vcd_dump.values_over_time = []
        
