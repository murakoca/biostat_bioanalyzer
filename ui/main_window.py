"""
Ana pencere - Modüler sekme tabanlı arayüz
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QIcon

from ui.data_panel import DataPanel
from ui.distribution_panel import DistributionPanel
from ui.hypothesis_panel import HypothesisPanel
from ui.survival_panel import SurvivalPanel
from ui.confounder_panel import ConfounderPanel
from ui.report_panel import ReportPanel
from ui.styles import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BiyoStat Pro — Klinik Veri Analizi")
        self.setMinimumSize(1280, 820)
        self.current_df = None

        self._setup_style()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

    def _setup_style(self):
        self.setStyleSheet(DARK_STYLE)

    def _setup_menu(self):
        menubar = self.menuBar()

        # Dosya Menüsü
        file_menu = menubar.addMenu("📁 Dosya")
        open_action = QAction("Veri Yükle (CSV/Excel)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Hakkında
        help_menu = menubar.addMenu("❓ Yardım")
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._make_header()
        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Panel instances — all share the same df reference via callback
        self.data_panel = DataPanel(on_data_loaded=self._on_data_loaded)
        self.dist_panel = DistributionPanel()
        self.hypo_panel = HypothesisPanel()
        self.surv_panel = SurvivalPanel()
        self.conf_panel = ConfounderPanel()
        self.report_panel = ReportPanel()

        self.tabs.addTab(self.data_panel,    "📂  Veri")
        self.tabs.addTab(self.dist_panel,    "📊  Dağılım")
        self.tabs.addTab(self.hypo_panel,    "🧪  Hipotez")
        self.tabs.addTab(self.surv_panel,    "📈  Sağkalım")
        self.tabs.addTab(self.conf_panel,    "🔗  Confounder")
        self.tabs.addTab(self.report_panel,  "📝  Rapor")

        layout.addWidget(self.tabs)

    def _make_header(self):
        frame = QFrame()
        frame.setObjectName("header")
        frame.setFixedHeight(64)
        h = QHBoxLayout(frame)
        h.setContentsMargins(24, 0, 24, 0)

        title = QLabel("🔬 BiyoStat Pro")
        title.setObjectName("appTitle")
        subtitle = QLabel("Biyoistatistik ve Yapay Zeka Destekli Klinik Veri Analizi")
        subtitle.setObjectName("appSubtitle")

        self.data_badge = QLabel("Veri yüklenmedi")
        self.data_badge.setObjectName("dataBadge")

        h.addWidget(title)
        h.addSpacing(16)
        h.addWidget(subtitle)
        h.addStretch()
        h.addWidget(self.data_badge)
        return frame

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Hazır  |  Veri yüklemek için  Dosya > Veri Yükle  veya  📂 Veri  sekmesini kullanın.")

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Veri Dosyası Seç", "",
            "Tüm Desteklenen (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls)"
        )
        if path:
            self.data_panel.load_file(path)

    def _on_data_loaded(self, df):
        self.current_df = df
        rows, cols = df.shape
        self.data_badge.setText(f"✅  {rows} satır × {cols} sütun")
        self.status.showMessage(f"Veri yüklendi: {rows} satır, {cols} sütun")

        # Propagate to all panels
        for panel in [self.dist_panel, self.hypo_panel,
                      self.surv_panel, self.conf_panel, self.report_panel]:
            panel.set_dataframe(df)

    def _show_about(self):
        QMessageBox.about(
            self, "BiyoStat Pro Hakkında",
            "<h3>BiyoStat Pro v1.0</h3>"
            "<p>Biyoistatistik ve Yapay Zeka Destekli Klinik Veri Analizi</p>"
            "<p>Dr. Yusuf SÜRÜCÜ & Said SÜRÜCÜ eğitim müfredatına dayalı</p>"
            "<hr/>"
            "<b>Modüller:</b><br/>"
            "• Veri Yükleme & Temizleme<br/>"
            "• Dağılım Testleri (Shapiro-Wilk, K-S)<br/>"
            "• Hipotez Testleri (t-test, ANOVA, Ki-kare…)<br/>"
            "• Sağkalım Analizi (Kaplan-Meier, Cox)<br/>"
            "• Confounder Düzeltme (ANCOVA, PSM)<br/>"
            "• Otomatik Rapor Üretimi"
        )
