"""Basic smoke tests for route planning and crowding outputs."""
import os
import unittest
from app import app

class PlannerTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_homepage(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Delhi Bus Crowdedness-Aware Journey Planner", resp.data)

    def test_stops_list(self):
        resp = self.client.get("/api/stops")
        self.assertEqual(resp.status_code, 200)
        stops = resp.get_json()
        self.assertTrue(len(stops) > 50)
        self.assertIn("Anand Vihar ISBT", stops)
        self.assertIn("Connaught Place", stops)

    def test_options_anand_vihar_cp(self):
        resp = self.client.get("/api/options?from=Anand+Vihar+ISBT&to=Connaught+Place&depart=18:00&day=weekday")
        self.assertEqual(resp.status_code, 200)
        options = resp.get_json()
        self.assertTrue(len(options) > 0)
        fastest = options[0]
        self.assertIn("level_label", fastest)
        self.assertIn("worst_stretch", fastest)

if __name__ == "__main__":
    unittest.main()
