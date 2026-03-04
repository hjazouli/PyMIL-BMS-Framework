import base64
import io
import os
from datetime import datetime
from typing import Any, Dict
from .base.base_reporter import BaseReporter
from .shared.logger import logger

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

_VERDICT_CSS = {
    "PASS": "#27ae60",
    "FAIL": "#e74c3c",
    "INCONCLUSIVE": "#f39c12",
    "BLOCKED": "#95a5a6",
}

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PyXIL-BMS — Test Report</title>
<style>
  :root {{
    --bg: #0f1117; --card: #1a1e2e; --border: #2d3250;
    --text: #e2e8f0; --muted: #8892a4;
    --pass: #27ae60; --fail: #e74c3c; --inc: #f39c12; --blocked: #95a5a6;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text);
         font-family: 'Segoe UI', system-ui, sans-serif; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; color: #7c9ef8; margin-bottom: .25rem; }}
  .meta {{ color: var(--muted); font-size: .9rem; margin-bottom: 2rem; }}
  .stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 2rem; }}
  .stat {{ background: var(--card); border: 1px solid var(--border);
           border-radius: 12px; padding: 1rem 1.5rem; min-width: 140px; }}
  .stat-val {{ font-size: 2rem; font-weight: 700; }}
  .stat-lbl {{ font-size: .8rem; color: var(--muted); margin-top: .25rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem;
           background: var(--card); border-radius: 12px; overflow: hidden; }}
  th {{ background: #1f2640; color: var(--muted); padding: .75rem 1rem;
        text-align: left; font-size: .8rem; text-transform: uppercase;
        letter-spacing: .05em; }}
  td {{ padding: .75rem 1rem; border-top: 1px solid var(--border); }}
  .badge {{ display: inline-block; padding: .2rem .7rem; border-radius: 20px;
            font-size: .78rem; font-weight: 600; color: #fff; }}
  .badge-PASS {{ background: var(--pass); }}
  .badge-FAIL {{ background: var(--fail); }}
  .badge-INCONCLUSIVE {{ background: var(--inc); }}
  .badge-BLOCKED {{ background: var(--blocked); }}
  .tc-section {{ background: var(--card); border: 1px solid var(--border);
                 border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  .tc-header {{ display: flex; align-items: center; gap: 1rem;
                margin-bottom: 1rem; }}
  .tc-id {{ font-size: 1rem; font-weight: 700; color: #7c9ef8; }}
  .tc-name {{ color: var(--text); }}
  .tc-meta {{ font-size: .8rem; color: var(--muted); }}
  .signal-list {{ display: flex; flex-wrap: wrap; gap: .4rem;
                  margin: .5rem 0 1rem; }}
  .signal-tag {{ background: #2d3250; border-radius: 6px; padding: .2rem .6rem;
                 font-size: .78rem; color: #9ab3f5; }}
  .plot-img {{ width: 100%; max-width: 900px; border-radius: 8px;
               margin-top: 1rem; }}
  .details {{ font-size: .85rem; color: var(--muted); margin-top: .5rem; }}
  .verdict-table {{ font-size: .78rem; }}
  .verdict-table th {{ font-size: .75rem; }}
  summary {{ cursor: pointer; font-size: .85rem; color: #9ab3f5;
             margin-top: .75rem; }}
</style>
</head>
<body>
<h1>📊 PyXIL-BMS Test Report</h1>
<p class="meta">Generated: {generated_at}</p>

<div class="stats">
  <div class="stat">
    <div class="stat-val" style="color:#7c9ef8">{total}</div>
    <div class="stat-lbl">Total Tests</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:var(--pass)">{pass_count}</div>
    <div class="stat-lbl">PASS</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:var(--fail)">{fail_count}</div>
    <div class="stat-lbl">FAIL</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:#7c9ef8">{pass_rate:.0f}%</div>
    <div class="stat-lbl">Pass Rate</div>
  </div>
</div>

<h2 style="margin-bottom:1rem;color:#9ab3f5">Summary</h2>
<table>
  <thead>
    <tr>
      <th>ID</th><th>Name</th><th>Verdict</th><th>Duration (ms)</th>
    </tr>
  </thead>
  <tbody>
    {summary_rows}
  </tbody>
</table>

<h2 style="margin-bottom:1rem;color:#9ab3f5">Test Details</h2>
{test_sections}
</body>
</html>"""

class Reporter(BaseReporter):
    """
    Concrete implementation of the HTML report generator.
    """

    def generate(self, results: Dict[str, Dict[str, Any]], output_dir: str = "reports") -> str:
        os.makedirs(output_dir, exist_ok=True)

        total = len(results)
        counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0, "BLOCKED": 0}
        for r in results.values():
            v = r.get("verdict", "FAIL")
            counts[v] = counts.get(v, 0) + 1

        pass_rate = (counts["PASS"] / total * 100) if total else 0.0

        summary_rows = self._build_summary_rows(results)
        test_sections = self._build_test_sections(results)

        html = _HTML_TEMPLATE.format(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=total,
            pass_count=counts["PASS"],
            fail_count=counts["FAIL"],
            pass_rate=pass_rate,
            summary_rows=summary_rows,
            test_sections=test_sections,
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"report_{ts}.html")
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(html)

        logger.info("CAMPAIGN_END", message=f"HTML report written to {filename}")
        return os.path.abspath(filename)

    def _build_summary_rows(self, results: Dict[str, Dict[str, Any]]) -> str:
        rows = []
        for tid, res in results.items():
            verdict = res.get("verdict", "FAIL")
            badge = f'<span class="badge badge-{verdict}">{verdict}</span>'
            rows.append(
                f"<tr><td><strong>{tid}</strong></td><td>{res.get('name', tid)}</td>"
                f"<td>{badge}</td><td>{res.get('duration_ms', 0):.1f}</td></tr>"
            )
        return "\n".join(rows)

    def _build_test_sections(self, results: Dict[str, Dict[str, Any]]) -> str:
        sections = []
        for tid, res in results.items():
            verdict = res.get("verdict", "FAIL")
            badge = f'<span class="badge badge-{verdict}">{verdict}</span>'
            history = res.get("verdict_history", [])
            
            verdict_rows = ""
            if history:
                verdict_rows = "<details><summary>Verdict trace</summary><table><thead><tr><th>Signal</th><th>Actual</th><th>Verdict</th></tr></thead><tbody>"
                for rec in history[:10]:
                    verdict_rows += f"<tr><td>{rec['signal']}</td><td>{rec['actual']:.4g}</td><td>{rec['verdict']}</td></tr>"
                verdict_rows += "</tbody></table></details>"

            sections.append(
                f'<div class="tc-section"><div class="tc-header"><span class="tc-id">{tid}</span>'
                f'<span class="tc-name">{res.get("name", tid)}</span>{badge}</div>'
                f'<p class="details">{res.get("details", "")}</p>{verdict_rows}</div>'
            )
        return "\n".join(sections)
