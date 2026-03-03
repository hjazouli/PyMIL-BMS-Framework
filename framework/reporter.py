"""
framework/reporter.py — Layer 1

Responsibility:
    Generates a single, fully self-contained HTML report from campaign
    results. All CSS, JavaScript, and chart images (matplotlib PNGs) are
    embedded inline — the output file has zero external dependencies.
"""

import base64
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available — signal plots will be omitted.")

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
<title>{campaign_name} — Test Report</title>
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
<h1>📊 {campaign_name}</h1>
<p class="meta">Generated: {generated_at} &nbsp;|&nbsp; Total duration: {duration_s:.2f}s</p>

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
    <div class="stat-val" style="color:var(--inc)">{inc_count}</div>
    <div class="stat-lbl">INCONCLUSIVE</div>
  </div>
  <div class="stat">
    <div class="stat-val" style="color:var(--blocked)">{blocked_count}</div>
    <div class="stat-lbl">BLOCKED</div>
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


class Reporter:
    """
    Self-contained HTML report generator.

    Embeds matplotlib PNGs as base64 data URIs so the output HTML file
    is fully portable and requires no external assets.
    """

    def generate(
        self,
        campaign_name: str,
        results: Dict[str, Dict[str, Any]],
        duration_s: float,
        output_dir: str = "reports",
    ) -> str:
        """
        Build and write the HTML report to *output_dir*.

        Args:
            campaign_name: Human-readable campaign identifier.
            results:       Output of Sequencer.run().
            duration_s:    Total campaign wall-clock time in seconds.
            output_dir:    Directory to write the HTML file into.

        Returns:
            Absolute path of the generated HTML file.
        """
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
            campaign_name=campaign_name,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration_s=duration_s,
            total=total,
            pass_count=counts["PASS"],
            fail_count=counts["FAIL"],
            inc_count=counts["INCONCLUSIVE"],
            blocked_count=counts["BLOCKED"],
            pass_rate=pass_rate,
            summary_rows=summary_rows,
            test_sections=test_sections,
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"report_{ts}.html")
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(html)

        logger.info("HTML report written → %s", os.path.abspath(filename))
        print(f"\n  📄 Report saved → {os.path.abspath(filename)}\n")
        return os.path.abspath(filename)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_summary_rows(self, results: Dict[str, Dict[str, Any]]) -> str:
        rows = []
        for tid, res in results.items():
            verdict = res.get("verdict", "FAIL")
            badge = f'<span class="badge badge-{verdict}">{verdict}</span>'
            rows.append(
                f"<tr>"
                f"<td><strong>{tid}</strong></td>"
                f"<td>{res.get('name', tid)}</td>"
                f"<td>{badge}</td>"
                f"<td>{res.get('duration_ms', 0):.1f}</td>"
                f"</tr>"
            )
        return "\n    ".join(rows)

    def _build_test_sections(
        self, results: Dict[str, Dict[str, Any]]
    ) -> str:
        sections = []
        for tid, res in results.items():
            verdict = res.get("verdict", "FAIL")
            v_color = _VERDICT_CSS.get(verdict, "#95a5a6")
            badge = f'<span class="badge badge-{verdict}">{verdict}</span>'

            # Signal tags
            signals_in = res.get("signals_in", [])
            signals_out = res.get("signals_out", [])
            in_tags = "".join(
                f'<span class="signal-tag">⬆ {s}</span>' for s in signals_in
            )
            out_tags = "".join(
                f'<span class="signal-tag">⬇ {s}</span>' for s in signals_out
            )

            # Verdict detail table
            history = res.get("verdict_history", [])
            verdict_rows = ""
            if history:
                sample = history[:20]  # cap at 20 rows to keep HTML lean
                verdict_rows = (
                    "<details><summary>Verdict trace "
                    f"({len(history)} evaluations, showing first {len(sample)})"
                    "</summary>"
                    '<table class="verdict-table" style="margin-top:.5rem">'
                    "<thead><tr><th>Signal</th><th>Expected</th>"
                    "<th>Actual</th><th>Δ</th><th>Band</th>"
                    "<th>Verdict</th></tr></thead><tbody>"
                )
                for rec in sample:
                    v_badge = (
                        f'<span class="badge badge-{rec["verdict"]}">'
                        f'{rec["verdict"]}</span>'
                    )
                    verdict_rows += (
                        f"<tr>"
                        f"<td>{rec['signal']}</td>"
                        f"<td>{rec['expected']:.4g}</td>"
                        f"<td>{rec['actual']:.4g}</td>"
                        f"<td>{rec['delta']:.4g}</td>"
                        f"<td>{rec['band']}</td>"
                        f"<td>{v_badge}</td>"
                        f"</tr>"
                    )
                verdict_rows += "</tbody></table></details>"

            # Signal plots
            plot_html = self._generate_plot(tid, res)

            sections.append(
                f'<div class="tc-section">'
                f'<div class="tc-header">'
                f'<span class="tc-id">{tid}</span>'
                f'<span class="tc-name">{res.get("name", tid)}</span>'
                f'{badge}'
                f'</div>'
                f'<div class="tc-meta">{res.get("duration_ms", 0):.1f} ms</div>'
                f'<p style="margin:.5rem 0 .25rem;font-size:.8rem;color:var(--muted)">Inputs:</p>'
                f'<div class="signal-list">{in_tags or "<em style=\'color:var(--muted)\'>none</em>"}</div>'
                f'<p style="margin:.5rem 0 .25rem;font-size:.8rem;color:var(--muted)">Outputs:</p>'
                f'<div class="signal-list">{out_tags or "<em style=\'color:var(--muted)\'>none</em>"}</div>'
                f'<p class="details">{res.get("details", "")}</p>'
                f'{verdict_rows}'
                f'{plot_html}'
                f'</div>'
            )
        return "\n".join(sections)

    def _generate_plot(self, tid: str, res: Dict[str, Any]) -> str:
        """Generate a matplotlib figure for the test and return inline HTML."""
        if not _MATPLOTLIB_AVAILABLE:
            return ""

        measurement = res.get("measurement")
        if measurement is None:
            return ""

        signals = measurement.available_signals()
        if not signals:
            return ""

        try:
            n_plots = len(signals)
            fig, axes = plt.subplots(
                n_plots, 1,
                figsize=(10, 2.5 * n_plots),
                facecolor="#1a1e2e",
                sharex=False,
            )
            if n_plots == 1:
                axes = [axes]

            for ax, sig in zip(axes, signals):
                series = measurement.get_series(sig)
                if not series:
                    continue
                timestamps = [t for t, _ in series]
                values = [v for _, v in series]
                ax.set_facecolor("#0f1117")
                ax.plot(timestamps, values, color="#7c9ef8", linewidth=1.5,
                        label="measured")
                ax.set_ylabel(sig, color="#8892a4", fontsize=8)
                ax.tick_params(colors="#8892a4", labelsize=7)
                ax.spines[:].set_color("#2d3250")
                ax.legend(fontsize=7, facecolor="#1a1e2e", labelcolor="#e2e8f0")

            axes[-1].set_xlabel("Time (s)", color="#8892a4", fontsize=8)
            fig.suptitle(f"{tid} — Output Signals", color="#e2e8f0", fontsize=11)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f'<img class="plot-img" src="data:image/png;base64,{b64}" alt="{tid} signal plot">'

        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Plot generation failed for %s: %s", tid, exc)
            return ""
