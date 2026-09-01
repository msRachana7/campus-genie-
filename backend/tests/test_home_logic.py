"""Offline unit tests: no credentials, network, database, or third-party packages."""
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from home_logic import (IST, SourceUnavailable, active, archive_item, content_key,
                        event_moment, matches, next_item, parse_moment, period,
                        post_payload, table_name, text_list, weekly_pulse)

NOW = datetime(2026, 9, 1, 16, 24, tzinfo=IST)


def row(identifier="1", **values):
    return {"content_id": identifier, "content_source": "event", "title": "AI meetup", **values}


class HomeLogicTests(unittest.TestCase):
    def test_india_timezone_can_cross_midnight(self):
        moment, precise = parse_moment("2026-08-31T23:45:00Z")
        self.assertEqual(moment.isoformat(), "2026-09-01T05:15:00+05:30")
        self.assertTrue(precise)

    def test_sql_epoch_preserves_instant(self):
        moment, precise = parse_moment(str(NOW.timestamp()))
        self.assertEqual(moment, NOW)
        self.assertTrue(precise)

    def test_date_only_is_not_fabricated_time(self):
        self.assertFalse(parse_moment("2026-09-01")[1])
        self.assertIsNone(parse_moment("bad date")[0])

    def test_period_boundaries(self):
        self.assertEqual([period(hour) for hour in [0, 5, 11, 12, 17, 21]],
                         ["night", "morning", "morning", "afternoon", "evening", "night"])

    def test_meta_event_date_and_time(self):
        moment, precise = event_moment(row(meta='{"event_date":"2026-09-02","start_time":"16:30"}'))
        self.assertEqual(moment.hour, 16)
        self.assertTrue(precise)

    def test_same_day_past_event_is_skipped(self):
        past = row("past", event_date="2026-09-01T09:00:00+05:30")
        future = row("future", event_date="2026-09-01T18:00:00+05:30")
        self.assertEqual(next_item([past, future], NOW)["id"], content_key(future))
        self.assertFalse(active(past, NOW))

    def test_event_date_wins_over_registration_deadline(self):
        event = row(event_date="2026-09-05", deadline="2026-08-30")
        result = next_item([event], NOW)
        self.assertEqual(result["date"], "2026-09-05")
        self.assertEqual(result["kind"], "event")
        self.assertEqual(result["time"], "Time not listed")

    def test_deadline_never_presented_as_event_start(self):
        result = next_item([row(deadline="2026-09-03")], NOW)
        self.assertEqual(result["kind"], "deadline")
        self.assertIsNone(next_item([], NOW))

    def test_teammate_post_is_not_an_event(self):
        item = row(content_source="research", type="research", title="AI hackathon teammates", event_date="2026-09-05", deadline="2026-09-04")
        self.assertEqual(next_item([item], NOW)["kind"], "deadline")
        self.assertFalse(weekly_pulse([item], NOW, False)["has_event_dates"])

    def test_week_boundaries_monday_to_sunday(self):
        data = [row("a", event_date="2026-08-30"), row("b", event_date="2026-08-31"),
                row("c", event_date="2026-09-06"), row("d", event_date="2026-09-07")]
        result = weekly_pulse(data, NOW, False)
        self.assertEqual(result["week_start"], "2026-08-31")
        self.assertEqual(result["week_end"], "2026-09-06")
        self.assertEqual(result["ai_event_count"], 2)
        self.assertEqual(result["previous_ai_event_count"], 1)
        self.assertEqual(result["ai_days"], [1, 0, 0, 0, 0, 0, 1])

    def test_ai_word_boundaries(self):
        result = weekly_pulse([row(title="Chair design", event_date="2026-09-02")], NOW, False)
        self.assertEqual(result["ai_event_count"], 0)

    def test_partial_data_has_qualified_counts(self):
        result = weekly_pulse([row(event_date="2026-09-02")], NOW, True)
        self.assertIn("loaded records", result["detail"])
        self.assertNotIn("up this week", result["headline"])

    def test_missing_dates_produce_no_trend_claim(self):
        result = weekly_pulse([row(deadline="2026-09-02")], NOW, False)
        self.assertFalse(result["has_event_dates"])
        self.assertIn("dates are not available", result["detail"])

    def test_preferences_and_json_arrays(self):
        self.assertEqual(text_list('["Python","Python","SQL"]'), ["Python", "SQL"])
        self.assertTrue(matches(row(title="Python research"), {"skills": '["python"]'}))
        self.assertFalse(matches(row(title="JavaScript group"), {"skills": ["Java"]}))
        self.assertTrue(matches(row(title="Machine learning meetup"), {"interests": ["AI & Data"]}))

    def test_stable_ids_survive_sorting_and_distinguish_sources(self):
        first = row("shared", content_source="event")
        second = row("shared", content_source="research")
        self.assertNotEqual(content_key(first), content_key(second))
        self.assertEqual(content_key(first), content_key(dict(reversed(list(first.items())))))

    def test_public_payload_omits_private_identity(self):
        item = row(author_id="student@example.edu", deadline=None)
        authors = {"student@example.edu": {"name": "Test Student", "student_id": "student@example.edu", "user_id": "private-id", "department": "AI & DS"}}
        payload = post_payload(item, authors, {content_key(item)}, {})
        self.assertTrue(payload["interested"])
        self.assertEqual(payload["name"], "Test Student")
        self.assertNotIn("student@example.edu", str(payload))
        self.assertNotIn("private-id", str(payload))
        self.assertIsNone(payload["deadline"])

    def test_archive_requires_a_past_date(self):
        self.assertIsNone(archive_item([row(event_date="2026-09-03")], NOW))
        self.assertEqual(archive_item([row(event_date="2025-09-03")], NOW)["year"], 2025)

    def test_table_identifier_validation(self):
        with patch.dict(os.environ, {"HOME_TEST_TABLE": "campus_genie.silver.campus_content"}):
            self.assertEqual(table_name("HOME_TEST_TABLE"), "`campus_genie`.`silver`.`campus_content`")
        with patch.dict(os.environ, {"HOME_TEST_TABLE": "x.y.z; DROP TABLE student_private"}):
            with self.assertRaises(SourceUnavailable):
                table_name("HOME_TEST_TABLE")


if __name__ == "__main__":
    unittest.main()
