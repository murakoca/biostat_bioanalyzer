"""
BiyoStat Pro — Karanlık Tema Stil Dosyası
"""

DARK_STYLE = """
/* ── Global ─────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}

/* ── Menu Bar ───────────────────────────────── */
QMenuBar {
    background-color: #0d1117;
    color: #94a3b8;
    border-bottom: 1px solid #1e293b;
    padding: 2px 8px;
}
QMenuBar::item:selected { background-color: #1e293b; color: #e2e8f0; border-radius: 4px; }
QMenu { background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; }
QMenu::item { padding: 6px 20px; }
QMenu::item:selected { background-color: #3b82f6; color: white; }

/* ── Header ─────────────────────────────────── */
#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0d1f3c, stop:0.5 #0f2a52, stop:1 #0d1f3c);
    border-bottom: 2px solid #3b82f6;
}
#appTitle {
    font-size: 20px;
    font-weight: 700;
    color: #60a5fa;
    letter-spacing: 0.5px;
}
#appSubtitle {
    font-size: 11px;
    color: #64748b;
    padding-top: 2px;
}
#dataBadge {
    background-color: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Tab Widget ─────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #0f1117;
}
QTabBar {
    background-color: #0d1117;
}
QTabBar::tab {
    background-color: #0d1117;
    color: #64748b;
    padding: 10px 20px;
    border: none;
    border-bottom: 3px solid transparent;
    font-size: 12px;
    font-weight: 500;
    min-width: 120px;
}
QTabBar::tab:selected {
    color: #60a5fa;
    border-bottom: 3px solid #3b82f6;
    background-color: #0f1117;
}
QTabBar::tab:hover:!selected {
    color: #94a3b8;
    background-color: #111827;
}

/* ── Buttons ────────────────────────────────── */
QPushButton {
    background-color: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #2563eb;
    color: white;
}
QPushButton:pressed { background-color: #1d4ed8; }
QPushButton:disabled { background-color: #1a1f2e; color: #374151; border-color: #1f2937; }

QPushButton#primaryBtn {
    background-color: #2563eb;
    color: white;
    border-color: #3b82f6;
    padding: 9px 22px;
    font-size: 13px;
}
QPushButton#primaryBtn:hover { background-color: #3b82f6; }

QPushButton#dangerBtn {
    background-color: #7f1d1d;
    color: #fca5a5;
    border-color: #ef4444;
}
QPushButton#dangerBtn:hover { background-color: #ef4444; color: white; }

QPushButton#successBtn {
    background-color: #14532d;
    color: #86efac;
    border-color: #22c55e;
}
QPushButton#successBtn:hover { background-color: #22c55e; color: white; }

/* ── ComboBox ───────────────────────────────── */
QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    min-width: 160px;
}
QComboBox:hover { border-color: #3b82f6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #e2e8f0;
    selection-background-color: #3b82f6;
}

/* ── Table ──────────────────────────────────── */
QTableWidget, QTableView {
    background-color: #111827;
    alternate-background-color: #0f1623;
    border: 1px solid #1e293b;
    border-radius: 6px;
    gridline-color: #1e293b;
    color: #e2e8f0;
}
QTableWidget::item:selected { background-color: #1e3a5f; color: #93c5fd; }
QHeaderView::section {
    background-color: #0d1117;
    color: #60a5fa;
    border: none;
    border-right: 1px solid #1e293b;
    border-bottom: 2px solid #3b82f6;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Text Areas / Line Edit ─────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a1f2e;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QTextEdit:focus { border-color: #3b82f6; }

/* ── Scrollbar ──────────────────────────────── */
QScrollBar:vertical {
    background: #0f1117;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #3b82f6; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #0f1117;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #3b82f6; }

/* ── Group Box ──────────────────────────────── */
QGroupBox {
    border: 1px solid #1e293b;
    border-radius: 8px;
    margin-top: 16px;
    padding: 12px;
    color: #94a3b8;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #60a5fa;
}

/* ── Labels ─────────────────────────────────── */
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #e2e8f0;
    padding: 4px 0;
}
QLabel#infoLabel {
    color: #64748b;
    font-size: 12px;
}
QLabel#resultLabel {
    background-color: #0d1f3c;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    padding: 10px 14px;
    color: #93c5fd;
    font-size: 12px;
}
QLabel#successLabel {
    color: #86efac;
    font-weight: 600;
}
QLabel#warningLabel {
    color: #fbbf24;
    font-weight: 600;
}
QLabel#errorLabel {
    color: #f87171;
    font-weight: 600;
}

/* ── CheckBox / RadioButton ─────────────────── */
QCheckBox, QRadioButton { color: #94a3b8; spacing: 6px; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 15px; height: 15px;
    border: 1px solid #334155;
    border-radius: 3px;
    background-color: #1e293b;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}
QRadioButton::indicator { border-radius: 7px; }
QRadioButton::indicator:checked { background-color: #2563eb; border-color: #3b82f6; }

/* ── SpinBox ────────────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #1a1f2e;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 8px;
    color: #e2e8f0;
}

/* ── Splitter ───────────────────────────────── */
QSplitter::handle { background-color: #1e293b; width: 2px; height: 2px; }

/* ── ToolTip ────────────────────────────────── */
QToolTip {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #3b82f6;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ── Status Bar ─────────────────────────────── */
QStatusBar {
    background-color: #0d1117;
    color: #475569;
    border-top: 1px solid #1e293b;
    font-size: 11px;
    padding: 2px 8px;
}

/* ── Progress Bar ───────────────────────────── */
QProgressBar {
    background-color: #1e293b;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 4px;
}

/* ── Divider card ───────────────────────────── */
QFrame#card {
    background-color: #111827;
    border: 1px solid #1e293b;
    border-radius: 8px;
}
"""
