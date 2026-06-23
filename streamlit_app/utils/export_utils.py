"""
RetailPulse Dashboard - Export Utilities (CSV bundling + PDF reports)
==========================================================================
Day 20's job, per the project plan: "Export functionality (CSV/PDF reports)"

TWO export paths are built here:
  1. CSV EXPORTS - per-dataset downloads (already partially present on
     individual pages like Day 16's forecast export) PLUS a single
     zipped bundle containing every exportable table at once, for a
     stakeholder who wants "everything" in one click.
  2. PDF REPORT - a polished, multi-section business summary combining
     headline KPIs from every model (forecasting, churn, inventory)
     into ONE shareable document - exactly what a non-technical
     stakeholder or your project submission PDF needs, without them
     having to open the dashboard at all.

WHY fpdf2 INSTEAD OF REPORTLAB OR AN HTML-TO-PDF LIBRARY?
fpdf2 has zero system-level dependencies (pure Python + a font
renderer), installs with a single pip command, and is explicitly
documented by its own maintainers for use inside Streamlit apps. For
a business-summary report (headline metrics + a few tables), it's a
much lighter footprint than ReportLab's steeper API or WeasyPrint's
need for system libraries like Pango/Cairo - important for keeping
this academic project's deployment simple (per the spec's "no VPN/
geo-restriction... fast initial load" live demo requirements).
"""

import pandas as pd
import numpy as np
import io
import zipfile
from datetime import datetime
from fpdf import FPDF


# ============================================================
# CSV BUNDLE EXPORT
# ============================================================

def build_csv_zip_bundle(dataframes_dict):
    """
    Packages multiple named DataFrames into a single in-memory ZIP
    file, so the user gets ONE download button instead of having to
    click through every page individually to grab each CSV. Returns
    raw bytes ready to hand to st.download_button.

    dataframes_dict: {"filename_without_extension": dataframe, ...}
    Entries with a None dataframe (data not available) are silently
    skipped rather than raising an error - consistent with this
    app's overall philosophy (see safe_load in data_loader.py) of
    degrading gracefully when a particular day's notebook output
    isn't present yet.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, df in dataframes_dict.items():
            if df is None:
                continue
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            zf.writestr(f"{name}.csv", csv_bytes)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# PDF REPORT GENERATION
# ============================================================

# A small, consistent color palette reused across every section of
# the PDF, so the document reads as ONE coherent report rather than
# stitched-together fragments with inconsistent styling.
COLOR_PRIMARY = (52, 73, 94)      # dark slate blue - headers
COLOR_ACCENT = (52, 152, 219)     # steelblue - section dividers
COLOR_SUCCESS = (39, 174, 96)     # green - PASS status
COLOR_WARNING = (230, 126, 34)    # orange - REVIEW status
COLOR_TEXT_MUTED = (127, 140, 141)  # grey - captions/footnotes


class RetailPulseReport(FPDF):
    """
    A thin subclass of FPDF that adds a consistent header and footer
    to EVERY page automatically (FPDF calls header()/footer() itself
    on each add_page()/output() cycle) - this is the standard fpdf2
    pattern for multi-page reports with repeating branding, rather
    than manually re-drawing the header on every section.
    """

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, "RetailPulse - Business Summary Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*COLOR_TEXT_MUTED)
        self.cell(0, 6, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.5)
        self.line(15, self.get_y() + 2, 195, self.get_y() + 2)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_TEXT_MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(4)

    def kpi_row(self, kpis):
        """
        Renders a row of label/value KPI pairs as evenly-spaced
        boxes - the PDF equivalent of Streamlit's st.metric() row,
        so the report's visual language matches the live dashboard.
        kpis: list of (label, value, status) tuples. status is
        'pass', 'warning', or None (no color coding).
        """
        n = len(kpis)
        col_width = 180 / n
        start_x = self.get_x()
        start_y = self.get_y()

        for i, (label, value, status) in enumerate(kpis):
            x = start_x + i * col_width
            self.set_xy(x, start_y)

            self.set_font("Helvetica", "", 8)
            self.set_text_color(*COLOR_TEXT_MUTED)
            self.multi_cell(col_width - 4, 5, label, align="L")

            self.set_xy(x, start_y + 6)
            self.set_font("Helvetica", "B", 13)
            if status == "pass":
                self.set_text_color(*COLOR_SUCCESS)
            elif status == "warning":
                self.set_text_color(*COLOR_WARNING)
            else:
                self.set_text_color(*COLOR_PRIMARY)
            self.multi_cell(col_width - 4, 7, str(value), align="L")

        self.set_xy(start_x, start_y + 18)
        self.set_text_color(0, 0, 0)

    def add_table(self, headers, rows, col_widths=None):
        """
        Renders a simple bordered table - headers in bold with a
        light background, data rows in regular weight. col_widths
        defaults to equal-width columns spanning the page if not
        specified.
        """
        if col_widths is None:
            col_widths = [180 / len(headers)] * len(headers)

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(236, 240, 241)
        self.set_text_color(*COLOR_PRIMARY)
        for header, w in zip(headers, col_widths):
            self.cell(w, 8, str(header), border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        for row in rows:
            for value, w in zip(row, col_widths):
                self.cell(w, 7, str(value), border=1, align="C")
            self.ln()
        self.ln(4)

    def add_paragraph(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(2)


def generate_business_report(
    forecast_metrics=None,
    churn_metrics=None,
    inventory_metrics=None,
    top_products_df=None,
    segment_summary_df=None,
    reorder_df=None,
):
    """
    Assembles the full multi-section PDF report from whatever data is
    available (each section is OPTIONAL and gracefully skipped if its
    corresponding metrics dict/dataframe is None) - same
    graceful-degradation philosophy used throughout this app, since a
    demo might run before every single day's notebook output exists.

    Returns: raw PDF bytes, ready for st.download_button.
    """
    pdf = RetailPulseReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ---------- Executive Summary ----------
    pdf.section_title("Executive Summary")
    pdf.add_paragraph(
        "This report summarizes the current state of the RetailPulse "
        "AI-Powered Customer Analytics and Demand Forecasting platform, "
        "covering demand forecasting accuracy, customer churn risk, and "
        "inventory optimization impact. Generated automatically from "
        "the latest saved model outputs."
    )
    pdf.ln(2)

    # ---------- Forecasting Section ----------
    if forecast_metrics:
        pdf.section_title("Demand Forecasting")
        mape = forecast_metrics.get("hybrid_mape", None)
        status = "pass" if (mape is not None and mape <= 12.0) else "warning"
        pdf.kpi_row([
            ("Prophet MAPE", f"{forecast_metrics.get('prophet_mape', 0):.2f}%", None),
            ("LSTM MAPE", f"{forecast_metrics.get('lstm_mape', 0):.2f}%", None),
            ("Hybrid MAPE", f"{mape:.2f}%" if mape is not None else "N/A", status),
        ])
        pdf.add_paragraph(
            f"The hybrid Prophet+LSTM ensemble forecast achieved a MAPE of "
            f"{mape:.2f}% against a project target of <= 12%. "
            f"{'This meets the acceptance criteria.' if status == 'pass' else 'This is above the target and warrants review.'}"
        )

    # ---------- Churn Section ----------
    if churn_metrics:
        pdf.section_title("Customer Churn Prediction")
        auc = churn_metrics.get("auc_roc", None)
        prec20 = churn_metrics.get("precision_at_top20", None)
        auc_status = "pass" if (auc is not None and auc >= 0.88) else "warning"
        prec_status = "pass" if (prec20 is not None and prec20 >= 0.75) else "warning"
        pdf.kpi_row([
            ("AUC-ROC", f"{auc:.3f}" if auc is not None else "N/A", auc_status),
            ("Precision@Top20%", f"{prec20:.3f}" if prec20 is not None else "N/A", prec_status),
            ("Observed Churn Rate", f"{churn_metrics.get('churn_rate', 0)*100:.1f}%", None),
        ])
        pdf.add_paragraph(
            "The XGBoost churn classifier identifies at-risk customers "
            "using RFM-derived behavioral features, evaluated against a "
            "time-based 90-day outcome window to avoid data leakage."
        )

        if segment_summary_df is not None and len(segment_summary_df) > 0:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Customer Segments", new_x="LMARGIN", new_y="NEXT")
            headers = ["Segment", "Customers", "% of Base"]
            rows = [
                [str(r["KMeans_Label"]), int(r["Count"]), f"{r['Pct_of_Customers']:.1f}%"]
                for _, r in segment_summary_df.head(7).iterrows()
            ]
            pdf.add_table(headers, rows, col_widths=[80, 50, 50])

    # ---------- Inventory Section ----------
    if inventory_metrics:
        pdf.section_title("Inventory Optimization")
        stockout_reduction = inventory_metrics.get("total_stockout_reduction_pct", None)
        inv_reduction = inventory_metrics.get("avg_inventory_reduction_pct", None)
        so_status = "pass" if (stockout_reduction is not None and 25 <= stockout_reduction <= 40) else "warning"
        inv_status = "pass" if (inv_reduction is not None and 25 <= inv_reduction <= 40) else "warning"
        pdf.kpi_row([
            ("Stockout Reduction", f"{stockout_reduction:.1f}%" if stockout_reduction is not None else "N/A", so_status),
            ("Inventory Reduction", f"{inv_reduction:.1f}%" if inv_reduction is not None else "N/A", inv_status),
            ("Target Range", "25-40%", None),
        ])
        pdf.add_paragraph(
            "Safety Stock, Reorder Point, and Economic Order Quantity "
            "(EOQ) were calculated for top Class A products, adjusted "
            "for forecasted demand growth, and validated via a 180-day "
            "simulated comparison against a naive reorder policy."
        )

        if reorder_df is not None and len(reorder_df) > 0:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Top Reorder Recommendations", new_x="LMARGIN", new_y="NEXT")
            headers = ["Product", "Reorder Point", "Order Qty"]
            rows = [
                [str(r["Description"])[:28], int(r["RecommendedReorderPoint"]), int(r["RecommendedOrderQty"])]
                for _, r in reorder_df.head(8).iterrows()
            ]
            pdf.add_table(headers, rows, col_widths=[100, 40, 40])

    # ---------- Top Products Section ----------
    if top_products_df is not None and len(top_products_df) > 0:
        pdf.section_title("Top Products by Revenue")
        headers = ["Product", "Revenue (GBP)"]
        rows = [
            [str(r.iloc[0])[:40], f"{r.iloc[1]:,.0f}"]
            for _, r in top_products_df.head(10).iterrows()
        ]
        pdf.add_table(headers, rows, col_widths=[130, 50])

    # ---------- Footer Note ----------
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*COLOR_TEXT_MUTED)
    pdf.multi_cell(
        0, 5,
        "This report was generated automatically from saved model "
        "outputs in the RetailPulse dashboard. Some sections may show "
        "'N/A' if the corresponding analysis notebook has not yet been run."
    )

    # fpdf2's output() returns a bytearray; convert to bytes for
    # Streamlit's download_button, which expects bytes-like data.
    return bytes(pdf.output())
