import os
import pandas as pd
from emailer import send_email, wrap_html

# Build a sample DataFrame similar to the screener output
data = [
    {"Stock": "ABC", "Current_Price": "₹123.45", "Target_Sell": "₹150.00", "Hold_Days": "30d", "Win_Prob": "85%", "Raw_Score": 85, "Category": "Momentum"},
    {"Stock": "DEF", "Current_Price": "₹45.67", "Target_Sell": "₹60.00", "Hold_Days": "45d", "Win_Prob": "62%", "Raw_Score": 62, "Category": "Value"},
    {"Stock": "GHI", "Current_Price": "₹9.12", "Target_Sell": "₹18.00", "Hold_Days": "90d", "Win_Prob": "32%", "Raw_Score": 32, "Category": "Recovery"},
]

df = pd.DataFrame(data)
cols = ["Stock", "Current_Price", "Target_Sell", "Hold_Days", "Win_Prob", "Category", "Raw_Score"]
def score_style(v):
    try:
        val = float(v)
    except Exception:
        return ""
    if val >= 75:
        return 'color: #0b8a3e; font-weight:600'
    if val >= 50:
        return 'color: #d97706;'
    return 'color: #b91c1c;'

sub = df[cols]

# Generate base HTML and post-process Raw_Score column to add inline styles
html_table = sub.to_html(index=False, classes='report-table', border=0, escape=True)

import re

# determine index of Raw_Score column
hdrs = re.findall(r'<th[^>]*>(.*?)</th>', html_table, flags=re.S)
try:
    score_idx = hdrs.index('Raw_Score')
except ValueError:
    score_idx = None

def style_cell(value):
    try:
        val = float(value)
    except Exception:
        return value
    if val >= 75:
        return f'<span style="color:#0b8a3e;font-weight:600">{value}</span>'
    if val >= 50:
        return f'<span style="color:#d97706">{value}</span>'
    return f'<span style="color:#b91c1c">{value}</span>'

if score_idx is not None:
    # process each row's <td> entries
    def repl_row(match):
        row_html = match.group(0)
        tds = re.findall(r'(<td[^>]*>)(.*?)(</td>)', row_html, flags=re.S)
        if not tds:
            return row_html
        new_row = row_html
        # find nth td and replace inner content
        for i, td in enumerate(tds):
            if i == score_idx:
                full = ''.join(td)
                inner = td[1]
                styled_inner = style_cell(inner)
                new_full = td[0] + styled_inner + td[2]
                new_row = new_row.replace(full, new_full, 1)
        return new_row

    html_table = re.sub(r'<tr[^>]*>.*?</tr>', repl_row, html_table, flags=re.S)

body_html = '<h2>Sample Screener Output</h2>' + html_table
html = wrap_html('Sample Alpha Intelligence Report', body_html)

recipient = os.getenv('REPORT_RECIPIENT', 'dkushal1109@gmail.com')
subject = 'Sample Formatted Report'
plain = 'This is a sample formatted report. If you see HTML, your client supports it.'

send_email(recipient, subject, plain, html=html)
print('Sample email sent to', recipient)
