"""仅测试业务路由规则，网络调用需使用 --live 单独验证。"""

import unittest

from triage import assess


def answer(team="billing", confidence=0.95, human=0.05, impact=None):
    impact = impact or {"0": 0.0, "1": 0.95, "2": 0.05}
    probabilities = {"technical": 0.01, "billing": 0.95, "sales": 0.02, "other": 0.02}
    if team == "technical":
        probabilities = {"technical": 0.95, "billing": 0.01, "sales": 0.02, "other": 0.02}
    return {"model": "test-fixture", "answers": {
        "department": {"type": "choice", "choice": team, "confidence": confidence,
                       "probabilities": probabilities},
        "impact": {"type": "score", "confidence": 0.9, "probabilities": impact},
        "wants_human": {"type": "noul", "noul": human},
    }}


class PolicyTests(unittest.TestCase):
    def test_high_confidence_routes_but_never_refunds(self):
        self.assertEqual(assess(answer())["route"], "billing")

    def test_explicit_human_request(self):
        self.assertEqual(assess(answer(human=0.95))["route"], "human")

    def test_ambiguous_or_low_confidence_escalates(self):
        self.assertEqual(assess(answer(human=0.45))["route"], "review")
        self.assertEqual(assess(answer(confidence=0.5))["route"], "review")

    def test_critical_impact_priority(self):
        result = assess(answer(team="technical", impact={"0": 0.01, "1": 0.09, "2": 0.9}))
        self.assertEqual((result["route"], result["priority"]), ("technical", "high"))

    def test_invalid_response_fails_closed(self):
        self.assertEqual(assess({"answers": {}})["route"], "review")
        bad = answer()
        bad["answers"]["wants_human"]["noul"] = float("nan")
        self.assertEqual(assess(bad)["route"], "review")


if __name__ == "__main__":
    unittest.main()