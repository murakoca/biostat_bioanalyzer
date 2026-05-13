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
        
        # Sonuç değişkeni için: sayısal sütunlar
        self.combo_outcome.clear()
        self.combo_outcome.addItems(num_cols)
        
        # Maruz kalma değişkeni için: ID ve gereksiz sütunları filtrele
        exposure_cols = []
        for col in all_cols:
            # ID, hasta_no, patient_id gibi sütunları filtrele
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['id', 'hasta_id', 'patient_id', 'kayit_no', 'no']):
                continue
            # Tarih sütunlarını filtrele
            if any(keyword in col_lower for keyword in ['tarih', 'date', 'zaman']):
                continue
            # Tek değerli sütunları filtrele
            if df[col].nunique() <= 1:
                continue
            exposure_cols.append(col)
        
        self.combo_exposure.clear()
        if exposure_cols:
            self.combo_exposure.addItems(exposure_cols)
        else:
            self.combo_exposure.addItem("⚠ Uygun değişken yok")
            self.combo_exposure.setEnabled(False)
            self.txt.setText("⚠ Uyarı: Maruz kalma (exposure) için uygun değişken bulunamadı.\n\n"
                           "Uygun değişkenler:\n"
                           "• Tedavi grubu (Kontrol/Tedavi_A/Tedavi_B)\n"
                           "• Sigara (0/1)\n"
                           "• Cinsiyet (Erkek/Kadın)\n"
                           "• Yaş, BMI gibi sürekli değişkenler\n\n"
                           "ID, hasta_no gibi benzersiz tanımlayıcılar kullanılamaz.")

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
        self.combo_outcome = QComboBox()
        self.combo_outcome.setMinimumWidth(140)
        self.combo_outcome.setToolTip("Bağımlı değişken - sayısal olmalıdır (örn: kan_basinci, kolesterol)")
        ctrl.addWidget(self.combo_outcome)

        ctrl.addWidget(QLabel("Maruz Kalma (X):"))
        self.combo_exposure = QComboBox()
        self.combo_exposure.setMinimumWidth(140)
        self.combo_exposure.setToolTip("Bağımsız değişken - tedavi grubu, sigara, cinsiyet gibi değişkenler (ID olamaz)")
        ctrl.addWidget(self.combo_exposure)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: confounder list + buttons
        left = QWidget()
        left.setMaximumWidth(280)
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
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
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

    def _show_error(self, msg):
        """Kullanıcı dostu hata mesajı göster"""
        self.txt.setText(f"❌ {msg}\n\n"
                        f"Çözüm önerileri:\n"
                        f"• Sonuç değişkeni sayısal olmalıdır (örn: kan_basinci, kolesterol)\n"
                        f"• Maruz kalma değişkeni ID veya hasta_no OLMAMALIDIR\n"
                        f"• Maruz kalma değişkeni: tedavi grubu, sigara, cinsiyet gibi anlamlı değişkenler olmalı\n"
                        f"• Eksik veriler için önce Veri sekmesinden temizleme yapın")

    def _get_series(self, data, col):
        """Güvenli Series çekme - DataFrame ise ilk sütunu al"""
        if col not in data.columns:
            return None
        series = data[col]
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        return series

    def _run_crude(self):
        if self.df is None:
            self._show_error("Önce veri yükleyin.")
            return
            
        y = self.combo_outcome.currentText()
        x = self.combo_exposure.currentText()
        
        if not y or not x:
            self._show_error("Lütfen sonuç ve maruz kalma değişkenlerini seçin.")
            return
        
        # Maruz kalma değişkeninin ID olup olmadığını kontrol et
        x_lower = x.lower()
        if any(keyword in x_lower for keyword in ['id', 'hasta_id', 'patient_id', 'kayit_no']):
            self._show_error(f"'{x}' bir kimlik/tanımlayıcı sütunudur. Maruz kalma değişkeni olarak kullanılamaz.\n\n"
                           f"Lütfen şunları deneyin:\n"
                           f"• Tedavi grubu (Kontrol/Tedavi_A/Tedavi_B)\n"
                           f"• Sigara (0/1)\n"
                           f"• Cinsiyet (Erkek/Kadın)\n"
                           f"• Yaş, BMI gibi sürekli değişkenler")
            return
            
        try:
            df = self.df[[y, x]].dropna()
            
            if len(df) == 0:
                self._show_error("Seçilen sütunlarda geçerli veri yok.")
                return
            
            # Kategorik değişkenleri kodla
            x_series = self._get_series(df, x)
            if x_series is None:
                self._show_error(f"'{x}' sütunu bulunamadı.")
                return
                
            if x_series.dtype == object or x_series.dtype.name == 'category':
                # Kategorik ise dummy değişkenlere çevir
                df = pd.get_dummies(df, columns=[x], drop_first=True)
                x_cols = [c for c in df.columns if c != y]
                for col in x_cols:
                    df[col] = df[col].astype(float)
            else:
                x_cols = [x]
                if not pd.api.types.is_numeric_dtype(df[x]):
                    self._show_error(f"'{x}' sütunu sayısal bir değere dönüştürülemedi.\n\n"
                                   f"Lütfen sayısal veya kategorik bir değişken seçin.")
                    return

            # Bağımlı değişken sayısal mı kontrol et
            if not pd.api.types.is_numeric_dtype(df[y]):
                self._show_error(f"Sonuç değişkeni '{y}' sayısal olmalıdır.\n\n"
                               f"Lütfen kan_basinci, kolesterol, glukoz gibi sayısal bir sütun seçin.")
                return

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
            self._show_error(f"Ham model hatası: {str(e)}")

    def _run_ancova(self):
        if self.df is None:
            self._show_error("Önce veri yükleyin.")
            return
            
        y = self.combo_outcome.currentText()
        x = self.combo_exposure.currentText()
        confounders = self._get_confounders()

        if not y or not x:
            self._show_error("Lütfen sonuç ve maruz kalma değişkenlerini seçin.")
            return
        
        # Maruz kalma değişkeninin ID olup olmadığını kontrol et
        x_lower = x.lower()
        if any(keyword in x_lower for keyword in ['id', 'hasta_id', 'patient_id', 'kayit_no']):
            self._show_error(f"'{x}' bir kimlik/tanımlayıcı sütunudur. Maruz kalma değişkeni olarak kullanılamaz.")
            return

        try:
            cols = list(set([y, x] + confounders))
            df = self.df[cols].dropna()

            if len(df) == 0:
                self._show_error("Seçilen sütunlarda geçerli veri yok.")
                return

            # Bağımlı değişken sayısal mı kontrol et
            if not pd.api.types.is_numeric_dtype(df[y]):
                self._show_error(f"Sonuç değişkeni '{y}' sayısal olmalıdır.")
                return

            # Bağımsız değişkenleri hazırla
            X_cols = []
            
            # Maruz kalma değişkenini ekle
            x_series = self._get_series(df, x)
            if x_series is not None and (x_series.dtype == object or x_series.dtype.name == 'category'):
                dummies = pd.get_dummies(df[x], prefix=x, drop_first=True).astype(float)
                df = pd.concat([df.drop(x, axis=1), dummies], axis=1)
                X_cols.extend(dummies.columns)
            elif x in df.columns:
                X_cols.append(x)
            
            # Confounder'ları ekle
            for conf in confounders:
                if conf in df.columns:
                    conf_series = self._get_series(df, conf)
                    if conf_series is not None and (conf_series.dtype == object or conf_series.dtype.name == 'category'):
                        dummies = pd.get_dummies(df[conf], prefix=conf, drop_first=True).astype(float)
                        df = pd.concat([df.drop(conf, axis=1), dummies], axis=1)
                        X_cols.extend(dummies.columns)
                    elif conf in df.columns:
                        X_cols.append(conf)

            # Tüm X değişkenlerinin df'de olduğundan emin ol
            available_X = [c for c in X_cols if c in df.columns]
            
            if len(available_X) == 0:
                self._show_error("Hiç bağımsız değişken kalmadı. Lütfen farklı değişkenler seçin.")
                return
            
            X = sm.add_constant(df[available_X])
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
            self._show_error(f"ANCOVA hatası: {str(e)}")

    def _run_psm(self):
        """Propensity Score Matching (basit logistic-based)"""
        if self.df is None:
            self._show_error("Önce veri yükleyin.")
            return
            
        x = self.combo_exposure.currentText()
        confounders = self._get_confounders()

        if not x:
            self._show_error("Lütfen maruz kalma değişkenini seçin.")
            return
        
        # Maruz kalma değişkeninin ID olup olmadığını kontrol et
        x_lower = x.lower()
        if any(keyword in x_lower for keyword in ['id', 'hasta_id', 'patient_id', 'kayit_no']):
            self._show_error(f"'{x}' bir kimlik/tanımlayıcı sütunudur. PSM için kullanılamaz.\n\n"
                           f"PSM için ikili (binary) bir değişken seçin:\n"
                           f"• Tedavi grubu (Kontrol/Tedavi_A)\n"
                           f"• Sigara (0/1)\n"
                           f"• Cinsiyet (Erkek/Kadın)")
            return

        if not confounders:
            self.txt.setText("⚠ PSM için en az 1 confounder seçmelisiniz.\n\n"
                           "Lütfen soldaki listeden confounder değişkenleri seçin (işaretleyin).\n\n"
                           "Confounder'lar: Maruz kalma ve sonuçla ilişkili karıştırıcı faktörlerdir.\n"
                           "Örnek: yaş, cinsiyet, BMI gibi değişkenler.")
            return

        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler

            # Veriyi hazırla
            cols = [x] + confounders
            df = self.df[cols].copy()
            df = df.dropna()
            
            if len(df) == 0:
                self.txt.setText("❌ Seçilen sütunlarda geçerli veri yok.\n\n"
                               "Lütfen eksik değerleri temizleyin veya farklı sütunlar seçin.")
                return

            # Maruz kalma değişkenini binary'e dönüştür
            exposure_series = self._get_series(df, x)
            
            if exposure_series is None:
                self._show_error(f"'{x}' sütunu bulunamadı.")
                return
            
            # Kategorik ise binary'e çevir
            if exposure_series.dtype == object or exposure_series.dtype.name == 'category':
                unique_vals = exposure_series.dropna().unique()
                if len(unique_vals) != 2:
                    self.txt.setText(f"⚠ PSM için maruz kalma değişkeni ikili (binary) olmalıdır.\n\n"
                                   f"'{x}' sütunu {len(unique_vals)} farklı değer içeriyor: {unique_vals.tolist()}\n\n"
                                   f"Öneri: İki gruplu bir değişken seçin (örn: tedavi_grubu için sadece 2 grup seçin)")
                    return
                exposure_binary = pd.Categorical(exposure_series).codes
            else:
                exposure_binary = exposure_series.values
            
            # Binary kontrol
            unique_vals = np.unique(exposure_binary[~np.isnan(exposure_binary)])
            if not set(unique_vals).issubset({0, 1}):
                self.txt.setText(f"⚠ PSM için maruz kalma değişkeni yalnızca 0 ve 1 değerlerini içermelidir.\n\n"
                               f"'{x}' sütununda bulunan değerler: {unique_vals.tolist()}")
                return
            
            y_ps = exposure_binary.astype(int)
            
            # Confounder'ları sayısallaştır
            X_ps_list = []
            valid_confounders = []
            
            for conf in confounders:
                if conf not in df.columns:
                    continue
                    
                conf_series = self._get_series(df, conf)
                if conf_series is None:
                    continue
                
                if conf_series.dtype == object or conf_series.dtype.name == 'category':
                    conf_numeric = pd.Categorical(conf_series).codes
                    if np.all(conf_numeric == -1):
                        continue
                    X_ps_list.append(conf_numeric)
                    valid_confounders.append(conf)
                elif pd.api.types.is_numeric_dtype(conf_series):
                    X_ps_list.append(conf_series.values)
                    valid_confounders.append(conf)
            
            if len(X_ps_list) == 0:
                self.txt.setText(f"⚠ Seçilen confounder'lar sayısal değere dönüştürülemedi.\n\n"
                               f"Lütfen sayısal veya kategorik confounder değişkenler seçin.\n"
                               f"Örnek: yaş, cinsiyet, bmi, kolesterol gibi değişkenler.")
                return
            
            # X_ps matrisini oluştur
            X_ps = np.column_stack(X_ps_list)
            
            # NaN kontrolü
            if np.any(np.isnan(X_ps)):
                nan_rows = np.any(np.isnan(X_ps), axis=1)
                X_ps = X_ps[~nan_rows]
                y_ps = y_ps[~nan_rows]
                df = df.iloc[~nan_rows].reset_index(drop=True)
                
                if len(X_ps) == 0:
                    self.txt.setText("❌ Confounder'ların hepsi eksik değer içeriyor.")
                    return
            
            # Ölçeklendir
            scaler = StandardScaler()
            X_ps_scaled = scaler.fit_transform(X_ps)
            
            # Lojistik regresyon
            lr = LogisticRegression(max_iter=1000)
            lr.fit(X_ps_scaled, y_ps)
            ps = lr.predict_proba(X_ps_scaled)[:, 1]
            
            df = df.reset_index(drop=True)
            df["propensity_score"] = ps
            df["treatment"] = y_ps
            
            # Grupları ayır
            treated = df[df["treatment"] == 1].copy()
            control = df[df["treatment"] == 0].copy()
            
            if len(treated) == 0:
                self.txt.setText(f"⚠ Tedavi grubu (değer=1) bulunamadı.\n\n"
                               f"Mevcut değerler: {np.unique(y_ps).tolist()}")
                return
                
            if len(control) == 0:
                self.txt.setText(f"⚠ Kontrol grubu (değer=0) bulunamadı.\n\n"
                               f"Mevcut değerler: {np.unique(y_ps).tolist()}")
                return
            
            # Caliper matching
            matched_control = []
            caliper = 0.05
            control_temp = control.copy()
            
            for idx, row in treated.iterrows():
                ps_t = row["propensity_score"]
                if len(control_temp) > 0:
                    diffs = np.abs(control_temp["propensity_score"].values - ps_t)
                    min_idx = np.argmin(diffs)
                    if diffs[min_idx] <= caliper:
                        matched_control.append(control_temp.index[min_idx])
                        control_temp = control_temp.drop(control_temp.index[min_idx])
            
            # Sonuçları hazırla
            out = "── Propensity Score Matching ──\n\n"
            out += f"Toplam gözlem: {len(df)}\n"
            out += f"Tedavi grubu (1): {len(treated)}\n"
            out += f"Kontrol grubu (0): {len(control)}\n"
            out += f"Eşleştirilen kontrol: {len(matched_control)}\n"
            out += f"Caliper: {caliper}\n\n"
            out += "PS Özeti:\n"
            out += f"Tedavi PS: {treated['propensity_score'].mean():.4f} ± {treated['propensity_score'].std():.4f}\n"
            out += f"Kontrol PS: {control['propensity_score'].mean():.4f} ± {control['propensity_score'].std():.4f}\n"
            
            if len(matched_control) > 0:
                out += f"\n✅ {len(matched_control)} kontrol başarıyla eşleştirildi."
            else:
                out += f"\n⚠ Hiç kontrol eşleştirilemedi. Caliper değerini artırmayı deneyin."
            
            self.txt.setText(out)
            
            # Plot
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            self.fig.patch.set_facecolor("#0f1117")
            ax.set_facecolor("#111827")
            ax.tick_params(colors="#94a3b8", labelsize=8)
            for s in ax.spines.values(): 
                s.set_edgecolor("#1e293b")
            
            ax.hist(treated["propensity_score"], bins=20, alpha=0.6, color="#3b82f6", label=f"Tedavi (n={len(treated)})")
            ax.hist(control["propensity_score"], bins=20, alpha=0.6, color="#f59e0b", label=f"Kontrol (n={len(control)})")
            ax.set_title("Propensity Score Dağılımı", color="#e2e8f0")
            ax.set_xlabel("Propensity Score", color="#94a3b8")
            ax.set_ylabel("Frekans", color="#94a3b8")
            lg = ax.legend()
            if lg:
                lg.get_frame().set_facecolor("#1e293b")
                for t in lg.get_texts(): 
                    t.set_color("#e2e8f0")
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.txt.setText(f"❌ PSM hatası: {str(e)}\n\n"
                           f"Olası çözümler:\n"
                           f"• Farklı confounder'lar seçmeyi deneyin\n"
                           f"• Maruz kalma değişkeninin binary (0/1) olduğundan emin olun\n"
                           f"• Maruz kalma değişkeni ID veya hasta_no OLMAMALIDIR\n"
                           f"• Veri temizleme yapın (eksik değerleri giderin)")

    def _plot_coef(self, model, title=""):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor("#0f1117")
        ax.set_facecolor("#111827")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for s in ax.spines.values(): 
            s.set_edgecolor("#1e293b")

        coefs = model.params.drop("const", errors="ignore")
        if len(coefs) == 0:
            ax.text(0.5, 0.5, "Katsayı gösterilemiyor", 
                   transform=ax.transAxes, ha='center', va='center',
                   color="#94a3b8")
            self.canvas.draw()
            return
            
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