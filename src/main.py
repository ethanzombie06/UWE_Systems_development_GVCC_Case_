import sys
import pandas as pd
from PySide6 import QtCore, QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Central widget and layout
        central_widget = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central_widget)
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
        self.temp_button.clicked.connect(self.run_temp_function)
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

        central_layout.addStretch()
        self.setCentralWidget(central_widget)

    def run_temp_function(self):
        # Example temp function: show first 5 rows in a dialog
        if hasattr(self, 'loaded_df'):
            temp_result = self.loaded_df.head().to_string()
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Temp Function Result")
            msg_box.setText(temp_result)
            msg_box.exec()
        else:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Temp Function Result")
            msg_box.setText("No data loaded.")
            msg_box.exec()

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
        total_length = df['PartLength'].sum()
        avg_length = df['PartLength'].mean()
        total_count = df['Count'].sum()
        self.update_file_info(csv_path, len(df))
        self.update_analysis(total_length, avg_length, total_count)

    def update_file_info(self, csv_path, row_count):
        self.clear_layout(self.file_info_container.layout())
        self.add_info_box(self.file_info_container.layout(), "File Loaded", csv_path)
        self.add_info_box(self.file_info_container.layout(), "Rows", str(row_count))

    def update_analysis(self, total_length, avg_length, total_count):
        self.clear_layout(self.analysis_container.layout())
        analysis = [
            ("Total Length", f"{total_length}"),
            ("Average Length", f"{avg_length:.2f}"),
            ("Total Count", f"{total_count}")
        ]
        for title, value in analysis:
            self.add_info_box(self.analysis_container.layout(), title, value)

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
