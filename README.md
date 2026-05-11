BioStat

Biostatistics and AI-Powered Clinical Data Analysis

🚀 Setup
bash
# 1. Install required libraries
pip install -r requirements.txt

# 2. Launch the application
python main.py
📦 Project Structure
text
biostat_app/
├── main.py                  # Entry point
├── requirements.txt
├── ui/
│   ├── main_window.py       # Main window & tabs
│   ├── styles.py            # Dark theme CSS
│   ├── data_panel.py        # 📂 Data loading & cleaning
│   ├── distribution_panel.py # 📊 Distribution tests
│   ├── hypothesis_panel.py  # 🧪 Hypothesis tests
│   ├── survival_panel.py    # 📈 Survival analysis
│   ├── confounder_panel.py  # 🔗 Confounder analysis
│   └── report_panel.py      # 📝 Report generation
🧩 Modules
📂 Data Panel
CSV & Excel loading (read_csv, read_excel)

Table preview (first 200 rows)

Missing value detection (highlighted in red)

Data cleaning: dropna() or median imputation

Built‑in sample clinical dataset (n=120)

📊 Distribution Tests
Shapiro‑Wilk normality test

Kolmogorov‑Smirnov test

Histogram + KDE curve

Box plot visualization

Q‑Q plot (with R²)

Descriptive statistics (mean, median, SD, skewness, kurtosis)

🧪 Hypothesis Tests (15 tests)
Parametric	Non‑Parametric	Categorical	Regression
Independent t‑test	Mann‑Whitney U	Chi‑square	Simple Linear
Paired t‑test	Wilcoxon	Fisher Exact	Multiple Linear
One‑Sample t‑test	Kruskal‑Wallis	McNemar	Logistic
One‑Way ANOVA			
Pearson / Spearman Correlation			
📈 Survival Analysis
Kaplan‑Meier curve (with grouping)

Log‑rank test (two‑group comparison)

Cox Proportional Hazards Regression (hazard ratios)

KM curves with confidence intervals

🔗 Confounder Analysis
Crude model – unadjusted β

ANCOVA – adjusted model controlling for confounders

PSM (Propensity Score Matching) – greedy caliper matching

Coefficient forest plot (95% CI)

📝 Report Generation
Preview text

PDF report (using ReportLab): descriptive statistics, normality, correlation

CSV export

📊 Sample Data
Click the "🧪 Sample Data" button to load the built‑in clinical dataset:

Variable	Description
patient_id	Patient identifier
age	Age (30‑80)
gender	Male / Female
treatment_group	Control / Treatment_A / Treatment_B
bmi	Body mass index
blood_pressure	Blood pressure (mmHg)
cholesterol	Cholesterol (mg/dL)
glucose	Glucose (mg/dL)
smoking	0 = Non‑smoker, 1 = Smoker
survival_time	Survival time (months)
survival_event	Event: 0 = Censored, 1 = Event
outcome	Good / Moderate / Poor
💡 Quick Start
Run python main.py

In the 📂 Data tab, load the "🧪 Sample Data"

📊 Distribution → select cholesterol → run Shapiro‑Wilk

🧪 Hypothesis → ANOVA → test cholesterol vs treatment_group

📈 Survival → survival_time / survival_event / treatment_group → KM curve

🔗 Confounder → mark age, smoking as confounders → ANCOVA

📝 Report → Save PDF Report
