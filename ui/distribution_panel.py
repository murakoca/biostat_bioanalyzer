"""
Dağılım Testleri Paneli — Shapiro-Wilk, K-S, QQ Plot, Histogram
"""
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QSplitter, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from scipy import stats


class DistributionPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self._build_ui()

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        self.combo_col.clear()
        self.combo_col.addItems(num_cols)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("📊 Dağılım Testleri")
        hdr.setObjectName("sectionTitle")
        layout.addWidget(hdr)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Değişken:"))
        self.combo_col = QComboBox()
        self.combo_col.setMinimumWidth(200)
        ctrl.addWidget(self.combo_col)

        ctrl.addWidget(QLabel("Test:"))
        self.combo_test = QComboBox()
        self.combo_test.addItems(["Shapiro-Wilk", "Kolmogorov-Smirnov", "Her İkisi"])
        ctrl.addWidget(self.combo_test)

        btn_run = QPushButton("▶  Testi Çalıştır")
        btn_run.setObjectName("primaryBtn")
        btn_run.clicked.connect(self._run_test)
        ctrl.addWidget(btn_run)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Splitter: results | plots
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Results
        grp_res = QGroupBox("Test Sonuçları")
        rv = QVBoxLayout(grp_res)
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setMaximumWidth(320)
        rv.addWidget(self.txt_result)
        splitter.addWidget(grp_res)

        # Plot area
        self.fig = Figure(figsize=(10, 5), facecolor="#0f1117")
        self.canvas = FigureCanvas(self.fig)
        splitter.addWidget(self.canvas)
        splitter.setSizes([320, 900])

        layout.addWidget(splitter)

    def _run_test(self):
        if self.df is None:
            self.txt_result.setText("⚠ Önce veri yükleyin.")
            return
        col = self.combo_col.currentText()
        if not col:
            return
        data = self.df[col].dropna().values

        result_text = f"Değişken: {col}\nn = {len(data)}\n\n"

        test = self.combo_test.currentText()

        if test in ["Shapiro-Wilk", "Her İkisi"]:
            stat, p = stats.shapiro(data[:5000])  # SW max 5000
            norm_sw = p > 0.05
            result_text += (
                "── Shapiro-Wilk ──\n"
                f"W = {stat:.4f}\n"
                f"p = {p:.4f}\n"
                f"{'✅ Normal dağılım' if norm_sw else '❌ Normal DEĞİL'}\n\n"
            )

        if test in ["Kolmogorov-Smirnov", "Her İkisi"]:
            stat_ks, p_ks = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
            norm_ks = p_ks > 0.05
            result_text += (
                "── Kolmogorov-Smirnov ──\n"
                f"D = {stat_ks:.4f}\n"
                f"p = {p_ks:.4f}\n"
                f"{'✅ Normal dağılım' if norm_ks else '❌ Normal DEĞİL'}\n\n"
            )

        result_text += "── Tanımlayıcı İstatistikler ──\n"
        result_text += f"Ortalama: {data.mean():.3f}\n"
        result_text += f"Medyan:   {np.median(data):.3f}\n"
        result_text += f"SD:       {data.std():.3f}\n"
        result_text += f"Min:      {data.min():.3f}\n"
        result_text += f"Max:      {data.max():.3f}\n"
        result_text += f"Çarpıklık: {stats.skew(data):.3f}\n"
        result_text += f"Basıklık:  {stats.kurtosis(data):.3f}\n"

        self.txt_result.setText(result_text)
        self._draw_plots(data, col)

    def _draw_plots(self, data, col):
        self.fig.clear()
        self.fig.patch.set_facecolor("#0f1117")

        axes = self.fig.subplots(1, 3)
        plot_style = {"facecolor": "#111827", "edgecolor": "#1e293b"}
        text_color = "#94a3b8"

        for ax in axes:
            ax.set_facecolor("#111827")
            ax.tick_params(colors=text_color, labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor("#1e293b")

        # Histogram + KDE
        ax1 = axes[0]
        ax1.hist(data, bins=20, color="#3b82f6", alpha=0.7, edgecolor="#1e3a5f")
        kde_x = np.linspace(data.min(), data.max(), 200)
        kde_y = stats.gaussian_kde(data)(kde_x)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(kde_x, kde_y, color="#f59e0b", linewidth=2)
        ax1_twin.set_yticks([])
        ax1_twin.tick_params(colors=text_color)
        ax1.set_title(f"Histogram + KDE\n{col}", color="#e2e8f0", fontsize=9)
        ax1.set_xlabel(col, color=text_color, fontsize=8)

        # Box Plot
        ax2 = axes[1]
        bp = ax2.boxplot(data, vert=True, patch_artist=True,
                         boxprops=dict(facecolor="#1e3a5f", color="#3b82f6"),
                         whiskerprops=dict(color="#60a5fa"),
                         capprops=dict(color="#60a5fa"),
                         medianprops=dict(color="#f59e0b", linewidth=2),
                         flierprops=dict(marker='o', color="#ef4444", markersize=4))
        ax2.set_title(f"Box Plot\n{col}", color="#e2e8f0", fontsize=9)
        ax2.set_xticks([])

        # QQ Plot
        ax3 = axes[2]
        (osm, osr), (slope, intercept, r) = stats.probplot(data, dist="norm")
        ax3.scatter(osm, osr, color="#3b82f6", s=8, alpha=0.7)
        line_x = np.array([osm[0], osm[-1]])
        ax3.plot(line_x, slope * line_x + intercept, color="#f59e0b", linewidth=2)
        ax3.set_title(f"Q-Q Plot\nR² = {r**2:.4f}", color="#e2e8f0", fontsize=9)
        ax3.set_xlabel("Teorik Quantile", color=text_color, fontsize=8)
        ax3.set_ylabel("Örnek Quantile", color=text_color, fontsize=8)

        self.fig.tight_layout(pad=1.5)
        self.canvas.draw()
