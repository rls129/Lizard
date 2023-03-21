from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import matplotlib.pyplot as pyplot
from matplotlib.widgets import MultiCursor

import os
import sys

from highlighter import VHDLHighlighter
from line_number import QTextEditHighlighter
import error

import cli
import vcd_dump

from  typing import List, Union

class MyMultiCursor(MultiCursor):
    def __init__(self, canvas, axes, useblit=True, horizOn=[], vertOn=[], xPos= None, **lineprops):
        super(MyMultiCursor, self).__init__(canvas, axes, useblit=useblit, horizOn=False, vertOn=False, **lineprops)

        self.horizAxes = horizOn
        self.vertAxes = vertOn

        if len(horizOn) > 0:
            self.horizOn = True
        if len(vertOn) > 0:
            self.vertOn = True

        xmid = xPos
        if xPos == None:
            xmin, xmax = axes[-1].get_xlim()
            xmid = 0.5 * (xmin + xmax)

        ymin, ymax = axes[-1].get_ylim()
        ymid = 0.5 * (ymin + ymax)

        self.vlines = [ax.axvline(xmid, visible=False, **lineprops) for ax in self.vertAxes]
        self.hlines = [ax.axhline(ymid, visible=True, **lineprops) for ax in self.horizAxes]

    def updatex(self,xPos,  **lineprops):
        for line in self.vlines:
            line.x = int(xPos)

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
        self.errorbox.setResizeMode(QListView.ResizeMode.Adjust)
        self.errorbox.setSizeAdjustPolicy(QListView.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.errorbox.setMaximumHeight(100)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.myFont = QFont("Consolas", 10)
        self.editor.setFont(self.myFont)
        self.editor.setTabStopDistance(QFontMetricsF(self.editor.font()).horizontalAdvance(' ') * 4)
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

        run_toolbar = QToolBar("Run")
        run_toolbar.setIconSize(QSize(14,14))
        self.addToolBar(run_toolbar)
        run_menu = self.menuBar().addMenu("&Run")

        self.add_action(file_toolbar, file_menu, "New File",'document-new.svg',"Ctrl+n", self.new_file)
        self.add_action(file_toolbar, file_menu, "Open File",'document-open.svg',"Ctrl+o", self.open_file)
        self.add_action(file_toolbar, file_menu, "Save File",'document-save.svg',"Ctrl+s", self.save_file)
        self.add_action(file_toolbar, file_menu, "Save File As",'document-save-as.svg',"Ctrl+Shift+s", self.save_file_as)
        self.add_action(run_toolbar, run_menu, "Compile",'builder-build-symbolic.svg',"Ctrl+Shift+b", self.compile)
        self.add_simulation_time_spin_box(run_toolbar)
        self.add_action(run_toolbar, run_menu, "Simulate",'builder-run-start-symbolic.svg',"f5", self.execute)

        self.update_title()
        self.show()
        self.arches = []
    
    def add_simulation_time_spin_box(self, platform: QToolBar):
        spinbox = QSpinBox()
        spinbox.setStatusTip("Simulation End time")
        spinbox.setMaximum(1000000000)
        spinbox.setValue(1000)
        platform.addWidget(spinbox)
        self.spinbox = spinbox

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
        lastPath = self.filePath
        if not autoOpen:
            self.filePath, _ = QFileDialog.getOpenFileName(self, "Open File ", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
        if self.filePath == '':
            self.filePath = lastPath
            return
        if self.filePath:
            with open(self.filePath, 'r') as f:
                text = f.read()
                self.editor.setPlainText(text)
                self.buffer = text
                self.update_title()
                self.config["lastActiveFile"] = self.filePath

    def save_file(self):
        if not self.filePath or self.filePath == './':
            lastPath = self.filePath
            self.filePath, _ = QFileDialog.getSaveFileName(self, "Save File ", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
            if self.filePath == '':
                self.filePath = lastPath
                return
        if self.filePath:
            with open(self.filePath, 'w') as f:
                text = self.editor.toPlainText()
                self.buffer = text
                f.write(text)
                self.update_title()
                self.config["lastActiveFile"] = self.filePath

    def save_file_as(self):
        lastPath = self.filePath
        self.filePath, _ = QFileDialog.getSaveFileName(self, "Save File As", os.path.dirname(self.config["lastActiveFile"]), "VHDL Files (*.vhd);; All Files (*.*)", "VHDL Files (*.vhd)")
        if self.filePath == '':
            self.filePath = lastPath
            return
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

    
    def compile(self, suppressMessage = False):
        self.errorbox.clear()
        error.errno.clear()
        if self.buffer != self.editor.toPlainText():
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


        '''
        Clear all errors already set
        '''
        cursor_current_pos = self.editor.textCursor()
        self.editor.selectAll()
        resetfmt = QTextCharFormat()
        resetfmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.NoUnderline)
        self.editor.textCursor().setCharFormat(resetfmt)
        self.editor.setTextCursor(cursor_current_pos)
        
        if len(cli.error.errno) == 0:
            if suppressMessage:
                return True
            
            self.statusBar().showMessage("Compilation Successful", 5000)
            QMessageBox.information(
                self,
                "Result",
                "Compilation Successful",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.Ok,
            )
            return True

        self.errorbox.itemClicked.connect(errorbox_error_clicked)
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
            fmt.setUnderlineColor(QColor(255,0,0,255))
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
            self.editor.textCursor().setCharFormat(fmt)
            self.editor.setTextCursor(cursor_current_pos)
        
        return False


    def execute(self):            
        def show_Legend(event): 
            #get mouse coordinates
            mouseXdata = event.xdata
            if mouseXdata is not None:    
                multi.updatex(mouseXdata, color='r')
    
        time = self.spinbox.value()
        cli.execute(self.arches, time)
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
        
        figure, axis = pyplot.subplots(len(signals), 1, sharex=True)
        for i in range(len(signals)):
            axis[i].plot(times, values[i], label=signals[i])
            axis[i].legend(loc='upper right')

        multi = MyMultiCursor(figure.canvas, tuple(axis), color='r' , lw=1, useblit=True, horizOn=[], vertOn=axis)
        figure.canvas.mpl_connect('motion_notify_event', show_Legend)

        pyplot.show()
        # vcd_dump.output.close()
        vcd_dump.VcdWriter = None

        vcd_dump.current_time = 0
        # vcd_dump.variables = {}
        vcd_dump.variable_values = {}
        vcd_dump.values_over_time = []
        
