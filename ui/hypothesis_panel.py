"""
Hipotez Testleri Paneli — t-test, ANOVA, Ki-kare, Mann-Whitney, Pearson/Spearman, Regresyon
"""
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QSplitter, QTextEdit, QStackedWidget
)
from PyQt6.QtCore import Qt
from scipy import stats
import statsmodels.api as sm
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


TESTS = [
    "Bağımsız t-testi",
    "Eşleştirilmiş t-testi",
    "Tek Örneklem t-testi",
    "Mann-Whitney U",
    "Wilcoxon",
    "Kruskal-Wallis",
    "Tek Yönlü ANOVA",
    "Ki-kare",
    "Fisher Exact",
    "McNemar",
    "Pearson Korelasyon",
    "Spearman Korelasyon",
    "Basit Lineer Regresyon",
    "Çoklu Lineer Regresyon",
    "Lojistik Regresyon",
]


class HypothesisPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self._build_ui()

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()

        for combo in [self.combo_col1, self.combo_col2, self.combo_group]:
            combo.clear()

        self.combo_col1.addItems(num_cols)
        self.combo_col2.addItems(num_cols)
        self.combo_group.addItems(cols)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("🧪 Hipotez Testleri")
        hdr.setObjectName("sectionTitle")
        layout.addWidget(hdr)

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Test:"))
        self.combo_test = QComboBox()
        self.combo_test.setMinimumWidth(220)
        self.combo_test.addItems(TESTS)
        ctrl.addWidget(self.combo_test)

        ctrl.addWidget(QLabel("Değişken 1:"))
        self.combo_col1 = QComboBox()
        self.combo_col1.setMinimumWidth(150)
        ctrl.addWidget(self.combo_col1)

        ctrl.addWidget(QLabel("Değişken 2 / Grup:"))
        self.combo_col2 = QComboBox()
        self.combo_col2.setMinimumWidth(150)
        ctrl.addWidget(self.combo_col2)

        ctrl.addWidget(QLabel("Grup Sütunu:"))
        self.combo_group = QComboBox()
        self.combo_group.setMinimumWidth(150)
        ctrl.addWidget(self.combo_group)

        btn_run = QPushButton("▶  Testi Uygula")
        btn_run.setObjectName("primaryBtn")
        btn_run.clicked.connect(self._run)
        ctrl.addWidget(btn_run)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        grp = QGroupBox("Sonuçlar & Yorum")
        gv = QVBoxLayout(grp)
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setMinimumWidth(360)
        gv.addWidget(self.txt)
        splitter.addWidget(grp)

        self.fig = Figure(figsize=(8, 5), facecolor="#0f1117")
        self.canvas = FigureCanvas(self.fig)
        splitter.addWidget(self.canvas)
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)

    def _run(self):
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return
        test = self.combo_test.currentText()
        col1 = self.combo_col1.currentText()
        col2 = self.combo_col2.currentText()
        grp  = self.combo_group.currentText()

        df = self.df
        out = f"Test: {test}\n{'─'*40}\n"

        try:
            if test == "Bağımsız t-testi":
                out += self._t_indep(df, col1, grp)
            elif test == "Eşleştirilmiş t-testi":
                out += self._t_paired(df, col1, col2)
            elif test == "Tek Örneklem t-testi":
                out += self._t_one(df, col1)
            elif test == "Mann-Whitney U":
                out += self._mann_whitney(df, col1, grp)
            elif test == "Wilcoxon":
                out += self._wilcoxon(df, col1, col2)
            elif test == "Kruskal-Wallis":
                out += self._kruskal(df, col1, grp)
            elif test == "Tek Yönlü ANOVA":
                out += self._anova(df, col1, grp)
            elif test == "Ki-kare":
                out += self._chi2(df, col1, grp)
            elif test == "Pearson Korelasyon":
                out += self._pearson(df, col1, col2)
            elif test == "Spearman Korelasyon":
                out += self._spearman(df, col1, col2)
            elif test == "Basit Lineer Regresyon":
                out += self._simple_reg(df, col1, col2)
            elif test == "Çoklu Lineer Regresyon":
                out += self._multi_reg(df, col2, df.select_dtypes(include=np.number).columns.tolist())
            elif test == "Lojistik Regresyon":
                out += self._logistic_reg(df, col1, col2)
            else:
                out += "Bu test yakında eklenecek."
        except Exception as e:
            out += f"\n❌ Hata: {e}"

        self.txt.setText(out)

    # ── Test implementations ────────────────────────────────────────────

    def _t_indep(self, df, col, grp_col):
        groups = [g[col].dropna().values for _, g in df.groupby(grp_col)]
        if len(groups) < 2:
            return "❌ En az 2 grup gerekli."
        g1, g2 = groups[0], groups[1]
        t, p = stats.ttest_ind(g1, g2)
        self._plot_boxplot(df, col, grp_col)
        return self._format_result("t", t, p, n=len(df),
            extra=f"Grup 1: n={len(g1)}, μ={g1.mean():.3f}\nGrup 2: n={len(g2)}, μ={g2.mean():.3f}")

    def _t_paired(self, df, col1, col2):
        d = df[[col1, col2]].dropna()
        t, p = stats.ttest_rel(d[col1], d[col2])
        self._plot_paired(d[col1].values, d[col2].values, col1, col2)
        return self._format_result("t", t, p, n=len(d))

    def _t_one(self, df, col):
        data = df[col].dropna()
        t, p = stats.ttest_1samp(data, popmean=data.mean())
        return self._format_result("t", t, p, n=len(data),
            extra=f"μ = {data.mean():.3f}  (μ₀ = {data.mean():.3f})")

    def _mann_whitney(self, df, col, grp_col):
        groups = [g[col].dropna().values for _, g in df.groupby(grp_col)]
        if len(groups) < 2:
            return "❌ En az 2 grup gerekli."
        u, p = stats.mannwhitneyu(groups[0], groups[1], alternative='two-sided')
        self._plot_boxplot(df, col, grp_col)
        return self._format_result("U", u, p, n=len(df))

    def _wilcoxon(self, df, col1, col2):
        d = df[[col1, col2]].dropna()
        w, p = stats.wilcoxon(d[col1], d[col2])
        return self._format_result("W", w, p, n=len(d))

    def _kruskal(self, df, col, grp_col):
        groups = [g[col].dropna().values for _, g in df.groupby(grp_col)]
        h, p = stats.kruskal(*groups)
        self._plot_boxplot(df, col, grp_col)
        return self._format_result("H", h, p, n=len(df),
            extra=f"Grup sayısı: {len(groups)}")

    def _anova(self, df, col, grp_col):
        groups = [g[col].dropna().values for _, g in df.groupby(grp_col)]
        f, p = stats.f_oneway(*groups)
        self._plot_boxplot(df, col, grp_col)
        return self._format_result("F", f, p, n=len(df),
            extra=f"Grup sayısı: {len(groups)}")

    def _chi2(self, df, col1, col2):
        ct = pd.crosstab(df[col1], df[col2])
        chi2, p, dof, expected = stats.chi2_contingency(ct)
        self._plot_heatmap(ct)
        return (f"Ki-kare = {chi2:.4f}\np = {p:.4f}\ndf = {dof}\n"
                f"{'✅ İstatistiksel olarak anlamlı (p<0.05)' if p<0.05 else '❌ İstatistiksel olarak anlamsız (p≥0.05)'}")

    def _pearson(self, df, col1, col2):
        d = df[[col1, col2]].dropna()
        r, p = stats.pearsonr(d[col1], d[col2])
        self._plot_scatter(d[col1].values, d[col2].values, col1, col2, r)
        return self._format_result("r", r, p, n=len(d),
            extra=f"r² = {r**2:.4f}  ({self._corr_strength(r)})")

    def _spearman(self, df, col1, col2):
        d = df[[col1, col2]].dropna()
        rho, p = stats.spearmanr(d[col1], d[col2])
        self._plot_scatter(d[col1].values, d[col2].values, col1, col2, rho)
        return self._format_result("ρ", rho, p, n=len(d),
            extra=self._corr_strength(rho))

    def _simple_reg(self, df, y_col, x_col):
        d = df[[y_col, x_col]].dropna()
        X = sm.add_constant(d[x_col])
        model = sm.OLS(d[y_col], X).fit()
        self._plot_regression(d[x_col].values, d[y_col].values, x_col, y_col, model)
        return (f"R² = {model.rsquared:.4f}\n"
                f"Adjusted R² = {model.rsquared_adj:.4f}\n"
                f"F = {model.fvalue:.4f}  p = {model.f_pvalue:.4f}\n\n"
                f"Katsayılar:\n{model.summary2().tables[1].to_string()}")

    def _multi_reg(self, df, y_col, x_cols):
        x_cols = [c for c in x_cols if c != y_col]
        d = df[[y_col] + x_cols].dropna()
        X = sm.add_constant(d[x_cols])
        model = sm.OLS(d[y_col], X).fit()
        return (f"R² = {model.rsquared:.4f}\n"
                f"Adjusted R² = {model.rsquared_adj:.4f}\n"
                f"F = {model.fvalue:.4f}  p = {model.f_pvalue:.4f}\n\n"
                + model.summary2().tables[1].to_string())

    def _logistic_reg(self, df, y_col, x_col):
        d = df[[y_col, x_col]].dropna()
        try:
            X = sm.add_constant(d[x_col])
            model = sm.Logit(d[y_col], X).fit(disp=False)
            return (f"Log-Likelihood: {model.llf:.4f}\n"
                    f"AIC: {model.aic:.4f}\n"
                    f"Pseudo R²: {model.prsquared:.4f}\n\n"
                    + model.summary2().tables[1].to_string())
        except Exception as e:
            return f"Lojistik regresyon hatası: {e}"

    # ── Helpers ────────────────────────────────────────────────────────

    def _format_result(self, stat_name, stat_val, p_val, n=None, extra=""):
        sig = p_val < 0.05
        res = (
            f"{stat_name} istatistiği = {stat_val:.4f}\n"
            f"p-değeri = {p_val:.4f}\n"
        )
        if n:
            res += f"n = {n}\n"
        if extra:
            res += f"\n{extra}\n"
        res += f"\n{'✅ İstatistiksel olarak ANLAMLI (p < 0.05)' if sig else '❌ İstatistiksel olarak ANLAMSIZ (p ≥ 0.05)'}\n"
        res += f"\nYorum: {'H₀ reddedilir.' if sig else 'H₀ reddedilemez.'}"
        return res

    def _corr_strength(self, r):
        r = abs(r)
        if r >= 0.7: return "Güçlü korelasyon"
        if r >= 0.4: return "Orta korelasyon"
        return "Zayıf korelasyon"

    # ── Plot helpers ────────────────────────────────────────────────────

    def _setup_ax(self, ax):
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for s in ax.spines.values():
            s.set_edgecolor("#1e293b")

    def _plot_boxplot(self, df, col, grp_col):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        self._setup_ax(ax)
        groups = df.groupby(grp_col)[col].apply(lambda x: x.dropna().tolist())
        colors = ["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6"]
        bp = ax.boxplot(groups, patch_artist=True, labels=groups.index)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        for elem in ['whiskers','caps','medians']:
            for line in bp[elem]:
                line.set_color("#94a3b8")
        ax.set_title(f"{col} by {grp_col}", color="#e2e8f0", fontsize=10)
        ax.set_xlabel(grp_col, color="#94a3b8", fontsize=8)
        ax.set_ylabel(col, color="#94a3b8", fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_paired(self, a, b, n1, n2):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        self._setup_ax(ax)
        for x1, x2 in zip(a[:60], b[:60]):
            color = "#22c55e" if x2 > x1 else "#ef4444"
            ax.plot([0, 1], [x1, x2], color=color, alpha=0.4, linewidth=1)
        ax.scatter([0]*len(a), a, color="#3b82f6", s=20, zorder=5)
        ax.scatter([1]*len(b), b, color="#f59e0b", s=20, zorder=5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([n1, n2], color="#94a3b8")
        ax.set_title("Eşleştirilmiş Değerler", color="#e2e8f0")
        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_scatter(self, x, y, xn, yn, r):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        self._setup_ax(ax)
        ax.scatter(x, y, color="#3b82f6", alpha=0.6, s=18)
        m, b = np.polyfit(x, y, 1)
        ax.plot(np.sort(x), m * np.sort(x) + b, color="#f59e0b", linewidth=2)
        ax.set_xlabel(xn, color="#94a3b8", fontsize=8)
        ax.set_ylabel(yn, color="#94a3b8", fontsize=8)
        ax.set_title(f"Scatter — r = {r:.3f}", color="#e2e8f0")
        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_heatmap(self, ct):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        self._setup_ax(ax)
        import matplotlib.colors as mcolors
        im = ax.imshow(ct.values, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(ct.columns)))
        ax.set_yticks(range(len(ct.index)))
        ax.set_xticklabels(ct.columns, color="#94a3b8", fontsize=8)
        ax.set_yticklabels(ct.index, color="#94a3b8", fontsize=8)
        for i in range(ct.shape[0]):
            for j in range(ct.shape[1]):
                ax.text(j, i, ct.values[i, j], ha='center', va='center', color='white', fontsize=9)
        ax.set_title("Çapraz Tablo (Isı Haritası)", color="#e2e8f0")
        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_regression(self, x, y, xn, yn, model):
        self.fig.clear()
        axes = self.fig.subplots(1, 2)
        self.fig.patch.set_facecolor("#0f1117")
        for ax in axes:
            self._setup_ax(ax)

        # Scatter + fit
        ax1 = axes[0]
        ax1.scatter(x, y, color="#3b82f6", s=15, alpha=0.6)
        xs = np.linspace(x.min(), x.max(), 100)
        ax1.plot(xs, model.params[0] + model.params[1]*xs, color="#f59e0b", linewidth=2)
        ax1.set_xlabel(xn, color="#94a3b8", fontsize=8)
        ax1.set_ylabel(yn, color="#94a3b8", fontsize=8)
        ax1.set_title(f"R² = {model.rsquared:.3f}", color="#e2e8f0")

        # Residuals
        ax2 = axes[1]
        resid = model.resid
        ax2.scatter(model.fittedvalues, resid, color="#8b5cf6", s=12, alpha=0.6)
        ax2.axhline(0, color="#f59e0b", linewidth=1.5)
        ax2.set_xlabel("Fitted", color="#94a3b8", fontsize=8)
        ax2.set_ylabel("Residuals", color="#94a3b8", fontsize=8)
        ax2.set_title("Artıklar", color="#e2e8f0")

        self.fig.tight_layout()
        self.canvas.draw()
