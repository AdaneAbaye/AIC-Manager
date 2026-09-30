"""Tests for turning the agents' markdown into the approved/rejected lists shown in the UI."""

import unittest
from types import SimpleNamespace

from src import config
from src import research_flow as rf

ARCHITECT_TABLE = """
## Final allocation

| Ticker | Allocation % | $ Amount | Rationale |
|--------|--------------|----------|-----------|
| **JNJ** | **40%** | **$800** | Stable cash flow |
| PG | 35% | $700 | Defensive demand |
| KO | 25% | $500 | Dividend history |
| **Total** | **100%** | **$2,000** | |

The final allocation is based only on assets that passed the Risk Manager's audit.
"""

RISK_OUTPUT = """
### APPROVED
- JNJ: low beta, strong balance sheet
- PG: defensive

### REJECTED
- **XYZ**: Volatility 48%, P/E 70, Debt/Equity 1.9, too risky for the thesis
- ABC (Acme Corp) - missing recent financial statements
| NVDA | Volatility 45% | P/E 65 | elevated risk |

### Summary
Two approved names remain.
"""


class TestAllocations(unittest.TestCase):
    def test_total_row_is_not_an_asset(self):
        parsed = rf.parse_recommendations_for_ui(ARCHITECT_TABLE)
        tickers = [a["ticker"] for a in parsed["allocations"]]
        self.assertEqual(tickers, ["JNJ", "PG", "KO"])
        self.assertEqual(parsed["allocations"][0]["amount"], 800)

    def test_hebrew_total_row(self):
        text = "| NVDA | 60% | $600 | צמיחה |\n| MSFT | 40% | $400 | יציבות |\n| סה\"כ | 100% | $1,000 | |"
        tickers = [a["ticker"] for a in rf.parse_recommendations_for_ui(text)["allocations"]]
        self.assertEqual(tickers, ["NVDA", "MSFT"])

    def test_inline_allocation_is_not_a_rejection(self):
        parsed = rf.parse_recommendations_for_ui("- MSFT: 50% ($250)\n- AAPL: 50% ($250)")
        self.assertEqual([a["ticker"] for a in parsed["allocations"]], ["MSFT", "AAPL"])
        self.assertEqual(parsed["rejected"], [])

    def test_validator_accepts_thousands_separators(self):
        text = "| AAPL | 60% | $1,200 | growth |\n| MSFT | 40% | $800 | quality |"
        out = rf._validate_and_enforce_allocation(text, 2000, is_dca=False)
        self.assertNotIn("Validation", out)

    def test_validator_flags_wrong_totals(self):
        text = "| AAPL | 60% | $600 | growth |\n| MSFT | 20% | $200 | quality |"
        out = rf._validate_and_enforce_allocation(text, 1000, is_dca=False)
        self.assertIn("80.0%", out)


class TestRejections(unittest.TestCase):
    def test_risk_manager_section(self):
        rejected = {r["ticker"]: r["reason"] for r in rf.parse_rejections(RISK_OUTPUT)}
        self.assertEqual(set(rejected), {"XYZ", "ABC", "NVDA"})
        self.assertIn("Volatility 48%", rejected["XYZ"])
        self.assertNotIn("JNJ", rejected)  # approved list items are not rejections

    def test_sentences_anywhere(self):
        text = "Rejected NVDA: Volatility 45%, P/E 65.\nTSLA was rejected due to extreme volatility."
        self.assertEqual({r["ticker"] for r in rf.parse_rejections(text)}, {"NVDA", "TSLA"})

    def test_lowercase_words_are_not_tickers(self):
        self.assertEqual(rf.parse_rejections("We rejected all assets because none fit."), [])

    def test_hebrew_section(self):
        text = "## נכסים שנדחו\n- XYZ: תנודתיות גבוהה\n\n## סיכום\n- JNJ: מאושר"
        self.assertEqual([r["ticker"] for r in rf.parse_rejections(text)], ["XYZ"])


class TestSafety(unittest.TestCase):
    def test_braces_are_escaped_for_crewai(self):
        self.assertEqual(rf._escape_template_braces("AI {stocks}"), "AI (stocks)")

    def test_errors_do_not_leak_details(self):
        msg = rf._format_llm_error(RuntimeError("anthropic 500 internal trace sk-abcdefghijklmnopqrstuvwxyz"))
        self.assertNotIn("sk-", msg)
        self.assertNotIn("trace", msg)
        self.assertIn("busy", rf._format_llm_error(RuntimeError("429 rate limit")))


class TestSession(unittest.TestCase):
    def test_rejections_come_from_the_risk_manager(self):
        tasks = [SimpleNamespace(raw=t) for t in ("scout picks", "analysis", RISK_OUTPUT, ARCHITECT_TABLE)]
        fake_result = SimpleNamespace(raw=ARCHITECT_TABLE, tasks_output=tasks)
        fake_crew = SimpleNamespace(kickoff=lambda: fake_result)
        old = (rf.create_research_crew, config.ANTHROPIC_API_KEY)
        rf.create_research_crew = lambda **kw: fake_crew
        config.ANTHROPIC_API_KEY = "test"
        try:
            out = rf.run_research_session("stable growth", 2000, is_dca=False)
        finally:
            rf.create_research_crew, config.ANTHROPIC_API_KEY = old
        self.assertEqual([a["ticker"] for a in out["approved_assets"]], ["JNJ", "PG", "KO"])
        self.assertEqual({r["ticker"] for r in out["rejected_assets"]}, {"XYZ", "ABC", "NVDA"})
        self.assertEqual(len(out["agent_logs"]), 4)
        self.assertIn("### REJECTED", out["agent_logs"][2]["markdown"])
        self.assertNotIn("Validation", out["raw_report"])


if __name__ == "__main__":
    unittest.main()
