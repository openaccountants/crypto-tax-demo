"""Tests for crypto tax demo."""

import unittest
from oa_client import OAClient
import crypto_check
import crypto_client


class CryptoTaxDemoTests(unittest.TestCase):
    def setUp(self):
        self.oa = OAClient(token=None)
        self.plan = self.oa.start("Classify crypto transaction history for tax", "US")
        slug = (self.plan.get("skills_to_load") or [None])[0]
        self.skill = self.oa.get_skill(slug)

    def test_mock_oa_client(self):
        self.assertEqual(self.plan["jurisdiction"], "US")
        self.assertEqual(self.skill["tier"], 1)
        self.assertIn("Amir Pelinkovic", self.skill["verifier"])

    def test_buy_non_taxable(self):
        ev = {
            "id": "tx_01",
            "type": "buy",
            "date": "2024-12-01",
            "asset": "ETH",
            "amount": 2.0,
            "cost_basis_usd": 4000.0,
            "proceeds_usd": 4000.0,
            "acquire_date": "2024-12-01",
            "is_disposal": False,
        }
        res = crypto_check.check(ev, self.skill)
        self.assertEqual(res["status"], "info")
        self.assertIn("Acquisition", res["headline"])

    def test_swap_taxable_disposal(self):
        ev = {
            "id": "tx_02",
            "type": "swap",
            "date": "2025-03-01",
            "asset": "ETH",
            "amount": 2.0,
            "received": "SOL",
            "cost_basis_usd": 4000.0,
            "proceeds_usd": 4800.0,
            "acquire_date": "2024-12-01",
            "is_disposal": True,
        }
        res = crypto_check.check(ev, self.skill)
        self.assertEqual(res["status"], "warn")
        self.assertIn("taxable disposal", res["headline"])
        self.assertIn("short-term", res["headline"])

    def test_staking_reward_income(self):
        ev = {
            "id": "tx_04",
            "type": "reward",
            "date": "2025-02-01",
            "asset": "SOL",
            "amount": 1.0,
            "cost_basis_usd": 0.0,
            "proceeds_usd": 150.0,
            "acquire_date": "2025-02-01",
            "is_disposal": False,
        }
        res = crypto_check.check(ev, self.skill)
        self.assertEqual(res["status"], "warn")
        self.assertIn("ordinary income", res["headline"])

    def test_sell_long_term_gain(self):
        ev = {
            "id": "tx_05",
            "type": "sell",
            "date": "2025-05-01",
            "asset": "BTC",
            "amount": 0.1,
            "cost_basis_usd": 4000.0,
            "proceeds_usd": 9500.0,
            "acquire_date": "2021-06-01",
            "is_disposal": True,
        }
        res = crypto_check.check(ev, self.skill)
        self.assertEqual(res["status"], "ok")
        self.assertIn("long-term gain", res["headline"])

    def test_samples_extraction(self):
        txns = crypto_client.extract("samples/transactions.json")
        self.assertEqual(len(txns), 5)
        norm = crypto_client.normalize(txns[0])
        self.assertEqual(norm["asset"], "ETH")


if __name__ == "__main__":
    unittest.main()
