"""
Sağkalım Analizi Paneli — Kaplan-Meier, Log-rank, Cox Regresyon
"""
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
    from lifelines.statistics import logrank_test
    LIFELINES_OK = True
except ImportError:
    LIFELINES_OK = False


class SurvivalPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self._build_ui()

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        for combo in [self.combo_time, self.combo_event, self.combo_group, self.combo_cov]:
            combo.clear()
        self.combo_time.addItems(num_cols)
        self.combo_event.addItems(num_cols)
        self.combo_group.addItems(["(Tümü)"] + cols)
        self.combo_cov.addItems(num_cols)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("📈 Sağkalım Analizi")
        hdr.setObjectName("sectionTitle")
        layout.addWidget(hdr)

        if not LIFELINES_OK:
            layout.addWidget(QLabel("⚠ lifelines kütüphanesi kurulu değil: pip install lifelines"))

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Süre:"))
        self.combo_time = QComboBox(); self.combo_time.setMinimumWidth(130)
        ctrl.addWidget(self.combo_time)

        ctrl.addWidget(QLabel("Olay (0/1):"))
        self.combo_event = QComboBox(); self.combo_event.setMinimumWidth(130)
        ctrl.addWidget(self.combo_event)

        ctrl.addWidget(QLabel("Gruplama:"))
        self.combo_group = QComboBox(); self.combo_group.setMinimumWidth(130)
        ctrl.addWidget(self.combo_group)

        btn_km = QPushButton("📊  Kaplan-Meier")
        btn_km.setObjectName("primaryBtn")
        btn_km.clicked.connect(self._run_km)
        ctrl.addWidget(btn_km)

        ctrl.addWidget(QLabel("Kovaryat (Cox):"))
        self.combo_cov = QComboBox(); self.combo_cov.setMinimumWidth(130)
        ctrl.addWidget(self.combo_cov)

        btn_cox = QPushButton("🔬  Cox Regresyon")
        btn_cox.clicked.connect(self._run_cox)
        ctrl.addWidget(btn_cox)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Split
        splitter = QSplitter(Qt.Orientation.Horizontal)

        grp = QGroupBox("Sonuçlar")
        gv = QVBoxLayout(grp)
        self.txt = QTextEdit(); self.txt.setReadOnly(True)
        self.txt.setMinimumWidth(340)
        gv.addWidget(self.txt)
        splitter.addWidget(grp)

        self.fig = Figure(figsize=(9, 5), facecolor="#0f1117")
        self.canvas = FigureCanvas(self.fig)
        splitter.addWidget(self.canvas)
        splitter.setSizes([380, 900])
        layout.addWidget(splitter)

    def _ax_style(self, ax):
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for s in ax.spines.values():
            s.set_edgecolor("#1e293b")

    def _run_km(self):
        if not LIFELINES_OK:
            self.txt.setText("❌ lifelines kurulu değil.")
            return
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return

        t_col = self.combo_time.currentText()
        e_col = self.combo_event.currentText()
        g_col = self.combo_group.currentText()

        if not t_col or not e_col:
            self.txt.setText("⚠ Lütfen süre ve olay sütunlarını seçin.")
            return

        # Sütunları sayısala çevir, geçersizleri at
        df = self.df[[t_col, e_col] + ([g_col] if g_col != "(Tümü)" else [])].copy()
        df[t_col] = pd.to_numeric(df[t_col], errors='coerce')
        df[e_col] = pd.to_numeric(df[e_col], errors='coerce')
        df = df.dropna(subset=[t_col, e_col])
        df[e_col] = df[e_col].astype(int)

        if df.empty:
            self.txt.setText("⚠ Geçerli sayısal veri bulunamadı.")
            return
        if not df[e_col].isin([0, 1]).all():
            self.txt.setText("❌ Olay sütunu yalnızca 0 ve 1 değerlerinden oluşmalıdır.")
            return

        T = df[t_col]
        E = df[e_col]

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        self._ax_style(ax)

        result_text = f"Kaplan-Meier Analizi\nSüre: {t_col}  Olay: {e_col}\n\n"
        colors = ["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6"]

        if g_col == "(Tümü)":
            kmf = KaplanMeierFitter()
            kmf.fit(T, E, label="Tüm Kohort")
            kmf.plot_survival_function(ax=ax, color=colors[0], ci_show=True,
                                       ci_alpha=0.15, linewidth=2)
            result_text += f"Medyan sağkalım: {kmf.median_survival_time_:.2f}\n"
            result_text += f"n = {len(T)}\n"
        else:
            groups = df[g_col].unique()
            kmfs = []
            for i, grp in enumerate(groups):
                mask = df[g_col] == grp
                if mask.sum() == 0:
                    continue
                kmf = KaplanMeierFitter()
                kmf.fit(T.loc[mask], E.loc[mask], label=str(grp))
                kmf.plot_survival_function(ax=ax, color=colors[i % len(colors)],
                                           ci_show=True, ci_alpha=0.1, linewidth=2)
                kmfs.append((grp, kmf, T.loc[mask], E.loc[mask]))
                result_text += f"Grup {grp}: Medyan = {kmf.median_survival_time_:.2f}  n={mask.sum()}\n"

            if len(kmfs) >= 2:
                g1, _, T1, E1 = kmfs[0]
                g2, _, T2, E2 = kmfs[1]
                lr = logrank_test(T1, T2, E1, E2)
                result_text += (
                    f"\n── Log-rank Testi ──\n"
                    f"({g1} vs {g2})\n"
                    f"p = {lr.p_value:.4f}\n"
                    f"{'✅ Anlamlı fark' if lr.p_value < 0.05 else '❌ Anlamlı fark yok'}\n"
                )

        ax.set_xlabel("Zaman", color="#94a3b8", fontsize=9)
        ax.set_ylabel("Sağkalım Olasılığı", color="#94a3b8", fontsize=9)
        ax.set_title("Kaplan-Meier Eğrisi", color="#e2e8f0", fontsize=11)
        ax.set_ylim(0, 1.05)
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor("#1e293b")
            for text in legend.get_texts():
                text.set_color("#e2e8f0")
        ax.grid(True, alpha=0.1, color="#334155")

        self.fig.tight_layout()
        self.canvas.draw()
        self.txt.setText(result_text)

    def _run_cox(self):
        if not LIFELINES_OK:
            self.txt.setText("❌ lifelines kurulu değil.")
            return
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return

        t_col = self.combo_time.currentText()
        e_col = self.combo_event.currentText()
        cov_col = self.combo_cov.currentText()

        if not t_col or not e_col or not cov_col:
            self.txt.setText("⚠ Lütfen süre, olay ve kovaryat sütunlarını seçin.")
            return

        df = self.df[[t_col, e_col, cov_col]].copy()
        df[t_col] = pd.to_numeric(df[t_col], errors='coerce')
        df[e_col] = pd.to_numeric(df[e_col], errors='coerce')
        df[cov_col] = pd.to_numeric(df[cov_col], errors='coerce')
        df = df.dropna()
        df[e_col] = df[e_col].astype(int)

        if df.empty:
            self.txt.setText("⚠ Geçerli sayısal veri bulunamadı.")
            return
        if not df[e_col].isin([0, 1]).all():
            self.txt.setText("❌ Olay sütunu yalnızca 0 ve 1 değerlerinden oluşmalıdır.")
            return

        try:
            cph = CoxPHFitter()
            cph.fit(df, duration_col=t_col, event_col=e_col)

            self.fig.clear()
            ax = self.fig.add_subplot(111)
            self.fig.patch.set_facecolor("#0f1117")
            self._ax_style(ax)
            cph.plot(ax=ax)
            ax.set_title("Cox Model — Hazard Oranları", color="#e2e8f0")
            ax.set_facecolor("#111827")
            ax.tick_params(colors="#94a3b8")
            self.fig.tight_layout()
            self.canvas.draw()

            result_text = "Cox Orantılı Hazard Modeli\n\n"
            result_text += f"Concordance: {cph.concordance_index_:.4f}\n"
            result_text += f"Log-Likelihood: {cph.log_likelihood_:.4f}\n\n"
            result_text += "Katsayılar:\n"
            result_text += cph.summary[["coef","exp(coef)","p"]].to_string()
            self.txt.setText(result_text)
        except Exception as e:
            self.txt.setText(f"❌ Cox hatası: {e}")