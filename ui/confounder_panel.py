"""
Confounder Analizi Paneli — ANCOVA, PSM, Adjusted OR/β
"""
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QSplitter, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import statsmodels.api as sm
import statsmodels.formula.api as smf


class ConfounderPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self._build_ui()

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        all_cols = df.columns.tolist()

        for combo in [self.combo_outcome, self.combo_exposure]:
            combo.clear()
        self.combo_outcome.addItems(num_cols)
        self.combo_exposure.addItems(all_cols)

        self.list_confounders.clear()
        for col in all_cols:
            item = QListWidgetItem(col)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_confounders.addItem(item)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("🔗 Confounder Analizi")
        hdr.setObjectName("sectionTitle")
        layout.addWidget(hdr)

        info = QLabel(
            "Confounder: Sonuç ve maruz kalma değişkeniyle ilişkili, "
            "gruplar arasında eşit dağılmayan karıştırıcı değişken."
        )
        info.setObjectName("infoLabel")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Sonuç (Y):"))
        self.combo_outcome = QComboBox(); self.combo_outcome.setMinimumWidth(140)
        ctrl.addWidget(self.combo_outcome)

        ctrl.addWidget(QLabel("Maruz Kalma (X):"))
        self.combo_exposure = QComboBox(); self.combo_exposure.setMinimumWidth(140)
        ctrl.addWidget(self.combo_exposure)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: confounder list + buttons
        left = QWidget(); left.setMaximumWidth(280)
        lv = QVBoxLayout(left)
        lv.addWidget(QLabel("Confounder Listesi (seç):"))
        self.list_confounders = QListWidget()
        lv.addWidget(self.list_confounders)

        btn_crude = QPushButton("📊  Ham Model (Crude)")
        btn_crude.clicked.connect(self._run_crude)
        btn_ancova = QPushButton("🔬  ANCOVA (Düzeltilmiş)")
        btn_ancova.setObjectName("primaryBtn")
        btn_ancova.clicked.connect(self._run_ancova)
        btn_psm = QPushButton("⚖  PSM Analizi")
        btn_psm.clicked.connect(self._run_psm)

        lv.addWidget(btn_crude)
        lv.addWidget(btn_ancova)
        lv.addWidget(btn_psm)
        splitter.addWidget(left)

        # Middle: results
        grp = QGroupBox("Analiz Sonuçları")
        gv = QVBoxLayout(grp)
        self.txt = QTextEdit(); self.txt.setReadOnly(True)
        gv.addWidget(self.txt)
        splitter.addWidget(grp)

        # Right: plot
        self.fig = Figure(figsize=(7, 5), facecolor="#0f1117")
        self.canvas = FigureCanvas(self.fig)
        splitter.addWidget(self.canvas)
        splitter.setSizes([280, 400, 700])
        layout.addWidget(splitter)

    def _get_confounders(self):
        selected = []
        for i in range(self.list_confounders.count()):
            item = self.list_confounders.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def _run_crude(self):
        if self.df is None:
            return
        y = self.combo_outcome.currentText()
        x = self.combo_exposure.currentText()
        try:
            df = self.df[[y, x]].dropna()
            # Encode categorical
            if df[x].dtype == object:
                df = pd.get_dummies(df, columns=[x], drop_first=True)
                x_cols = [c for c in df.columns if c != y]
            else:
                x_cols = [x]

            X = sm.add_constant(df[x_cols])
            model = sm.OLS(df[y], X).fit()

            out = "── Ham Model (Crude) ──\n"
            out += f"Bağımlı: {y}  |  Bağımsız: {x}\n\n"
            out += f"R² = {model.rsquared:.4f}\n"
            out += f"F = {model.fvalue:.4f}  p = {model.f_pvalue:.4f}\n\n"
            out += model.summary2().tables[1].to_string()
            self.txt.setText(out)
            self._plot_coef(model, title="Ham Model — Katsayılar")
        except Exception as e:
            self.txt.setText(f"❌ {e}")

    def _run_ancova(self):
        if self.df is None:
            return
        y = self.combo_outcome.currentText()
        x = self.combo_exposure.currentText()
        confounders = self._get_confounders()

        try:
            cols = list(set([y, x] + confounders))
            df = self.df[cols].dropna()

            x_cols = [x] + confounders
            # Encode object columns
            for col in x_cols[:]:
                if df[col].dtype == object:
                    dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                    df = pd.concat([df.drop(col, axis=1), dummies], axis=1)
                    x_cols = [c for c in df.columns if c != y]

            X = sm.add_constant(df[x_cols])
            model = sm.OLS(df[y], X).fit()

            out = "── ANCOVA (Düzeltilmiş Model) ──\n"
            out += f"Bağımlı: {y}\n"
            out += f"Maruz kalma: {x}\n"
            out += f"Confounder'lar: {', '.join(confounders) if confounders else 'Yok'}\n\n"
            out += f"Adjusted R² = {model.rsquared_adj:.4f}\n"
            out += f"F = {model.fvalue:.4f}  p = {model.f_pvalue:.4f}\n\n"
            out += model.summary2().tables[1].to_string()
            self.txt.setText(out)
            self._plot_coef(model, title="Düzeltilmiş Model — Katsayılar")
        except Exception as e:
            self.txt.setText(f"❌ {e}")

    def _run_psm(self):
        """Propensity Score Matching (basit logistic-based)"""
        if self.df is None:
            return
        x = self.combo_exposure.currentText()
        confounders = self._get_confounders()

        if not confounders:
            self.txt.setText("⚠ PSM için en az 1 confounder seçin.")
            return

        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler

            cols = [x] + confounders
            df = self.df[cols].dropna().copy()

            # Binary treatment
            if df[x].dtype == object or df[x].nunique() > 2:
                self.txt.setText("⚠ PSM için maruz kalma ikili (binary) olmalıdır.")
                return

            y_ps = df[x].values.astype(int)
            X_ps = df[confounders].select_dtypes(include=np.number).values
            scaler = StandardScaler()
            X_ps = scaler.fit_transform(X_ps)

            lr = LogisticRegression()
            lr.fit(X_ps, y_ps)
            ps = lr.predict_proba(X_ps)[:, 1]
            df["propensity_score"] = ps

            # Caliper matching (greedy)
            treated = df[df[x] == 1].copy()
            control = df[df[x] == 0].copy()

            matched_control = []
            caliper = 0.05
            for ps_t in treated["propensity_score"]:
                diffs = abs(control["propensity_score"] - ps_t)
                closest_idx = diffs.idxmin()
                if diffs[closest_idx] <= caliper:
                    matched_control.append(closest_idx)
                    control = control.drop(closest_idx)

            out = "── Propensity Score Matching ──\n\n"
            out += f"Toplam: {len(df)}\n"
            out += f"Tedavi grubu: {len(treated)}\n"
            out += f"Kontrol grubu: {len(control)}\n"
            out += f"Eşleştirilen: {len(matched_control)} çift\n"
            out += f"Caliper: {caliper}\n\n"
            out += "PS Özeti:\n"
            out += f"Tedavi PS: {treated['propensity_score'].mean():.3f} ± {treated['propensity_score'].std():.3f}\n"
            out += f"Kontrol PS: {df[df[x]==0]['propensity_score'].mean():.3f} ± {df[df[x]==0]['propensity_score'].std():.3f}\n"
            self.txt.setText(out)

            # PS distribution plot
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            self.fig.patch.set_facecolor("#0f1117")
            ax.set_facecolor("#111827")
            ax.tick_params(colors="#94a3b8", labelsize=8)
            for s in ax.spines.values(): s.set_edgecolor("#1e293b")

            ax.hist(treated["propensity_score"], bins=20, alpha=0.6, color="#3b82f6", label="Tedavi")
            ax.hist(df[df[x]==0]["propensity_score"], bins=20, alpha=0.6, color="#f59e0b", label="Kontrol")
            ax.set_title("Propensity Score Dağılımı", color="#e2e8f0")
            ax.set_xlabel("Propensity Score", color="#94a3b8")
            lg = ax.legend()
            lg.get_frame().set_facecolor("#1e293b")
            for t in lg.get_texts(): t.set_color("#e2e8f0")
            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            self.txt.setText(f"❌ PSM hatası: {e}")

    def _plot_coef(self, model, title=""):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for s in ax.spines.values(): s.set_edgecolor("#1e293b")

        coefs = model.params.drop("const", errors="ignore")
        ci = model.conf_int().drop("const", errors="ignore")
        y_pos = range(len(coefs))

        ax.barh(list(y_pos), coefs.values, color="#3b82f6", alpha=0.7, height=0.5)
        ax.errorbar(coefs.values, list(y_pos),
                    xerr=[coefs.values - ci[0].values, ci[1].values - coefs.values],
                    fmt='none', color="#94a3b8", capsize=4)
        ax.axvline(0, color="#f59e0b", linewidth=1.5, linestyle="--")
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(coefs.index, color="#94a3b8", fontsize=8)
        ax.set_xlabel("Katsayı (95% CI)", color="#94a3b8", fontsize=8)
        ax.set_title(title, color="#e2e8f0", fontsize=10)
        self.fig.tight_layout()
        self.canvas.draw()
