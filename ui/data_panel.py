"""
Veri Yükleme & Önizleme Paneli
"""
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QGroupBox,
    QComboBox, QSplitter, QTextEdit, QHeaderView, QFrame,
    QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class DataPanel(QWidget):
    def __init__(self, on_data_loaded=None):
        super().__init__()
        self.on_data_loaded = on_data_loaded
        self.df = None
        self.df_clean = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.lbl_file = QLabel("Dosya seçilmedi")
        self.lbl_file.setObjectName("infoLabel")

        btn_open = QPushButton("📂  Dosya Aç")
        btn_open.setObjectName("primaryBtn")
        btn_open.clicked.connect(self._open_file)

        btn_sample = QPushButton("🧪  Örnek Veri")
        btn_sample.clicked.connect(self._load_sample)

        toolbar.addWidget(btn_open)
        toolbar.addWidget(btn_sample)
        toolbar.addSpacing(16)
        toolbar.addWidget(self.lbl_file)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Splitter: table left, info right
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        splitter.addWidget(self.table)

        # Right panel
        right = QWidget()
        right.setMaximumWidth(340)
        rv = QVBoxLayout(right)
        rv.setSpacing(10)

        # Stats group
        grp_stats = QGroupBox("Veri Özeti")
        sv = QVBoxLayout(grp_stats)
        self.lbl_stats = QTextEdit()
        self.lbl_stats.setReadOnly(True)
        self.lbl_stats.setMaximumHeight(200)
        sv.addWidget(self.lbl_stats)
        rv.addWidget(grp_stats)

        # Clean group
        grp_clean = QGroupBox("Veri Temizleme")
        cv = QVBoxLayout(grp_clean)
        self.chk_dropna = QCheckBox("Eksik satırları sil (na.omit)")
        self.chk_dropna.setChecked(True)
        self.chk_fillna = QCheckBox("Sayısal NaN → Medyan ile doldur")

        btn_clean = QPushButton("🧹  Temizle & Uygula")
        btn_clean.setObjectName("primaryBtn")
        btn_clean.clicked.connect(self._apply_clean)

        cv.addWidget(self.chk_dropna)
        cv.addWidget(self.chk_fillna)
        cv.addWidget(btn_clean)
        rv.addWidget(grp_clean)

        # Column types
        grp_types = QGroupBox("Sütun Tipleri")
        tv = QVBoxLayout(grp_types)
        self.lbl_types = QTextEdit()
        self.lbl_types.setReadOnly(True)
        tv.addWidget(self.lbl_types)
        rv.addWidget(grp_types)

        splitter.addWidget(right)
        splitter.setSizes([900, 340])
        layout.addWidget(splitter)

    # ── Public API ────────────────────────────────────────────────────────

    def load_file(self, path: str):
        try:
            if path.endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            self.df = df
            self.df_clean = df.copy()
            self.lbl_file.setText(f"📄  {path.split('/')[-1]}")
            self._show_table(df)
            self._show_summary(df)
            if self.on_data_loaded:
                self.on_data_loaded(df)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Dosya okunamadı:\n{e}")

    def set_dataframe(self, df):
        pass  # DataPanel is the source; other panels receive

    # ── Private ────────────────────────────────────────────────────────────

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Veri Dosyası Seç", "",
            "CSV / Excel (*.csv *.xlsx *.xls)"
        )
        if path:
            self.load_file(path)

    def _load_sample(self):
        """Dahili örnek klinik veri seti oluştur"""
        np.random.seed(42)
        n = 120
        df = pd.DataFrame({
            "hasta_id":    range(1, n + 1),
            "yas":         np.random.randint(30, 80, n),
            "cinsiyet":    np.random.choice(["Erkek", "Kadın"], n),
            "tedavi_grubu": np.random.choice(["Kontrol", "Tedavi_A", "Tedavi_B"], n),
            "bmi":         np.round(np.random.normal(26.5, 4.5, n), 1),
            "kan_basinci": np.random.randint(80, 160, n),
            "kolesterol":  np.random.normal(200, 35, n).round(1),
            "glukoz":      np.random.normal(100, 20, n).round(1),
            "sigara":      np.random.choice([0, 1], n, p=[0.65, 0.35]),
            "surv_sure":   np.random.exponential(24, n).round(1),
            "surv_olay":   np.random.choice([0, 1], n, p=[0.4, 0.6]),
            "sonuc":       np.random.choice(["İyi", "Orta", "Kötü"], n, p=[0.5, 0.3, 0.2]),
        })
        # Bazı eksik değerler ekle
        for col in ["bmi", "kolesterol", "glukoz"]:
            idx = np.random.choice(n, 5, replace=False)
            df.loc[idx, col] = np.nan

        self.df = df
        self.df_clean = df.copy()
        self.lbl_file.setText("🧪  Örnek Klinik Veri (n=120)")
        self._show_table(df)
        self._show_summary(df)
        if self.on_data_loaded:
            self.on_data_loaded(df)

    def _show_table(self, df: pd.DataFrame):
        preview = df.head(200)
        self.table.setRowCount(len(preview))
        self.table.setColumnCount(len(preview.columns))
        self.table.setHorizontalHeaderLabels(list(preview.columns))

        for i, row in preview.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val) if pd.notna(val) else "NaN")
                if pd.isna(val):
                    item.setForeground(QColor("#f87171"))
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def _show_summary(self, df: pd.DataFrame):
        rows, cols = df.shape
        missing = df.isnull().sum().sum()
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        categ_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        summary = (
            f"Satır: {rows}  |  Sütun: {cols}\n"
            f"Eksik değer: {missing}\n"
            f"Sayısal: {len(numeric_cols)}\n"
            f"Kategorik: {len(categ_cols)}\n\n"
        )
        if numeric_cols:
            summary += "── Sayısal İstatistikler ──\n"
            for col in numeric_cols[:6]:
                summary += f"{col}: μ={df[col].mean():.1f}  σ={df[col].std():.1f}\n"

        self.lbl_stats.setText(summary)

        types_text = ""
        for col in df.columns:
            dtype = str(df[col].dtype)
            tag = "📊" if dtype.startswith("float") or dtype.startswith("int") else "🔤"
            types_text += f"{tag}  {col}  [{dtype}]\n"
        self.lbl_types.setText(types_text)

    def _apply_clean(self):
        if self.df is None:
            return
        df = self.df.copy()
        if self.chk_dropna.isChecked():
            df = df.dropna()
        if self.chk_fillna.isChecked():
            for col in df.select_dtypes(include=np.number).columns:
                df[col] = df[col].fillna(df[col].median())
        self.df_clean = df
        self._show_table(df)
        self._show_summary(df)
        if self.on_data_loaded:
            self.on_data_loaded(df)
