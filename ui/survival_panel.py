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
        
        # Uygun sütunları belirle
        all_cols = df.columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Binary (0/1) sütunları bul - olay sütunu için
        binary_cols = []
        for col in numeric_cols:
            unique_vals = df[col].dropna().unique()
            if set(unique_vals).issubset({0, 1}):
                binary_cols.append(col)
        
        # Pozitif sayısal sütunlar - süre için (opsiyonel: >0 kontrolü)
        time_cols = []
        for col in numeric_cols:
            # En az 2 farklı değer olsun ve pozitif olsun
            if df[col].nunique() > 1 and df[col].min() > 0:
                time_cols.append(col)
            elif df[col].nunique() > 1:  # Pozitif değilse de ekle ama uyarı gösterme
                time_cols.append(col)
        
        # Dropdownları temizle ve doldur
        self.combo_time.clear()
        self.combo_event.clear()
        self.combo_group.clear()
        self.combo_cov.clear()
        
        # Süre sütunları (sayısal)
        self.combo_time.addItems(time_cols if time_cols else numeric_cols)
        if not time_cols and numeric_cols:
            # Uyarı mesajı göster
            self.txt.setText("⚠ Uyarı: Uygun süre sütunu bulunamadı. Sayısal sütunlar listeleniyor.")
        
        # Olay sütunları (sadece binary 0/1)
        if binary_cols:
            self.combo_event.addItems(binary_cols)
        else:
            self.combo_event.addItem("❌ Uygun binary (0/1) sütun yok")
            self.combo_event.setEnabled(False)
        
        # Gruplama sütunları (tüm sütunlar + Tümü)
        self.combo_group.addItem("(Tümü)")
        self.combo_group.addItems(all_cols)
        
        # Kovaryat sütunları (sayısal)
        self.combo_cov.addItems(numeric_cols)
        
        # Eğer hiç binary sütun yoksa kullanıcıyı bilgilendir
        if not binary_cols:
            self.txt.setText("⚠ Bilgi: Olay (event) için 0/1 değeri içeren binary bir sütun bulunamadı.\n\n"
                           "Sağkalım analizi için verinizde 'surv_olay', 'ölüm', 'status' gibi 0/1 değerli bir sütun olmalıdır.\n\n"
                           "Örnek veri setinde 'surv_olay' sütunu bu amaçla kullanılabilir.")

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
        self.combo_time = QComboBox()
        self.combo_time.setMinimumWidth(130)
        self.combo_time.setToolTip("Sağkalım süresi (gün, ay, yıl gibi pozitif sayısal değerler)")
        ctrl.addWidget(self.combo_time)

        ctrl.addWidget(QLabel("Olay (0/1):"))
        self.combo_event = QComboBox()
        self.combo_event.setMinimumWidth(130)
        self.combo_event.setToolTip("Sadece 0 ve 1 değerleri içeren binary sütun (0: sansürlü, 1: olay)")
        ctrl.addWidget(self.combo_event)

        ctrl.addWidget(QLabel("Gruplama:"))
        self.combo_group = QComboBox()
        self.combo_group.setMinimumWidth(130)
        self.combo_group.setToolTip("Gruplama yapılacak sütun (opsiyonel)")
        ctrl.addWidget(self.combo_group)

        btn_km = QPushButton("📊  Kaplan-Meier")
        btn_km.setObjectName("primaryBtn")
        btn_km.clicked.connect(self._run_km)
        ctrl.addWidget(btn_km)

        ctrl.addWidget(QLabel("Kovaryat (Cox):"))
        self.combo_cov = QComboBox()
        self.combo_cov.setMinimumWidth(130)
        self.combo_cov.setToolTip("Cox regresyon için bağımsız değişken (sayısal)")
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
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
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

    def _show_error(self, msg):
        """Display user‑friendly error message in result area."""
        self.txt.setText(f"❌ {msg}\n\nLütfen doğru sütunları seçiniz.\n\n"
                         f"• Süre: Pozitif sayısal değerler (örn: surv_sure)\n"
                         f"• Olay: Sadece 0 ve 1 değerleri (örn: surv_olay)\n"
                         f"• Gruplama: İsteğe bağlı, kategorik veya sayısal\n"
                         f"• Kovaryat: Sayısal değişken (örn: yas, bmi)")

    def _get_series(self, df, col):
        """Safely extract a Series from a DataFrame column."""
        if col not in df.columns:
            return None
        series = df[col]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        return series

    def _validate_binary_column(self, df, col):
        """Bir sütunun binary (0/1) olup olmadığını kontrol et."""
        series = self._get_series(df, col)
        if series is None:
            return False, []
        unique_vals = series.dropna().unique()
        is_binary = set(unique_vals).issubset({0, 1})
        return is_binary, unique_vals

    def _run_km(self):
        if not LIFELINES_OK:
            self.txt.setText("❌ lifelines kütüphanesi yüklü değil.\n\nKurulum: pip install lifelines")
            return
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return

        t_col = self.combo_time.currentText()
        e_col = self.combo_event.currentText()
        g_col = self.combo_group.currentText()

        # Binary sütun kontrolü
        is_binary, unique_vals = self._validate_binary_column(self.df, e_col)
        if not is_binary:
            if "❌" in e_col or not e_col:
                self._show_error("Olay sütunu seçilmedi veya uygun binary sütun bulunamadı.")
            else:
                self._show_error(f"Olay sütunu '{e_col}' yalnızca 0 ve 1 değerlerini içermelidir.\n"
                               f"Mevcut değerler: {unique_vals[:10]}...")
            return

        if not t_col or not e_col:
            self._show_error("Süre ve olay sütunları seçilmelidir.")
            return

        # Column existence check
        if t_col not in self.df.columns:
            self._show_error(f"'{t_col}' sütunu veride bulunamadı.")
            return
        if e_col not in self.df.columns:
            self._show_error(f"'{e_col}' sütunu veride bulunamadı.")
            return

        # Convert to numeric
        try:
            time_vals = pd.to_numeric(self.df[t_col].values, errors='coerce')
            event_vals = pd.to_numeric(self.df[e_col].values, errors='coerce')
        except Exception:
            self._show_error(f"'{t_col}' veya '{e_col}' sütunu sayısal değere dönüştürülemedi.")
            return

        # Build working DataFrame
        df = pd.DataFrame({t_col: time_vals, e_col: event_vals})
        if g_col != "(Tümü)":
            if g_col not in self.df.columns:
                self._show_error(f"'{g_col}' sütunu veride bulunamadı.")
                return
            df[g_col] = self.df[g_col]

        # Drop rows with missing time or event
        df = df.dropna(subset=[t_col, e_col])
        if len(df) == 0:
            self._show_error("Seçilen sütunlarda geçerli sayısal veri yok.")
            return

        T = self._get_series(df, t_col)
        E = self._get_series(df, e_col).astype(int)

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
            group_series = self._get_series(df, g_col)
            groups = group_series.unique()
            kmfs = []
            for i, grp in enumerate(groups):
                mask = group_series == grp
                if mask.sum() == 0:
                    continue
                kmf = KaplanMeierFitter()
                kmf.fit(T[mask], E[mask], label=str(grp))
                kmf.plot_survival_function(ax=ax, color=colors[i % len(colors)],
                                           ci_show=True, ci_alpha=0.1, linewidth=2)
                kmfs.append((grp, kmf, T[mask], E[mask]))
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
            self.txt.setText("❌ lifelines kütüphanesi yüklü değil.\n\nKurulum: pip install lifelines")
            return
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return

        t_col = self.combo_time.currentText()
        e_col = self.combo_event.currentText()
        cov_col = self.combo_cov.currentText()

        # Binary sütun kontrolü
        is_binary, unique_vals = self._validate_binary_column(self.df, e_col)
        if not is_binary:
            if "❌" in e_col or not e_col:
                self._show_error("Olay sütunu seçilmedi veya uygun binary sütun bulunamadı.")
            else:
                self._show_error(f"Olay sütunu '{e_col}' yalnızca 0 ve 1 değerlerini içermelidir.\n"
                               f"Mevcut değerler: {unique_vals[:10]}...")
            return

        if not t_col or not e_col or not cov_col:
            self._show_error("Süre, olay ve kovaryat sütunlarının tümü seçilmelidir.")
            return

        for col in [t_col, e_col, cov_col]:
            if col not in self.df.columns:
                self._show_error(f"'{col}' sütunu veride bulunamadı.")
                return

        try:
            time_vals = pd.to_numeric(self.df[t_col].values, errors='coerce')
            event_vals = pd.to_numeric(self.df[e_col].values, errors='coerce')
            cov_vals = pd.to_numeric(self.df[cov_col].values, errors='coerce')
        except Exception:
            self._show_error(f"Seçilen sütunlardan biri sayısal değere dönüştürülemedi.")
            return

        df = pd.DataFrame({
            t_col: time_vals,
            e_col: event_vals,
            cov_col: cov_vals
        }).dropna()

        if df.empty:
            self._show_error("Seçilen sütunlarda geçerli sayısal veri yok.")
            return

        df[e_col] = df[e_col].astype(int)

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
            self._show_error(f"Cox regresyon hatası: {str(e)[:200]}\n\n"
                           f"Olası nedenler: yetersiz gözlem sayısı, sabit kovaryat, "
                           f"veya veri yapısı uygun değil.")