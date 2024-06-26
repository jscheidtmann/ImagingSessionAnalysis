import os
import subprocess
import sys
import logging

import qdarktheme
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QComboBox, QToolButton, QTableWidgetItem
from PyQt6.QtWidgets import QTabWidget, QTableWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from astropy.coordinates import SkyOffsetFrame
from Spherical import formatHMS, formatDMS, formatAngle, formatDMSLow

import DataColumn as DataColumn
import SessionData as Data
from GuideGraph import QGuideGraph
from OpenNewSession import OpenNewSession

is_frozen = getattr(sys, 'frozen', False)
frozen_temp_path = getattr(sys, '_MEIPASS', '')


class MainWindow(QMainWindow):
    """
    Main window and its functionality.

    Conventions:
      createX... methods are invoked for creating (parts of) the application.

      On... methods are invoked by the UI (view).
       - all exceptions must be caught, logged and displayed in a message box.

      updateX... methods are used to manage the model.

      The main method (see bottom of file) creates a logger object, which is accessible as 'self.log'
    """

    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.log = logger

        # UI Elements
        self.leftGraphBox = None
        self.rightGraphBox = None
        self.guidingChartView = None
        self.guidingChart = None
        self.guidingChartAxis = []
        self.tableFrame = None
        self.openSession = None
        self.chartView = None
        self.ditherView = None
        self.ditherChart = None
        self.ditherChartView = None
        self.ditherChartAxis = []
        self.chart = None
        self.main_widget = None
        self.toolbar_widget = None
        self.overviewText = None
        self.imagesTable = None
        self.graphView = None
        self.createWindow()
        self.setWindowTitle("Image Session Analysis")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        self.sessionGraphLeft = None
        self.sessionGraphRight = None
        self.sessionGraphAxis = []

        # Model components
        self.sessionData = Data.SessionData()
        self.sessionFolder = None

    def createToolBar(self):
        self.toolbar_widget = QWidget()
        toolBarLayout = QHBoxLayout()
        self.toolbar_widget.setLayout(toolBarLayout)
        toolBarLayout.setContentsMargins(4, 2, 4, 2)
        self.openSession = QToolButton()
        self.openSession.clicked.connect(self.OnOpenNewSession)

        if is_frozen:
            basedir = frozen_temp_path
        else:
            basedir = os.path.dirname(os.path.abspath(__file__))

        self.openSession.setFixedSize(QSize(32, 32))
        self.openSession.setIcon(QIcon(os.path.join(basedir, 'Icons/folder.png')))
        toolBarLayout.addWidget(self.openSession)
        toolBarLayout.addSpacing(8)

        self.changeSettings = QToolButton()
        self.changeSettings.setFixedSize(QSize(32, 32))
        self.changeSettings.setIcon(QIcon(os.path.join(basedir, 'Icons/gearshape.png')))
        toolBarLayout.addWidget(self.changeSettings)

        toolBarLayout.addStretch()

        return self.toolbar_widget

    def createImageTable(self):
        self.tableFrame = QWidget()
        tableFrameLayout = QVBoxLayout()
        tableFrameLayout.setContentsMargins(4, 4, 4, 4)
        self.tableFrame.setLayout(tableFrameLayout)
        self.imagesTable = QTableWidget()
        self.imagesTable.setSortingEnabled(True)

        self.imagesTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tableFrame.layout().addWidget(self.imagesTable)
        self.imagesTable.currentCellChanged.connect(self.OnCurrentTableCellChanged)
        self.imagesTable.cellDoubleClicked.connect(self.OnLaunchImageViewer)

        self.guidingChart = QChart()
        self.guidingChartView = QGuideGraph(self.guidingChart)
        self.guidingChartView.setFixedHeight(240)
        self.guidingChart.createDefaultAxes()
        self.guidingChart.setAnimationOptions(QChart.AnimationOption.AllAnimations)
        self.guidingChart.legend().setVisible(True)
        self.guidingChart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.guidingChart.setBackgroundBrush(QBrush(QColor(0, 0, 0)))

        self.tableFrame.layout().addWidget(self.guidingChartView)

        return self.tableFrame

    def createGraphView(self):
        self.graphView = QWidget()
        graphLayout = QVBoxLayout()
        self.graphView.setLayout(graphLayout)

        self.chart = QChart()
        self.chartView = QChartView(self.chart)
        self.chart.createDefaultAxes()
        self.chart.setAnimationOptions(QChart.AnimationOption.AllAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart.setBackgroundBrush(QBrush(QColor(0, 0, 0)))

        graphToolsWidget = QWidget()
        graphToolsLayout = QHBoxLayout()
        graphToolsLayout.setContentsMargins(4, 2, 4, 2)
        graphToolsWidget.setLayout(graphToolsLayout)

        self.leftGraphBox = QComboBox()
        self.leftGraphBox.currentIndexChanged.connect(self.OnLeftGraphValueIndexChanged)
        self.rightGraphBox = QComboBox()
        self.rightGraphBox.currentIndexChanged.connect(self.OnRightGraphValueIndexChanged)

        graphToolsLayout.addWidget(self.leftGraphBox)
        graphToolsLayout.addSpacing(32)
        graphToolsLayout.addWidget(self.rightGraphBox)

        graphLayout.addWidget(graphToolsWidget)
        graphLayout.addSpacing(4)
        graphLayout.addWidget(self.chartView)

        return self.graphView

    def createDitherView(self):
        self.ditherView = QWidget()
        graphLayout = QVBoxLayout()
        self.ditherView.setLayout(graphLayout)

        self.ditherChart = QChart()
        self.ditherChartView = QChartView(self.ditherChart)
        self.ditherChart.createDefaultAxes()
        self.ditherChart.setAnimationOptions(QChart.AnimationOption.AllAnimations)
        self.ditherChart.legend().setVisible(True)
        self.ditherChart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.ditherChart.setBackgroundBrush(QBrush(QColor(0, 0, 0)))

        graphLayout.addWidget(self.ditherChartView)

        return self.ditherView

    def createTabWidget(self):
        tabWidget = QTabWidget()
        tabWidget.addTab(self.createImageTable(), "Data")
        tabWidget.addTab(self.createGraphView(), "Charts")
        tabWidget.addTab(self.createDitherView(), "Dither")

        return tabWidget

    def createWindow(self):
        mainVertical = QVBoxLayout()

        mainVertical.addWidget(self.createToolBar())
        mainVertical.addSpacing(8)
        mainVertical.addWidget(self.createTabWidget())

        self.main_widget = QWidget(self)
        self.main_widget.setLayout(mainVertical)
        self.setCentralWidget(self.main_widget)

        self.log.info("Starting ImagingSessionAnalysis")
        return

    def OnOpenNewSession(self):
        try:
            dialog = OpenNewSession(self)
            dialog.set(self.sessionData)
            dialog.execute()
            if self.sessionData is not None and self.sessionData.data is not None and not self.sessionData.data.empty:
                self.log.info("Imported Session Data")
                self.updateSessionValues()
                self.updateTable()
                self.updateSessionGraph()
                self.updateDitherGraph()
            return
        except Exception as e:
            self.log.error("Error opening new session")
            self.log.exception(e)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("An Error occurred")
            dlg.setText(str(e))
            dlg.exec()

    def OnLaunchImageViewer(self):
        try:
            if self.sessionData.imageFolder is not None:
                rowIndex = self.imagesTable.currentRow()
                filename = self.sessionData.data.iloc[rowIndex][DataColumn.FNAME]
                filepath = os.path.normpath(os.path.join(self.sessionData.imageFolder, filename))
                self.log.info("Starting image viewer on %s", filepath)
                subprocess.Popen([self.getImageViewer(), filepath])
        except Exception as e:
            self.log.error("Error launching the image viewer", repr(e))
            # TODO Display error message box.
            dlg = QMessageBox(self)
            dlg.setWindowTitle("An Error occurred")
            dlg.setText(str(e))
            dlg.exec()

    def OnCurrentTableCellChanged(self):
        try:
            self.log.info("Image row changed")
            self.updateGuideGraph()
            return
        except Exception as e:
            self.log.error("Error in OnCurrentTableCellChanged", repr(e))
            dlg = QMessageBox(self)
            dlg.setWindowTitle("An error occurred")
            dlg.setText(str(e))
            dlg.exec()

    def getTextColor(self, value, column, min=None, max=None, pxscale=None):
        if value is None:
            return QColor(0, 0, 0)  # Black
        if (column == DataColumn.FNAME or column == DataColumn.BAYERPAT or column == DataColumn.CAMERA
                or column == DataColumn.TELESCOPE or column == DataColumn.CCDSETTEMP or column == DataColumn.CCDTEMP):
            return QColor(160, 160, 160)
        if column == DataColumn.FOCALLENGTH or column == DataColumn.FOCRATIO:
            return QColor(160, 160, 160)
        if column == DataColumn.RMS or column == DataColumn.RMSRA or column == DataColumn.RMSDEC:
            assert pxscale is not None, "Pass pxscale for RMS, RMSRA or RMSDEC"
            if value < 0.66 * pxscale:
                return QColor(0, 255, 0)
            elif value < pxscale:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)
        if column == DataColumn.DetectedStars:
            assert max is not None, "Pass max for DetectedStars!"
            maxStars = max
            if value < 0.75 * maxStars:
                return QColor(255, 0, 0)
            elif value < 0.9 * maxStars:
                return QColor(255, 255, 0)
            else:
                return QColor(0, 255, 0)

        if column == DataColumn.ADUMean or column == DataColumn.ADUMedian:
            assert min is not None, "Pass min fro ADUMedian!"
            minValue = min
            if value > 1.25 * minValue:
                return QColor(255, 0, 0)
            elif value > 1.1 * minValue:
                return QColor(255, 255, 0)
            else:
                return QColor(0, 255, 0)

        if column == DataColumn.SUNALT:
            if value.deg < -18.0:
                return QColor(0, 255, 0)
            elif value.deg < -12.0:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.MOONALT:
            if value.deg < 0.0:
                return QColor(0, 255, 0)
            elif value.deg < 10.0:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.HUMIDITY:
            if value < 70.0:
                return QColor(0, 255, 0)
            elif value < 90.0:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.AIRMASS:
            assert min is not None, "pass in min-value for AIRMASS"
            minValue = min
            if value > 3.0 * minValue:
                return QColor(255, 0, 0)
            elif value > 1.5 * minValue:
                return QColor(255, 255, 0)
            else:
                return QColor(0, 255, 0)

        if column == DataColumn.HFR:
            assert min is not None, "pass in min-value for HFR"
            minValue = min
            if value < 1.1 * minValue:
                return QColor(0, 255, 0)
            elif value < 1.25 * minValue:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.FWHM:
            assert min is not None, "pass in min-value for FWHM!"
            minValue = min
            if value < 1.1 * minValue:
                return QColor(0, 255, 0)
            elif value < 1.25 * minValue:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.GUIDINGPIXRA or column == DataColumn.GUIDINGPIXDEC or column == DataColumn.GUIDINGPIX:
            if value < 0.66:
                return QColor(0, 255, 0)
            elif value < 0.9:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.GUIDINGMINRA or column == DataColumn.GUIDINGMINDEC or \
                column == DataColumn.GUIDINGMAXRA or column == DataColumn.GUIDINGMAXDEC:
            assert pxscale is not None, "pass in pixel scale for Guiding values"
            if abs(value) < 0.8 * pxscale:
                return QColor(0, 255, 0)
            elif abs(value) < pxscale:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        if column == DataColumn.Eccentricity:
            if value < 0.3:
                return QColor(0, 255, 0)
            elif value < 0.5:
                return QColor(255, 255, 0)
            else:
                return QColor(255, 0, 0)

        return QColor(255, 255, 255)  # TODO Depends on UI mode: Dark mode needs white, else black

    def format(self, value, column):
        if value is None:
            return "n/a"
        if column == DataColumn.FNAME:
            return value
        if column == DataColumn.FOCALLENGTH:
            return str(value)
        if column == DataColumn.FOCRATIO:
            return str(value)
        if column == DataColumn.RMS:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.RMSRA:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.RMSDEC:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.GUIDINGPEAKSRA:
            return str(value)
        if column == DataColumn.GUIDINGPEAKSDEC:
            return str(value)
        if column == DataColumn.GUIDINGMINRA or column == DataColumn.GUIDINGMAXRA:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.GUIDINGMINDEC or column == DataColumn.GUIDINGMAXDEC:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.GUIDINGRMSSNR or column == DataColumn.GUIDINGMINSNR or column == DataColumn.GUIDINGMAXSNR:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.GUIDINGPIX or column == DataColumn.GUIDINGPIXRA or column == DataColumn.GUIDINGPIXDEC:
            return "{value:.2f}".format(value=value)
        if column == DataColumn.GUIDINGMINSTARMASS:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.AIRMASS:
            return "{value:.3f}".format(value=value)
        if column == DataColumn.RA:
            return formatHMS(value / 15.0)
        if column == DataColumn.DEC:
            return formatDMS(value)
        if column == DataColumn.ALTITUDE or column == DataColumn.AZIMUTH:
            return formatDMSLow(value)
        if column == DataColumn.SITELONG or column == DataColumn.SITELAT:
            return formatDMSLow(value)
        if column == DataColumn.MOONALT:
            return formatAngle(value)
        if column == DataColumn.SUNALT:
            return formatAngle(value)
        if column == DataColumn.DEWPOINT:
            return "{value:.1f}".format(value=value)

        if column == DataColumn.AMBIENTTEMP:
            return "{value:.1f}".format(value=value)
        if column == DataColumn.HFR or column == DataColumn.FWHM or column == DataColumn.Eccentricity:
            return "{value:.2f}".format(value=value)
        if column == DataColumn.HFRStDev:
            return "{value:.2f}".format(value=value)
        if column == DataColumn.ADUMean:
            return "{value:.2f}".format(value=value)

        return str(value)

    def updateTable(self):
        if self.sessionData is None:
            self.log.warn("updateTable called, even though sessionData is empty")
            return
        headers = list(self.sessionData.data)
        self.imagesTable.setRowCount(self.sessionData.data.shape[0])
        self.imagesTable.setColumnCount(self.sessionData.data.shape[1])
        self.imagesTable.setHorizontalHeaderLabels(headers)

        # getting data from df is computationally costly so convert it to array first
        for row in range(self.sessionData.data.shape[0]):
            currentRow = self.sessionData.data.iloc[row]
            for i, col in enumerate(self.sessionData.getColumns()):
                str = self.format(currentRow[col], col)
                item = QTableWidgetItem(str)
                if col == DataColumn.AIRMASS or col == DataColumn.FWHM or col == DataColumn.HFR \
                        or col == DataColumn.ADUMedian or col == DataColumn.ADUMean:
                    item.setForeground(QBrush(self.getTextColor(currentRow[col], col, min=self.sessionData.getMin(col))))
                elif col == DataColumn.DetectedStars:
                    item.setForeground(QBrush(self.getTextColor(currentRow[col], col, max=self.sessionData.getMax(col))))
                elif col == DataColumn.GUIDINGMINRA or col == DataColumn.GUIDINGMINDEC \
                        or col == DataColumn.GUIDINGMAXRA or col == DataColumn.GUIDINGMAXDEC \
                        or col == DataColumn.RMS or col == DataColumn.RMSRA or col == DataColumn.RMSDEC:
                    item.setForeground(QBrush(self.getTextColor(currentRow[col], col, \
                                       pxscale=self.sessionData.getPixelScale())))
                else:
                    item.setForeground(QBrush(self.getTextColor(currentRow[col], col)))
                self.imagesTable.setItem(row, i, item)

    def updateSessionValues(self):
        if self.sessionData is None:
            self.log.warn("updateSessionValues is called, even though sessionData is empty")
            return
        values = self.sessionData.getChartValues()
        self.leftGraphBox.addItems(values.keys())
        self.rightGraphBox.addItems(values.keys())
        return

    def OnLeftGraphValueIndexChanged(self, index):
        """
        Update graph(s), when user selects another variable from the left combobox
        """
        if self.sessionData is None:
            return
        try:
            values = self.sessionData.getChartValues()
            keys = list(values.keys())
            key = keys[index]
            self.sessionGraphLeft = values[key]
            self.log.info("Displaying left graph %s", key)
            self.updateSessionGraph()
            return
        except Exception as e:
            self.log.error("Error in OnLeftGraphValueIndexChange")
            self.log.exception(e)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("An error occurred")
            dlg.setText(str(e))
            dlg.exec()

    def OnRightGraphValueIndexChanged(self, index):
        """
        Update graph(s), when user selects antoher variable from the right combobox
        """
        if self.sessionData is None:
            return
        try:
            values = self.sessionData.getChartValues()
            keys = list(values.keys())
            key = keys[index]
            self.sessionGraphRight = values[key]
            self.log.info("Displaying right graph %s", key)
            self.updateSessionGraph()
            return
        except Exception as e:
            self.log.error("Error in OnLeftGraphValueIndexChange")
            self.log.exception(e)
            dlg = QMessageBox(self)
            dlg.setWindowTitle("An error occurred")
            dlg.setText(str(e))
            dlg.exec()

    def updateDitherGraph(self):
        """
        The Dither chart is created from the solved positions of the images.

        uses a smash & rebuild strategy for the dither graph

        May throw an Exception.
        """
        self.log.info("Updating dither graph")
        self.ditherChart.removeAllSeries()
        for axis in self.ditherChartAxis:
            self.ditherChart.removeAxis(axis)
        self.ditherChart.legend().hide()
        self.ditherChartAxis.clear()

        positions = self.sessionData.getDitherData()
        center = SkyOffsetFrame(origin=positions[0])
        ditherPositionsRA = []
        ditherPositionsDEC = []
        for pos in positions:
            d = pos.transform_to(center)
            ditherPositionsRA.append(d.lon.degree * 3600.0)
            ditherPositionsDEC.append(d.lat.degree * 3600.0)

        x_axis = QValueAxis()
        x_axis.setRange(min(ditherPositionsRA), max(ditherPositionsRA))
        x_axis.setLabelFormat("%3.1f\"")
        x_axis.setTickType(QValueAxis.TickType.TicksDynamic)
        x_axis.setTickInterval(10)
        x_axis.setGridLineColor(QColor(128, 128, 128, 128))
        x_axis.setTitleText("△RA / arc-sec")
        x_axis.setLabelsColor(QColor(255, 255, 255, 255))
        x_axis.setTitleBrush(QColor(255, 255, 255, 255))
        self.ditherChart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self.ditherChartAxis.append(x_axis)

        y_axis = QValueAxis()
        y_axis.setRange(min(ditherPositionsDEC), max(ditherPositionsDEC))
        y_axis.setLabelFormat("%3.1f\"")
        y_axis.setTickType(QValueAxis.TickType.TicksDynamic)
        y_axis.setTickInterval(10)
        y_axis.setGridLineColor(QColor(128, 128, 128, 128))
        y_axis.setTitleText("△DEC / arc-sec")
        y_axis.setLabelsColor(QColor(255, 255, 255, 255))
        y_axis.setTitleBrush(QColor(255, 255, 255, 255))
        self.ditherChart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        self.ditherChartAxis.append(y_axis)

        series = QLineSeries()
        series.setPointsVisible(True)

        for i in range(0, len(ditherPositionsRA)):
            series.append(ditherPositionsRA[i], ditherPositionsDEC[i])

        pen = series.pen()
        pen.setColor(QColor(255, 255, 0, 255))   # Yellow
        series.setPen(pen)
        self.ditherChart.addSeries(series)

    def updateSessionGraph(self):
        """
        Update the graph on the second tab
        """
        self.log.info("Updating session graph")
        self.chart.removeAllSeries()
        for axis in self.sessionGraphAxis:
            self.chart.removeAxis(axis)
        self.chart.legend().hide()
        self.sessionGraphAxis.clear()

        exposures = self.getExposures()

        x_axis = QValueAxis()
        x_axis.setRange(1, max(exposures))
        x_axis.setLabelFormat("%d")
        x_axis.setTickType(QValueAxis.TickType.TicksDynamic)
        x_axis.setTickInterval(5)
        x_axis.setGridLineColor(QColor(128, 128, 128, 128))
        x_axis.setTitleText("Exposure")
        x_axis.setLabelsColor(QColor(255, 255, 255, 255))
        x_axis.setTitleBrush(QColor(255, 255, 255, 255))
        self.chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self.sessionGraphAxis.append(x_axis)

        if self.sessionGraphLeft is not None:
            leftSeries = QLineSeries()
            yvalues = self.createSeries(leftSeries, self.sessionGraphLeft)
            pen = leftSeries.pen()
            pen.setColor(QColor(255, 255, 0, 255))
            leftSeries.setPen(pen)
            self.chart.addSeries(leftSeries)

            miny = min(yvalues)
            maxy = max(yvalues)
            ticks = (maxy - miny) / 10

            yLeft_axis = QValueAxis()
            yLeft_axis.setRange(miny, maxy)
            yLeft_axis.setLabelFormat("%1.3f")
            if self.sessionGraphLeft == DataColumn.DetectedStars or self.sessionGraphLeft == DataColumn.ADUMean or \
                    self.sessionGraphLeft == DataColumn.ADUMedian or self.sessionGraphLeft == DataColumn.ADUMin or \
                    self.sessionGraphLeft == DataColumn.ADUMax:
                yLeft_axis.setLabelFormat("%d")

            yLeft_axis.setTickType(QValueAxis.TickType.TicksDynamic)
            yLeft_axis.setTickInterval(ticks)
            yLeft_axis.setGridLineColor(QColor(128, 128, 128, 128))
            yLeft_axis.setTitleText(self.sessionGraphLeft)
            yLeft_axis.setTitleBrush(QColor(255, 255, 0, 255))
            yLeft_axis.setLabelsColor(QColor(255, 255, 0, 255))
            self.chart.addAxis(yLeft_axis, Qt.AlignmentFlag.AlignLeft)
            self.sessionGraphAxis.append(yLeft_axis)

        if self.sessionGraphRight is not None:
            rightSeries = QLineSeries()
            yvalues = self.createSeries(rightSeries, self.sessionGraphRight)
            pen = rightSeries.pen()
            pen.setColor(QColor(0, 0, 255, 255))
            rightSeries.setPen(pen)
            self.chart.addSeries(rightSeries)

            miny = min(yvalues)
            maxy = max(yvalues)
            ticks = (maxy - miny) / 10

            yRight_axis = QValueAxis()
            yRight_axis.setRange(miny, maxy)
            yRight_axis.setLabelFormat("%1.3f")
            if self.sessionGraphRight == DataColumn.DetectedStars or self.sessionGraphRight == DataColumn.ADUMean or \
                    self.sessionGraphRight == DataColumn.ADUMedian or self.sessionGraphRight == DataColumn.ADUMin or \
                    self.sessionGraphRight == DataColumn.ADUMax:
                yRight_axis.setLabelFormat("%d")

            yRight_axis.setTickType(QValueAxis.TickType.TicksDynamic)
            yRight_axis.setTickInterval(ticks)
            yRight_axis.setGridLineColor(QColor(128, 128, 128, 128))
            yRight_axis.setTitleText(self.sessionGraphRight)
            yRight_axis.setTitleBrush(QColor(0, 0, 255, 255))
            yRight_axis.setLabelsColor(QColor(0, 0, 255, 255))
            self.chart.addAxis(yRight_axis, Qt.AlignmentFlag.AlignRight)
            self.sessionGraphAxis.append(yRight_axis)

    def createSeries(self, series, graphType):
        """
        create series for session graph(s)

        helper method called by respective OnUpdate... methods
        """
        values = []
        seriesData = self.sessionData.data[['INDEX', graphType]]
        for row in range(seriesData.shape[0]):
            currentRow = seriesData.iloc[row]
            index = currentRow[0]
            data = currentRow[1]

            if data is not None:
                if graphType == DataColumn.MOONALT or graphType == DataColumn.SUNALT:
                    data = data.degree

                series.append(index, data)
                values.append(data)

            print(data)

        return values

    def getExposures(self):
        indices = []
        seriesData = self.sessionData.data[['INDEX']]
        for row in range(seriesData.shape[0]):
            currentRow = seriesData.iloc[row]
            index = currentRow.iloc[0]
            indices.append(index)

        return indices

    def updateGuideGraph(self):
        rowIndex = self.imagesTable.currentRow()
        self.log.info("Updating guide graph for row %i", rowIndex)
        jd1 = self.sessionData.data.iloc[rowIndex][DataColumn.EXPSTARTJDD]
        duration = self.sessionData.data.iloc[rowIndex][DataColumn.EXPOSURE]
        jd2 = jd1 + duration / 86400.0
        frames = self.sessionData.guidingData.getGuidingFrames(jd1, jd2)

        seriesRA = QLineSeries()
        seriesDEC = QLineSeries()

        self.guidingChart.removeAllSeries()
        self.guidingChart.legend().hide()

        for axis in self.guidingChartAxis:
            self.guidingChart.removeAxis(axis)

        self.guidingChartAxis.clear()

        maxRA = 0.0
        maxDEC = 0.0

        pulseRA = []
        pulseDEC = []

        for frame in frames:
            t = (frame.time - jd1) * 86400.0
            seriesRA.append(t, frame.raRawDistance)
            seriesDEC.append(t, frame.decRawDistance)
            maxRA = max(maxRA, abs(frame.raRawDistance))
            maxDEC = max(maxDEC, abs(frame.decRawDistance))
            raDir = 1.0
            if frame.raDirection == 'W':
                raDir = -1.0
            pulseRA.append((t, frame.raDuration * raDir))
            decDir = 1.0
            if frame.decDirection == 'S':
                decDir = -1.0
            pulseDEC.append((t, frame.decDuration * decDir))

        x_axis = QValueAxis()
        x_axis.setRange(1, duration)
        x_axis.setLabelFormat("%d")
        x_axis.setTickType(QValueAxis.TickType.TicksDynamic)
        x_axis.setGridLineColor(QColor(60, 60, 60, 128))
        x_axis.setTickInterval(5)
        x_axis.setTitleText("Time")
        self.guidingChart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self.guidingChartAxis.append(x_axis)

        y_axis = QValueAxis()
        y_axis.setRange(-max(maxRA, maxDEC, 1.0), max(maxRA, maxDEC, 1.0))
        y_axis.setLabelFormat("%0.2f")
        y_axis.setTickType(QValueAxis.TickType.TicksDynamic)
        y_axis.setGridLineColor(QColor(60, 60, 60, 128))
        y_axis.setTickInterval(1)

        self.guidingChartAxis.append(y_axis)
        pen = seriesRA.pen()
        pen.setColor(QColor(0, 0, 255, 255))
        seriesRA.setPen(pen)

        self.guidingChart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        self.guidingChart.addAxis(y_axis, Qt.AlignmentFlag.AlignRight)

        pen2 = seriesDEC.pen()
        pen2.setColor(QColor(255, 0, 0, 255))
        seriesDEC.setPen(pen2)

        self.guidingChart.addSeries(seriesRA)
        self.guidingChart.addSeries(seriesDEC)
        seriesRA.attachAxis(x_axis)
        seriesRA.attachAxis(y_axis)
        seriesDEC.attachAxis(x_axis)
        seriesDEC.attachAxis(y_axis)

        self.guidingChartView.setRaGuidePulses(pulseRA)
        self.guidingChartView.setDecGuidePulses(pulseDEC)

        self.guidingChartView.update()

    def getImageViewer(self):
        """
        Use sys.platform to determine, which process to start in order to open a file.
        """
        # TODO make this a configuration option
        return {'linux': 'xdg-open', 'win32': 'explorer', 'darwin': 'open'}[sys.platform]


if __name__ == "__main__":
    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt6'

    # Setup two log handlers: One for the console, one (more detailed) to a file.
    chdlr = logging.StreamHandler()
    logging.getLogger().addHandler(chdlr)
    fhdlr = logging.FileHandler('ImagingSessionAnalysis.log', 'a', encoding='utf-8')
    fhdlr.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s'))
    logging.getLogger().addHandler(fhdlr)
    logging.getLogger().setLevel(logging.INFO)  # TODO Make default log level a configuration item.

    app = QApplication(sys.argv)
    # Apply the complete dark theme to your Qt App.
    # qdarktheme.setup_theme()

    logger = logging.getLogger("ImagingSessionAnalysis")
    win = MainWindow(logger)

    win.show()
    exit_code = app.exec()
    win.log.info("Stopping ImagingSessionAnalysis with exit code %i", exit_code)
    sys.exit(exit_code)
