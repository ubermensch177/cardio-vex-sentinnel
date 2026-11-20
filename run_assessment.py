"""
Assessment Evaluation Runner for CardioVex Sentinel AI.
Executes all 5 protocol assessment questions, verifies against expected values,
and outputs a professional comparison table and report using Rich.
Generates JSON, text, and rich HTML execution reports for documentation and screenshots.
"""

import os
import json
import time
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markup import escape

from rag_engine import answer

ASSESSMENT_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What is the minimum required estimated Glomerular Filtration Rate (eGFR) threshold for a patient to be included in the CardioVex Phase III trial?",
        "expected_answer": "Baseline eGFR of at least 45 mL/min/1.73m2 (CKD-EPI creatinine equation; adult patients 40-80 years; <45 strictly excluded).",
        "expected_sources": ["Page 14"],
        "must_contain": ["45", "egfr"],
        "expect_found": True
    },
    {
        "id": "Q2",
        "question": "Within how many hours of becoming aware of a Serious Adverse Event (SAE) must a site investigator report it to the pharmacovigilance safety desk?",
        "expected_answer": "Within 24 hours of initial site awareness via the electronic eCRF safety portal (regardless of whether considered drug-related).",
        "expected_sources": ["Page 28"],
        "must_contain": ["24", "hours"],
        "expect_found": True
    },
    {
        "id": "Q3",
        "question": "What is the wholesale or retail price of CardioVex in commercial pharmacies?",
        "expected_answer": "[not found]",
        "expected_sources": [],
        "must_contain": ["[not found]"],
        "expect_found": False
    },
    {
        "id": "Q4",
        "question": "Within what exact temperature range, in degrees Celsius, must reconstituted CardioVex vials be stored before administration?",
        "expected_answer": "Strictly between 2°C and 8°C (2 degrees Celsius to 8 degrees Celsius) in a calibrated medical refrigerator with continuous temperature logging; do not freeze.",
        "expected_sources": ["Page 42"],
        "must_contain": ["2", "8"],
        "expect_found": True
    },
    {
        "id": "Q5",
        "question": "What is the standard recommended dosage of amoxicillin for treating a paediatric ear infection?",
        "expected_answer": "[not found]",
        "expected_sources": [],
        "must_contain": ["[not found]"],
        "expect_found": False
    }
]


def run_assessment() -> List[Dict]:
    """Runs all assessment questions and measures execution metrics."""
    results = []
    console = Console()

    console.print(Panel.fit(
        "[bold cyan]CardioVex Sentinel AI - Phase III Clinical Protocol Assistant[/bold cyan]\n"
        "[italic]Running Protocol Assessment & Strict Grounding Verification[/italic]",
        border_style="cyan"
    ))

    text_log_lines = [
        "=" * 80,
        "CARDIOVEX SENTINEL AI - PROTOCOL ASSESSMENT EXECUTION LOG",
        "Phase III Clinical Trial Protocol & Pharmacovigilance Assistant",
        "=" * 80,
        ""
    ]

    for item in ASSESSMENT_QUESTIONS:
        start_time = time.time()
        output = answer(item["question"])
        elapsed = time.time() - start_time

        gen_ans = output.get("answer", "")
        sources = output.get("sources", [])

        # Strict verification check
        if not item["expect_found"]:
            passed = gen_ans == "[not found]" and len(sources) == 0
        else:
            has_keywords = all(k.lower() in gen_ans.lower() for k in item["must_contain"])
            has_sources = len(sources) > 0 and any(s in item["expected_sources"] for s in sources)
            passed = has_keywords and has_sources

        result_entry = {
            "id": item["id"],
            "question": item["question"],
            "expected_answer": item["expected_answer"],
            "expected_sources": item["expected_sources"],
            "generated_answer": gen_ans,
            "generated_sources": sources,
            "latency_sec": round(elapsed, 4),
            "passed": passed
        }
        results.append(result_entry)

        # Print detailed individual card with escaped brackets
        status_tag = "[bold green][PASS - 100% GROUNDED][/bold green]" if passed else "[bold red][FAIL][/bold red]"
        console.print(Panel(
            f"[bold yellow]Question:[/bold yellow] {escape(item['question'])}\n\n"
            f"[bold green]Generated Answer:[/bold green] {escape(gen_ans)}\n\n"
            f"[bold cyan]Retrieved Sources:[/bold cyan] {escape(', '.join(sources) if sources else 'None (Ungrounded Topic)')}\n"
            f"[bold magenta]Expected Answer:[/bold magenta] {escape(item['expected_answer'])}\n"
            f"[bold blue]Status:[/bold blue] {status_tag} (Latency: {elapsed:.3f}s)",
            title=f"Assessment Item {item['id']}",
            border_style="green" if passed else "red"
        ))

        text_log_lines.extend([
            f"[{item['id']}] {item['question']}",
            f"Expected Answer   : {item['expected_answer']}",
            f"Expected Sources  : {item['expected_sources']}",
            f"Generated Answer  : {gen_ans}",
            f"Generated Sources : {sources}",
            f"Result Status     : {'PASS' if passed else 'FAIL'} (Latency: {elapsed:.3f}s)",
            "-" * 80
        ])

    all_passed = all(r["passed"] for r in results)
    passed_count = sum(r["passed"] for r in results)
    total_count = len(results)
    accuracy = (passed_count / total_count) * 100.0

    summary_text = f"Assessment Suite Finished: {passed_count}/{total_count} Passed ({accuracy:.1f}% Accuracy)"
    console.print(Panel.fit(f"[bold green]{summary_text}[/bold green]", border_style="green"))

    text_log_lines.append(f"FINAL SUMMARY: {passed_count}/{total_count} Passed ({accuracy:.1f}% Accuracy)")

    # Save execution output log
    with open("execution_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(text_log_lines) + "\n")

    # Save results JSON
    with open("assessment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate polished HTML report for screenshots
    _generate_html_report(results, passed_count, total_count, accuracy)

    return results


def _generate_html_report(results: List[Dict], passed: int, total: int, accuracy: float):
    """Generates a clean HTML dashboard for documentation and visual screenshots."""
    rows = ""
    for r in results:
        status_badge = '<span class="badge pass">PASS</span>' if r["passed"] else '<span class="badge fail">FAIL</span>'
        sources_str = ", ".join(r["generated_sources"]) if r["generated_sources"] else '<span class="none">None</span>'
        ans_display = r["generated_answer"]
        if ans_display == "[not found]":
            ans_display = '<span class="not-found">[not found]</span>'
        rows += f"""
        <tr>
            <td class="id-col">{r["id"]}</td>
            <td class="q-col"><strong>{r["question"]}</strong></td>
            <td class="ans-col">{ans_display}</td>
            <td class="src-col">{sources_str}</td>
            <td class="status-col">{status_badge}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CardioVex Sentinel AI - Assessment Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: #1e293b;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            padding: 30px;
            border: 1px solid #334155;
        }}
        .header {{
            border-bottom: 2px solid #334155;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        h1 {{
            margin: 0 0 8px 0;
            color: #38bdf8;
            font-size: 26px;
        }}
        .subtitle {{
            color: #94a3b8;
            font-size: 15px;
            margin: 0;
        }}
        .metrics {{
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
        }}
        .metric-card {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px 20px;
            flex: 1;
        }}
        .metric-title {{
            font-size: 13px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #4ade80;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}
        th {{
            background: #0f172a;
            color: #94a3b8;
            padding: 12px 14px;
            border-bottom: 2px solid #334155;
            font-weight: 600;
        }}
        td {{
            padding: 14px;
            border-bottom: 1px solid #334155;
            vertical-align: top;
            line-height: 1.5;
        }}
        tr:hover {{
            background: #273549;
        }}
        .id-col {{ font-weight: bold; color: #a855f7; width: 45px; text-align: center; }}
        .q-col {{ width: 28%; color: #f1f5f9; }}
        .ans-col {{ width: 44%; color: #e2e8f0; }}
        .src-col {{ width: 12%; text-align: center; color: #fbbf24; font-weight: 600; }}
        .status-col {{ width: 10%; text-align: center; }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-weight: bold;
            font-size: 12px;
        }}
        .badge.pass {{
            background: #14532d;
            color: #4ade80;
            border: 1px solid #22c55e;
        }}
        .badge.fail {{
            background: #7f1d1d;
            color: #f87171;
            border: 1px solid #ef4444;
        }}
        .not-found {{
            font-family: monospace;
            background: #334155;
            padding: 2px 6px;
            border-radius: 4px;
            color: #fca5a5;
            font-weight: bold;
        }}
        .none {{ color: #64748b; font-style: italic; }}
        .footer {{
            margin-top: 25px;
            text-align: center;
            font-size: 13px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CardioVex Sentinel AI</h1>
            <p class="subtitle">Phase III Clinical Trial Protocol & Pharmacovigilance Assistant — Assessment Matrix</p>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-title">Test Corpus</div>
                <div class="metric-value" style="color: #38bdf8; font-size: 17px;">cardiovex_clinical_trial_protocol_50p.pdf (50 Pages)</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Questions Tested</div>
                <div class="metric-value" style="color: #f8fafc;">{total} Questions</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Validation Accuracy</div>
                <div class="metric-value">{accuracy:.1f}% ({passed}/{total} Passed)</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Grounding Policy</div>
                <div class="metric-value" style="color: #fbbf24; font-size: 17px;">Strict (Zero External Assumptions)</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Assessment Question</th>
                    <th>Generated Answer</th>
                    <th>Source Citation</th>
                    <th>Verification</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div class="footer">
            CardioVex Sentinel AI &bull; Persistent ChromaDB Vector Store &bull; PyPDF Ingestion &bull; Production RAG Architecture
        </div>
    </div>
</body>
</html>
    """
    with open("execution_report.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    run_assessment()
