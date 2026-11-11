"""Regression tests for archive filtering in the Pioneer all-lot updater.

These tests use saved fixtures/mocks; no HiBid requests or auction actions occur.
"""
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import update_all_lot_bids as updater


NOW = datetime(2026, 11, 11, 3, 0, tzinfo=timezone.utc)


def final_archive():
    return {
        "checkedAt": "2026-10-08T10:59:16Z",
        "auction": {
            "id": "781007",
            "bidCloseDateTime": "2026-10-07T19:00:00",
            "auctionStatus": "ARCHIVED",
            "openLotCount": 0,
        },
        "summary": {
            "trackedLots": 580,
            "closedLots": 580,
            "activeLots": 0,
        },
        "lots": [{"hibidLotId": "1", "isClosed": True}],
    }


class SavedArchiveTests(unittest.TestCase):
    def test_original_failed_auction_is_final(self):
        self.assertTrue(updater.saved_archived_auction_is_final(final_archive(), NOW))

    def test_reopening_or_active_lots_still_require_online_check(self):
        for key, value in (("activeLots", 1), ("closedLots", 579)):
            with self.subTest(field=key):
                snapshot = final_archive()
                snapshot["summary"][key] = value
                self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))

    def test_non_archived_and_nonzero_remote_open_count_still_check(self):
        for field, value in (("auctionStatus", "OPEN"), ("openLotCount", 1)):
            with self.subTest(field=field):
                snapshot = final_archive()
                snapshot["auction"][field] = value
                self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))

    def test_recent_closure_still_checks_during_grace_period(self):
        snapshot = final_archive()
        snapshot["auction"]["bidCloseDateTime"] = "2026-11-10T19:00:00"
        self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))
        self.assertTrue(
            updater.saved_archived_auction_is_final(snapshot, NOW + timedelta(hours=18))
        )

    def test_missing_or_incomplete_metadata_never_skips(self):
        for snapshot in ({}, {"auction": {}}, {"auction": {"auctionStatus": "ARCHIVED"}, "summary": {}}):
            with self.subTest(snapshot=snapshot):
                self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))
        snapshot = final_archive()
        del snapshot["summary"]["trackedLots"]
        self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))

    def test_incorrect_zero_lot_snapshot_does_not_skip(self):
        snapshot = final_archive()
        snapshot["summary"].update(trackedLots=0, closedLots=0)
        self.assertFalse(updater.saved_archived_auction_is_final(snapshot, NOW))

    def test_final_archive_runs_without_any_hibid_connection_or_rewrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "auctions"
            auction_dir = root / "781007"
            auction_dir.mkdir(parents=True)
            (auction_dir / "lots.json").write_text("[]", encoding="utf-8")
            live_path = auction_dir / "live.json"
            original = json.dumps(final_archive())
            live_path.write_text(original, encoding="utf-8")
            with (
                patch.object(updater, "AUCTIONS_DIR", root),
                patch.object(updater, "WATCHLIST_SOURCE", Path(directory) / "watchlists/latest.json"),
                patch.object(updater, "WATCHLIST_LIVE", Path(directory) / "watchlists/live.json"),
                patch.object(updater, "now_utc_dt", return_value=NOW),
                patch.object(updater.requests, "Session", side_effect=AssertionError("unexpected HiBid call")),
            ):
                self.assertEqual(updater.main(), 0)
            self.assertEqual(live_path.read_text(encoding="utf-8"), original)
            self.assertFalse((Path(directory) / "watchlists/live.json").exists())


if __name__ == "__main__":
    unittest.main()
