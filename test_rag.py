"""
Comprehensive Test Suite for CardioVex Sentinel AI.
Validates:
1. answer() function signature and response structure.
2. Accurate retrieval and answers for all 5 assessment questions.
3. Strict grounding and exact '[not found]' output for missing information.
4. Correct source citation tracking.
5. ChromaDB persistence without re-embedding.
6. Robustness against invalid/empty inputs.
7. Multi-turn conversational follow-up questions with conversation history.
"""

import unittest
from rag_engine import answer
from ingestion import build_vectorstore
from conversation import ConversationManager


class TestCardioVexSentinel(unittest.TestCase):

    def test_answer_function_signature_and_format(self):
        """Verify answer() returns a dictionary with 'answer' and 'sources' keys."""
        res = answer("What is the eGFR cutoff?")
        self.assertIsInstance(res, dict, "Result must be a dict")
        self.assertIn("answer", res, "Dictionary must contain 'answer' key")
        self.assertIn("sources", res, "Dictionary must contain 'sources' key")
        self.assertIsInstance(res["answer"], str, "'answer' must be a string")
        self.assertIsInstance(res["sources"], list, "'sources' must be a list")

    def test_q1_egfr_threshold(self):
        """Q1: Minimum required eGFR threshold."""
        q = "What is the minimum required estimated Glomerular Filtration Rate (eGFR) threshold for a patient to be included in the CardioVex Phase III trial?"
        res = answer(q)
        ans = res["answer"]
        sources = res["sources"]

        self.assertIn("45", ans, "Answer must specify 45 mL/min/1.73m2 threshold")
        self.assertTrue(
            "eGFR" in ans or "estimated Glomerular Filtration Rate" in ans or "egfr" in ans.lower(),
            "Answer must reference eGFR"
        )
        self.assertTrue(
            "Page 14" in sources or 14 in sources,
            "Source must cite Page 14"
        )

    def test_q2_sae_reporting_timeline(self):
        """Q2: SAE reporting window to pharmacovigilance safety desk."""
        q = "Within how many hours of becoming aware of a Serious Adverse Event (SAE) must a site investigator report it to the pharmacovigilance safety desk?"
        res = answer(q)
        ans = res["answer"]
        sources = res["sources"]

        self.assertIn("24", ans, "Answer must specify 24 hours")
        self.assertIn("hours", ans.lower())
        self.assertTrue(
            "Page 28" in sources or 28 in sources,
            "Source must cite Page 28"
        )

    def test_q3_commercial_price_not_found(self):
        """Q3: Wholesale or retail price of CardioVex in commercial pharmacies (Must be [not found])."""
        q = "What is the wholesale or retail price of CardioVex in commercial pharmacies?"
        res = answer(q)
        self.assertEqual(res["answer"], "[not found]", "Unmentioned price must return exactly [not found]")
        self.assertEqual(res["sources"], [], "Sources must be empty for [not found]")

    def test_q4_reconstituted_vial_temperature(self):
        """Q4: Reconstituted vial storage temperature."""
        q = "Within what exact temperature range, in degrees Celsius, must reconstituted CardioVex vials be stored before administration?"
        res = answer(q)
        ans = res["answer"]
        sources = res["sources"]

        self.assertTrue("2" in ans and "8" in ans, "Answer must state 2°C to 8°C")
        self.assertTrue("celsius" in ans.lower() or "°c" in ans.lower())
        self.assertTrue(
            "Page 42" in sources or 42 in sources,
            "Source must cite Page 42"
        )

    def test_q5_amoxicillin_dosage_not_found(self):
        """Q5: Paediatric amoxicillin dosage (Must be [not found])."""
        q = "What is the standard recommended dosage of amoxicillin for treating a paediatric ear infection?"
        res = answer(q)
        self.assertEqual(res["answer"], "[not found]", "Out of domain question must return exactly [not found]")
        self.assertEqual(res["sources"], [], "Sources must be empty for [not found]")

    def test_conversational_followup_dialogue(self):
        """Verify conversational multi-turn follow-up resolution using conversation memory."""
        cm = ConversationManager()

        # Turn 1: Initial query
        q1 = "What is the minimum eGFR required for patient inclusion?"
        res1 = answer(q1, history=cm.get_history())
        cm.add_message("user", q1)
        cm.add_message("assistant", res1["answer"])
        self.assertIn("45", res1["answer"])
        self.assertIn("Page 14", res1["sources"])

        # Turn 2: Referential follow-up
        q2 = "What happens if the patient fails this criterion?"
        res2 = answer(q2, history=cm.get_history())
        cm.add_message("user", q2)
        cm.add_message("assistant", res2["answer"])
        self.assertTrue("excluded" in res2["answer"].lower() or "45" in res2["answer"])
        self.assertIn("Page 14", res2["sources"])

    def test_vectorstore_persistence_no_reindexing(self):
        """Verify that persisted vector database is reloaded without generating embeddings again."""
        client, collection, reindexed = build_vectorstore(force_rebuild=False)
        self.assertGreater(collection.count(), 0, "Collection must contain indexed chunks")
        self.assertFalse(reindexed, "Persistent database should reload without reindexing")

    def test_empty_or_invalid_query(self):
        """Verify graceful handling of empty or blank queries."""
        res_empty = answer("")
        self.assertEqual(res_empty["answer"], "[not found]")
        self.assertEqual(res_empty["sources"], [])

        res_whitespace = answer("    ")
        self.assertEqual(res_whitespace["answer"], "[not found]")
        self.assertEqual(res_whitespace["sources"], [])


if __name__ == "__main__":
    unittest.main()
