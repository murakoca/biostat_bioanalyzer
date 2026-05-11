"""
Rapor Üretimi Paneli — Otomatik PDF rapor + özet tablo
"""
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QCheckBox, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt
from scipy import stats


class ReportPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self._build_ui()

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        self._refresh_preview()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        hdr = QLabel("📝 Otomatik Rapor Üretimi")
        hdr.setObjectName("sectionTitle")
        layout.addWidget(hdr)

        # Options
        grp_opt = QGroupBox("Rapor Bölümleri")
        ov = QHBoxLayout(grp_opt)
        self.chk_desc  = QCheckBox("Tanımlayıcı İstatistikler")
        self.chk_norm  = QCheckBox("Normallik Testleri")
        self.chk_corr  = QCheckBox("Korelasyon Matrisi")
        self.chk_miss  = QCheckBox("Eksik Değer Analizi")
        for chk in [self.chk_desc, self.chk_norm, self.chk_corr, self.chk_miss]:
            chk.setChecked(True)
            ov.addWidget(chk)
        layout.addWidget(grp_opt)

        # Buttons
        btn_row = QHBoxLayout()
        btn_preview = QPushButton("🔍  Önizleme Oluştur")
        btn_preview.setObjectName("primaryBtn")
        btn_preview.clicked.connect(self._refresh_preview)

        btn_csv = QPushButton("💾  CSV Olarak Kaydet")
        btn_csv.clicked.connect(self._export_csv)

        btn_pdf = QPushButton("📄  PDF Rapor")
        btn_pdf.setObjectName("successBtn")
        btn_pdf.clicked.connect(self._export_pdf)

        btn_row.addWidget(btn_preview)
        btn_row.addWidget(btn_csv)
        btn_row.addWidget(btn_pdf)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumHeight(6)
        layout.addWidget(self.progress)

        # Preview area
        grp_prev = QGroupBox("Rapor Önizleme")
        pv = QVBoxLayout(grp_prev)
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setFontFamily("Courier New")
        pv.addWidget(self.txt)
        layout.addWidget(grp_prev)

    def _refresh_preview(self):
        if self.df is None:
            self.txt.setText("⚠ Önce veri yükleyin.")
            return
        report = self._generate_report_text()
        self.txt.setText(report)

    def _generate_report_text(self) -> str:
        df = self.df
        lines = []
        lines.append("=" * 60)
        lines.append("  BİYOİSTATİSTİK KLİNİK VERİ ANALİZ RAPORU")
        lines.append("  BiyoStat Pro v1.0")
        lines.append("=" * 60)
        lines.append(f"\nVeri Boyutu: {df.shape[0]} satır × {df.shape[1]} sütun")
        lines.append(f"Sayısal Değişken: {len(df.select_dtypes(include=np.number).columns)}")
        lines.append(f"Kategorik Değişken: {len(df.select_dtypes(exclude=np.number).columns)}")

        if self.chk_miss.isChecked():
            lines.append("\n── EKSİK DEĞER ANALİZİ ──")
            missing = df.isnull().sum()
            missing = missing[missing > 0]
            if len(missing) == 0:
                lines.append("Eksik değer yok.")
            else:
                for col, cnt in missing.items():
                    pct = 100 * cnt / len(df)
                    lines.append(f"  {col}: {cnt} ({pct:.1f}%)")

        if self.chk_desc.isChecked():
            lines.append("\n── TANIMLAYICI İSTATİSTİKLER ──")
            num_df = df.select_dtypes(include=np.number)
            for col in num_df.columns:
                data = num_df[col].dropna()
                lines.append(
                    f"  {col}:\n"
                    f"    n={len(data)}  μ={data.mean():.3f}  Medyan={data.median():.3f}"
                    f"  SD={data.std():.3f}  Min={data.min():.3f}  Max={data.max():.3f}"
                )

            cat_df = df.select_dtypes(exclude=np.number)
            for col in cat_df.columns:
                lines.append(f"\n  {col} (kategorik):")
                for val, cnt in df[col].value_counts().items():
                    pct = 100 * cnt / len(df)
                    lines.append(f"    {val}: {cnt} ({pct:.1f}%)")

        if self.chk_norm.isChecked():
            lines.append("\n── NORMALLİK TESTLERİ (Shapiro-Wilk) ──")
            for col in df.select_dtypes(include=np.number).columns:
                data = df[col].dropna().values
                if len(data) < 3:
                    continue
                sample = data[:5000]
                w, p = stats.shapiro(sample)
                verdict = "Normal ✅" if p > 0.05 else "Normal değil ❌"
                lines.append(f"  {col}: W={w:.4f}  p={p:.4f}  → {verdict}")

        if self.chk_corr.isChecked():
            lines.append("\n── KORELASYON MATRİSİ ──")
            num_cols = df.select_dtypes(include=np.number).columns[:8]  # first 8
            corr = df[num_cols].corr().round(3)
            lines.append(corr.to_string())

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def _export_csv(self):
        if self.df is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "CSV Olarak Kaydet", "rapor.csv", "CSV (*.csv)")
        if path:
            try:
                self.df.describe().to_csv(path)
                self.txt.append(f"\n✅ CSV kaydedildi: {path}")
            except Exception as e:
                self.txt.append(f"\n❌ {e}")

    def _export_pdf(self):
        if self.df is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "PDF Kaydet", "biostat_rapor.pdf", "PDF (*.pdf)")
        if not path:
            return

        self.progress.setVisible(True)
        self.progress.setValue(20)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.enums import TA_CENTER

            doc = SimpleDocTemplate(path, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle("title", parent=styles["Title"],
                fontSize=16, textColor=colors.HexColor("#1e3a5f"),
                spaceAfter=6, alignment=TA_CENTER)
            h1 = ParagraphStyle("h1", parent=styles["Heading1"],
                fontSize=12, textColor=colors.HexColor("#2563eb"), spaceAfter=4)
            body = ParagraphStyle("body", parent=styles["Normal"],
                fontSize=9, leading=14, textColor=colors.HexColor("#1f2937"))
            mono = ParagraphStyle("mono", parent=styles["Code"],
                fontSize=8, leading=12)

            story.append(Paragraph("BiyoStat Pro — Klinik Veri Analiz Raporu", title_style))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3b82f6")))
            story.append(Spacer(1, 0.4*cm))

            df = self.df
            story.append(Paragraph(f"Veri: {df.shape[0]} satır × {df.shape[1]} sütun", body))
            story.append(Spacer(1, 0.3*cm))

            self.progress.setValue(40)

            # Descriptive table
            story.append(Paragraph("Tanımlayıcı İstatistikler", h1))
            num_df = df.select_dtypes(include=np.number)
            desc = num_df.describe().round(3)
            table_data = [[""] + list(desc.columns)]
            for idx in desc.index:
                row = [idx] + [str(v) for v in desc.loc[idx]]
                table_data.append(row)

            t = Table(table_data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.4*cm))

            self.progress.setValue(70)

            # Normality section
            story.append(Paragraph("Normallik Testleri (Shapiro-Wilk)", h1))
            for col in num_df.columns:
                data = df[col].dropna().values[:5000]
                if len(data) < 3:
                    continue
                w, p = stats.shapiro(data)
                verdict = "Normal ✅" if p > 0.05 else "Normal DEĞİL ❌"
                story.append(Paragraph(
                    f"<b>{col}</b>: W={w:.4f}  p={p:.4f}  → {verdict}", body
                ))

            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph("Rapor BiyoStat Pro v1.0 tarafından oluşturulmuştur.", body))

            self.progress.setValue(90)
            doc.build(story)
            self.progress.setValue(100)
            self.txt.append(f"\n✅ PDF kaydedildi: {path}")

        except Exception as e:
            self.txt.append(f"\n❌ PDF hatası: {e}")
        finally:
            self.progress.setVisible(False)
