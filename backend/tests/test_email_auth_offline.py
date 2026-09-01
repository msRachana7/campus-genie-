"""Offline unit checks. No emails, credentials or live database are used.

Route helpers are extracted with AST to avoid requiring web/DB dependencies.
This tests branch logic, not FastAPI routing or real PostgreSQL transactions.
"""
import ast
import hashlib
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auth_crypto import hash_password, check_password, new_token, token_hash


class HttpError(Exception):
    def __init__(self, status, detail, **kwargs):
        self.status_code = status
        self.detail = detail


def functions(path, names, env):
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    for node in nodes:
        node.decorator_list = []
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(module, str(path), "exec"), env)
    return env


class CryptoTests(unittest.TestCase):
    def test_password_round_trip(self):
        encoded = hash_password("A long sample password 42!")
        self.assertTrue(check_password("A long sample password 42!", encoded))
        self.assertFalse(check_password("a wrong sample password", encoded))

    def test_salted_hashes_differ(self):
        self.assertNotEqual(hash_password("same password"), hash_password("same password"))

    def test_unicode_and_long_passwords(self):
        value = "🌱campus-" * 25
        self.assertTrue(check_password(value, hash_password(value)))

    def test_hash_capacity(self):
        self.assertEqual(len(hash_password("sample password")), 76)

    def test_unregistered_or_broken_hash(self):
        for value in [None, "", "NOT_REGISTERED", "invalid", "scrypt$abc$xyz", "scrypt$a"]:
            with self.subTest(value=value):
                self.assertFalse(check_password("sample password", value))

    def test_link_tokens(self):
        raw, stored = new_token()
        self.assertEqual(len(raw), 43)
        self.assertEqual(len(stored), 64)
        self.assertEqual(stored, hashlib.sha256(raw.encode()).hexdigest())
        self.assertNotEqual(raw, stored)
        self.assertNotEqual(new_token()[0], raw)


class AuthBranchTests(unittest.TestCase):
    def setUp(self):
        self.env = functions(ROOT / "routes/auth.py",
            {"registration_target", "valid_pending", "public_user", "verify_email", "reset_password", "login"},
            {"HTTPException": HttpError, "token_hash": token_hash, "dict_row": object(),
             "IntegrityError": type("IntegrityError", (Exception,), {}),
             "DataError": type("DataError", (Exception,), {}), "throttle": Mock(),
             "hash_password": hash_password, "check_password": check_password})
        self.cur = Mock()
        self.cur.__enter__ = Mock(return_value=self.cur)
        self.cur.__exit__ = Mock(return_value=False)
        conn = Mock()
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=False)
        conn.cursor.return_value = self.cur
        self.env["get_connection"] = Mock(return_value=conn)
        self.user = {"user_id": "example-id", "usn": "1BM25AD999", "email": "test@bmsce.ac.in",
                     "password_hash": "NOT_REGISTERED", "auth_version": 0,
                     "student_id": "test@bmsce.ac.in", "email_verified_at": None}
        self.data = {"usn": "1BM25AD999", "email": "test@bmsce.ac.in"}

    def test_new_email_does_not_need_preloaded_record(self):
        self.cur.fetchall.return_value = []
        self.assertIsNone(self.env["registration_target"](self.cur, self.data))

    def test_matching_preloaded_identity(self):
        self.cur.fetchall.return_value = [self.user]
        self.assertEqual(self.env["registration_target"](self.cur, self.data), self.user)

    def test_usn_alone_cannot_claim_other_email(self):
        self.cur.fetchall.return_value = [{**self.user, "email": "different@bmsce.ac.in"}]
        with self.assertRaises(HttpError) as err:
            self.env["registration_target"](self.cur, self.data)
        self.assertEqual(err.exception.status_code, 409)

    def test_email_cannot_claim_different_usn(self):
        self.cur.fetchall.return_value = [{**self.user, "usn": "1BM25AD998"}]
        with self.assertRaises(HttpError):
            self.env["registration_target"](self.cur, self.data)

    def test_conflicting_multiple_rows(self):
        self.cur.fetchall.return_value = [self.user, self.user]
        with self.assertRaises(HttpError):
            self.env["registration_target"](self.cur, self.data)

    def test_pending_links_require_expected_purpose(self):
        self.cur.fetchone.return_value = {"kind": "reset"}
        with self.assertRaises(HttpError):
            self.env["valid_pending"](self.cur, "x" * 43, {"signup"})

    def test_missing_consumed_or_expired_token(self):
        self.cur.fetchone.return_value = None
        with self.assertRaises(HttpError):
            self.env["valid_pending"](self.cur, "x" * 43, {"signup"})
        query, params = self.cur.execute.call_args.args
        self.assertIn("expires_at>CURRENT_TIMESTAMP", query)
        self.assertIn("FOR UPDATE", query)
        self.assertEqual(params, (token_hash("x" * 43),))

    def test_login_response_contains_no_password(self):
        self.assertEqual(set(self.env["public_user"](self.user)), {"user_id", "student_id", "email", "usn"})

    def prepare_verify(self, existing):
        self.env["valid_pending"] = Mock(return_value={"kind": "signup", "email": self.data["email"], "payload": {**self.data, "password_hash": "hashed"}})
        self.env["registration_target"] = Mock(return_value=existing)
        self.env["create_student"] = Mock()

    def test_new_student_created_only_when_verifying(self):
        self.prepare_verify(None)
        self.env["verify_email"](SimpleNamespace(token="x" * 43), object())
        self.env["create_student"].assert_called_once()
        self.assertIn("DELETE FROM campus_auth_pending", self.cur.execute.call_args.args[0])

    def test_verification_never_overwrites_registered_password(self):
        self.prepare_verify({**self.user, "password_hash": "existing-hash"})
        with self.assertRaises(HttpError):
            self.env["verify_email"](SimpleNamespace(token="x" * 43), object())
        self.env["create_student"].assert_not_called()
        self.cur.execute.assert_not_called()

    def test_unverified_login_denied_after_password_check(self):
        self.env["account"] = Mock(return_value=self.user)
        self.env["check_password"] = Mock(return_value=True)
        with self.assertRaises(HttpError) as err:
            self.env["login"](SimpleNamespace(email=self.data["email"], password="sample"), object())
        self.assertEqual(err.exception.status_code, 403)

    def test_reset_rejects_stale_account_version(self):
        self.env["valid_pending"] = Mock(return_value={"email": self.data["email"], "payload": {"user_id": "example-id", "auth_version": 0}})
        self.env["account"] = Mock(return_value={**self.user, "auth_version": 1, "email_verified_at": True})
        with self.assertRaises(HttpError):
            self.env["reset_password"](SimpleNamespace(token="x" * 43, new_password="sample password"), object())
        self.cur.execute.assert_not_called()

    def test_successful_reset_revokes_old_sessions_and_consumes_links(self):
        self.env["valid_pending"] = Mock(return_value={"email": self.data["email"], "payload": {"user_id": "example-id", "auth_version": 0}})
        self.env["account"] = Mock(return_value={**self.user, "email_verified_at": True})
        self.env["reset_password"](SimpleNamespace(token="x" * 43, new_password="sample password"), object())
        self.assertIn("auth_version=auth_version+1", self.cur.execute.call_args_list[0].args[0])
        self.assertIn("DELETE FROM campus_auth_pending", self.cur.execute.call_args_list[1].args[0])


if __name__ == "__main__":
    unittest.main()
