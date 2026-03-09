import sys
from pathlib import Path
import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_df = None
        self.setup_ui()

    def setup_ui(self):
        # Scrollable central widget and layout
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        content_widget = QtWidgets.QWidget()
        scroll.setWidget(content_widget)

        central_layout = QtWidgets.QVBoxLayout(content_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Top bar
        self.top_bar = self.create_top_bar()
        central_layout.addWidget(self.top_bar)

        # CSV input and temp function buttons
        self.csv_button = QtWidgets.QPushButton("Load CSV File")
        self.csv_button.setObjectName("CsvButton")
        self.csv_button.setFixedHeight(40)
        self.csv_button.clicked.connect(self.load_csv)
        self.temp_button = QtWidgets.QPushButton("Run Temp Function")
        self.temp_button.setObjectName("TempButton")
        self.temp_button.setFixedHeight(40)
        self.temp_button.setEnabled(False)
        self.temp_button.setText("Run Calculation")
        self.temp_button.clicked.connect(self.run_calculation)
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 20, 20, 0)
        button_layout.addWidget(self.csv_button, stretch=1)
        button_layout.addWidget(self.temp_button)
        central_layout.addWidget(button_container)

        # File info boxes
        self.file_info_container = self.create_info_container()
        central_layout.addWidget(self.file_info_container)

        # Analysis boxes
        self.analysis_container = self.create_info_container()
        central_layout.addWidget(self.analysis_container)

        # CSV preview table
        self.csv_table = QtWidgets.QTableWidget()
        self.csv_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.csv_table.setAlternatingRowColors(True)
        self.csv_table.horizontalHeader().setStretchLastSection(True)
        self.csv_table.setMinimumHeight(250)
        central_layout.addWidget(self.csv_table)

        # Output below CSV data
        self.output_box = QtWidgets.QPlainTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("Pattern output will appear here after loading a CSV.")
        self.output_box.setMinimumHeight(160)
        central_layout.addWidget(self.output_box)

        # Pie chart for waste percentage
        self.chart_container = QtWidgets.QWidget()
        self.chart_layout = QtWidgets.QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(20, 0, 20, 20)
        self.chart_layout.setSpacing(8)
        self.chart_layout.addWidget(QtWidgets.QLabel("Waste Chart"))
        central_layout.addWidget(self.chart_container)

        central_layout.addStretch()

    def run_calculation(self):
        if self.loaded_df is None:
            self.show_error("No CSV loaded.")
            return

        self.temp_button.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        QtWidgets.QApplication.processEvents()
        try:
            result = self.calculate_patterns(self.loaded_df)
            if "error" in result:
                self.output_box.setPlainText(result["error"])
                self.clear_chart()
                return

            self.output_box.setPlainText(self.format_result_text(result))
            self.clear_chart()
            self.update_pie_chart(result['waste_percent'])
            self.update_runtime_chart(
                result['cumulative_waste_6000'],
                result['cumulative_waste_8000'],
                result['cumulative_waste_13000'],
                result['max_remaining_lengths']
            )
            self.update_bar_usage_runtime_chart(result['selected_bar_sizes'])
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.temp_button.setEnabled(True)

    def create_top_bar(self):
        bar = QtWidgets.QWidget()
        bar.setObjectName("TopBar")
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 0, 0)
        layout.setSpacing(0)
        title = QtWidgets.QLabel("grant vessels construction")
        title.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        layout.addStretch()
        return bar

    def create_info_container(self):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)
        return container

    def clear_layout(self, layout):
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.setParent(None)

    def load_csv(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("CSV Files (*.csv)")
        if not file_dialog.exec():
            return
        selected_files = file_dialog.selectedFiles()
        if not selected_files:
            return
        csv_path = selected_files[0]
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            self.show_error(str(e))
            return

        summary = self.get_csv_summary(df)
        if "error" in summary:
            self.show_error(summary["error"])
            return

        self.loaded_df = df
        self.temp_button.setEnabled(True)

        self.update_file_info(csv_path, len(df))
        self.update_analysis(summary["total_length"], summary["avg_length"], summary["total_count"])
        self.update_csv_table(df)
        self.output_box.clear()
        self.clear_chart()

    def update_file_info(self, csv_path, row_count):
        self.clear_layout(self.file_info_container.layout())
        self.add_info_box(self.file_info_container.layout(), "File Loaded", self.format_local_path(csv_path))
        self.add_info_box(self.file_info_container.layout(), "Rows", str(row_count))

    def format_local_path(self, file_path):
        path_obj = Path(file_path)
        try:
            return str(path_obj.relative_to(Path.cwd()))
        except ValueError:
            return path_obj.name

    def update_analysis(self, total_length, avg_length, total_count):
        self.clear_layout(self.analysis_container.layout())
        analysis = [
            ("Total Length", f"{total_length}"),
            ("Average Length", f"{avg_length:.2f}"),
            ("Total Count", f"{total_count}")
        ]
        for title, value in analysis:
            self.add_info_box(self.analysis_container.layout(), title, value)

    def update_csv_table(self, df):
        preview = df.head(500).copy()
        self.csv_table.setRowCount(len(preview.index))
        self.csv_table.setColumnCount(len(preview.columns))
        self.csv_table.setHorizontalHeaderLabels([str(col) for col in preview.columns])

        for row_idx, row in enumerate(preview.itertuples(index=False, name=None)):
            for col_idx, value in enumerate(row):
                self.csv_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(value)))

    def format_result_text(self, result):
        stock_usage = result.get('stock_usage', {})
        return (
            f"Total bars used: {result['bars_used']}\n"
            f"Bars by size: 6000×{stock_usage.get(6000, 0)}, 8000×{stock_usage.get(8000, 0)}, 13000×{stock_usage.get(13000, 0)}\n"
            f"Total waste: {result['waste']} units\n"
            f"Total length: {result['total_length']} units\n"
            f"Waste percentage: {result['waste_percent']:.2f}%"
        )

    def get_csv_summary(self, df):
        if 'PartLength' in df.columns and 'Count' in df.columns:
            return {
                "total_length": (df['PartLength'] * df['Count']).sum(),
                "avg_length": df['PartLength'].mean(),
                "total_count": int(df['Count'].sum()),
            }

        if 'Length' in df.columns:
            return {
                "total_length": df['Length'].sum(),
                "avg_length": df['Length'].mean(),
                "total_count": int(df['Length'].count()),
            }

        return {"error": "CSV needs either columns: PartLength + Count, or Length."}

    def extract_length_counts(self, df):
        if 'PartLength' in df.columns and 'Count' in df.columns:
            grouped = df.groupby('PartLength', as_index=False)['Count'].sum()
            return {
                int(row['PartLength']): int(row['Count'])
                for _, row in grouped.iterrows()
                if int(row['Count']) > 0
            }

        if 'Length' in df.columns:
            series = df['Length'].dropna().astype(int)
            counts = series.value_counts()
            return {int(length): int(count) for length, count in counts.items()}

        return None

    def plan_bar_fill(self, remaining, sorted_lengths, bar_size):
        taken_by_length = {}
        used_length = 0
        available = bar_size

        for length in sorted_lengths:
            count = remaining.get(length, 0)
            if count <= 0 or length > available:
                continue

            take = min(count, available // length)
            if take <= 0:
                continue

            taken_by_length[length] = take
            taken_length = take * length
            available -= taken_length
            used_length += taken_length

        return used_length, taken_by_length

    def pick_best_bar_size(self, remaining, sorted_lengths, stock_sizes):
        best = None

        for candidate_size in stock_sizes:
            used_length, taken_by_length = self.plan_bar_fill(remaining, sorted_lengths, candidate_size)
            if used_length <= 0:
                continue

            waste = candidate_size - used_length
            score = (used_length, -waste, -candidate_size)
            if best is None or score > best["score"]:
                best = {
                    "score": score,
                    "bar_size": candidate_size,
                    "taken_by_length": taken_by_length,
                    "used_parts": sum(taken_by_length.values()),
                }

        return best

    def apply_bar_cut(self, remaining, taken_by_length):
        for length, count_taken in taken_by_length.items():
            new_count = remaining.get(length, 0) - count_taken
            if new_count > 0:
                remaining[length] = new_count
            else:
                remaining.pop(length, None)

    def calculate_patterns(self, df):
        stock_sizes = [6000, 8000, 13000]

        length_counts = self.extract_length_counts(df)
        if length_counts is None:
            return {"error": "CSV needs either columns: PartLength + Count, or Length."}

        if not length_counts:
            return {"error": "No parts found in CSV."}

        max_stock_size = max(stock_sizes)
        too_long = [length for length in length_counts.keys() if length > max_stock_size]
        if too_long:
            return {
                "error": f"Cannot calculate: largest part is {max(too_long)} and exceeds max stock size {max_stock_size}."
            }

        remaining = dict(length_counts)
        total_parts_remaining = sum(remaining.values())
        sorted_lengths = sorted(remaining.keys(), reverse=True)

        waste = 0
        bars_used = 0
        total_length = 0
        cumulative_waste_6000 = []
        cumulative_waste_8000 = []
        cumulative_waste_13000 = []
        max_remaining_lengths = []
        waste_by_size = {6000: 0, 8000: 0, 13000: 0}
        stock_usage = {6000: 0, 8000: 0, 13000: 0}
        selected_bar_sizes = []

        while total_parts_remaining > 0:
            best_choice = self.pick_best_bar_size(remaining, sorted_lengths, stock_sizes)
            if best_choice is None:
                return {"error": "No valid cuts can be made with available stock sizes."}

            chosen_bar_size = best_choice["bar_size"]
            taken_by_length = best_choice["taken_by_length"]
            used_parts = best_choice["used_parts"]

            if used_parts <= 0:
                return {"error": "No valid cuts can be made with available stock sizes."}

            bars_used += 1
            total_length += chosen_bar_size
            stock_usage[chosen_bar_size] = stock_usage.get(chosen_bar_size, 0) + 1
            selected_bar_sizes.append(chosen_bar_size)

            used_length = sum(length * count for length, count in taken_by_length.items())
            bar_waste = chosen_bar_size - used_length
            waste += bar_waste
            waste_by_size[chosen_bar_size] += bar_waste
            total_parts_remaining -= used_parts
            self.apply_bar_cut(remaining, taken_by_length)

            max_length = max(remaining.keys()) if remaining else 0
            max_remaining_lengths.append(max_length)

            cumulative_waste_6000.append(waste_by_size[6000])
            cumulative_waste_8000.append(waste_by_size[8000])
            cumulative_waste_13000.append(waste_by_size[13000])

        waste_percent = (waste / total_length) * 100 if total_length > 0 else 0

        return {
            "bars_used": bars_used,
            "waste": waste,
            "total_length": total_length,
            "waste_percent": waste_percent,
            "cumulative_waste_6000": cumulative_waste_6000,
            "cumulative_waste_8000": cumulative_waste_8000,
            "cumulative_waste_13000": cumulative_waste_13000,
            "max_remaining_lengths": max_remaining_lengths,
            "stock_usage": stock_usage,
            "selected_bar_sizes": selected_bar_sizes,
        }

    def clear_chart(self):
        while self.chart_layout.count() > 1:
            item = self.chart_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def update_pie_chart(self, waste_percent):
        try:
            from PySide6 import QtCharts
        except Exception:
            self.chart_layout.addWidget(QtWidgets.QLabel("QtCharts is not available in this environment."))
            return

        waste_value = max(0.0, min(100.0, float(waste_percent)))
        used_value = max(0.0, 100.0 - waste_value)

        series = QtCharts.QPieSeries()
        series.append("Waste", waste_value)
        series.append("Used", used_value)

        chart = QtCharts.QChart()
        chart.addSeries(series)
        chart.setTitle("Waste Percentage")
        chart.legend().setVisible(True)

        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        chart_view.setMinimumHeight(260)
        self.chart_layout.addWidget(chart_view)

    def update_runtime_chart(self, cumulative_waste_6000, cumulative_waste_8000, cumulative_waste_13000, max_remaining_lengths):
        try:
            from PySide6 import QtCharts
        except Exception:
            return

        all_waste = cumulative_waste_6000 + cumulative_waste_8000 + cumulative_waste_13000
        if not all_waste:
            return

        line_6000 = QtCharts.QLineSeries()
        line_6000.setName("6000 Bar Waste")
        for index, waste_value in enumerate(cumulative_waste_6000, start=1):
            line_6000.append(index, waste_value)
        pen_6000 = QtGui.QPen(QtGui.QColor("#4CAF50"))
        pen_6000.setWidth(2)
        line_6000.setPen(pen_6000)

        line_8000 = QtCharts.QLineSeries()
        line_8000.setName("8000 Bar Waste")
        for index, waste_value in enumerate(cumulative_waste_8000, start=1):
            line_8000.append(index, waste_value)
        pen_8000 = QtGui.QPen(QtGui.QColor("#2196F3"))
        pen_8000.setWidth(2)
        line_8000.setPen(pen_8000)

        line_13000 = QtCharts.QLineSeries()
        line_13000.setName("13000 Bar Waste")
        for index, waste_value in enumerate(cumulative_waste_13000, start=1):
            line_13000.append(index, waste_value)
        pen_13000 = QtGui.QPen(QtGui.QColor("#FF9800"))
        pen_13000.setWidth(2)
        line_13000.setPen(pen_13000)

        chart = QtCharts.QChart()
        chart.addSeries(line_6000)
        chart.addSeries(line_8000)
        chart.addSeries(line_13000)

        max_bar_count = max(len(cumulative_waste_6000), len(cumulative_waste_8000), len(cumulative_waste_13000))
        max_waste = max(all_waste) if all_waste else 1
        max_length = max(max_remaining_lengths) if max_remaining_lengths else 13000
        max_y = max(max_waste, max_length)

        chart.setTitle("Cumulative Waste by Bar Size During Runtime")
        chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
        chart.legend().setVisible(True)

        axis_x = QtCharts.QValueAxis()
        axis_x.setTitleText("Bar Number")
        axis_x.setLabelFormat("%d")
        axis_x.setTickCount(max(2, min(max_bar_count, 10)))
        axis_x.setRange(1, max(1, max_bar_count))

        axis_y = QtCharts.QValueAxis()
        axis_y.setTitleText("Units")
        axis_y.setRange(0, max(1, max_y))

        chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        line_6000.attachAxis(axis_x)
        line_6000.attachAxis(axis_y)
        line_8000.attachAxis(axis_x)
        line_8000.attachAxis(axis_y)
        line_13000.attachAxis(axis_x)
        line_13000.attachAxis(axis_y)

        crossing_points = self.find_milestone_crossings(max_remaining_lengths)
        for threshold, bar_num in crossing_points.items():
            milestone = QtCharts.QLineSeries()
            milestone.setName(f"Below {threshold}")
            milestone.append(bar_num, 0)
            milestone.append(bar_num, max_y)
            pen_milestone = QtGui.QPen(QtGui.QColor("#888888"))
            pen_milestone.setWidth(2)
            pen_milestone.setDashPattern([5, 5])
            milestone.setPen(pen_milestone)
            chart.addSeries(milestone)
            milestone.attachAxis(axis_x)
            milestone.attachAxis(axis_y)

        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        chart_view.setMinimumHeight(260)
        self.chart_layout.addWidget(chart_view)

    def find_milestone_crossings(self, max_remaining_lengths):
        thresholds = [13000, 8000, 6000]
        crossings = {}

        for threshold in thresholds:
            for index, length in enumerate(max_remaining_lengths, start=1):
                if length < threshold and (index == 1 or max_remaining_lengths[index - 2] >= threshold):
                    crossings[threshold] = index
                    break

        return crossings

    def update_bar_usage_runtime_chart(self, selected_bar_sizes):
        try:
            from PySide6 import QtCharts
        except Exception:
            return

        if not selected_bar_sizes:
            return

        set_6000 = QtCharts.QBarSet("6000")
        set_8000 = QtCharts.QBarSet("8000")
        set_13000 = QtCharts.QBarSet("13000")

        set_6000.setColor(QtGui.QColor("#4CAF50"))
        set_8000.setColor(QtGui.QColor("#2196F3"))
        set_13000.setColor(QtGui.QColor("#FF9800"))

        categories = []
        for index, size in enumerate(selected_bar_sizes, start=1):
            categories.append(str(index))
            set_6000.append(6000 if size == 6000 else 0)
            set_8000.append(8000 if size == 8000 else 0)
            set_13000.append(13000 if size == 13000 else 0)

        series = QtCharts.QStackedBarSeries()
        series.append(set_6000)
        series.append(set_8000)
        series.append(set_13000)

        chart = QtCharts.QChart()
        chart.addSeries(series)
        chart.setTitle("Bar Sizes Used During Runtime")
        chart.legend().setVisible(True)

        axis_x = QtCharts.QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setTitleText("Bar Number")

        axis_y = QtCharts.QValueAxis()
        axis_y.setTitleText("Bar Size")
        axis_y.setRange(0, 13000)

        chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QtCharts.QChartView(chart)
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        chart_view.setMinimumHeight(260)
        self.chart_layout.addWidget(chart_view)

    def show_error(self, error_msg):
        self.clear_layout(self.file_info_container.layout())
        self.clear_layout(self.analysis_container.layout())
        self.add_info_box(self.file_info_container.layout(), "Error", error_msg)

    def add_info_box(self, layout, title, value):
        box = QtWidgets.QGroupBox(title)
        box_layout = QtWidgets.QVBoxLayout(box)
        box_layout.setContentsMargins(10, 10, 10, 10)
        box_layout.addWidget(QtWidgets.QLabel(value))
        layout.addWidget(box)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    with open("src/style.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
