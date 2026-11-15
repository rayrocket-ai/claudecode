#!/usr/bin/env python3
"""Unit tests for hl_build.py. Standard library only. No network.

A fake HTTP layer is injected into the tool. It keeps an in-memory
sub-account and records every call it receives.

Run:  python3 -m unittest -v test_hl_build   (from this folder)
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hl_build  # noqa: E402

def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


TOKEN = "pit-TESTSECRET-0000-not-a-real-token"
LOC = "demoLocation123"
RAY = "rayHomesLive999"
NAME = "NL Demo"


class FakeHL:
    """In-memory stand-in for the HighLevel API."""

    def __init__(self, name=NAME, location_id=LOC):
        self.name = name
        self.location_id = location_id
        self.calls = []
        self.deny = {}            # path prefix -> (status, message)
        self.rate_limit_once = set()
        self.workflow_api = True
        self.echo_auth_in_errors = False
        self.counter = 0
        self.custom_values = []
        self.custom_fields = []
        self.tags = []
        self.pipelines = []
        self.calendars = []
        self.agents = []

    # -- helpers
    def _id(self, prefix):
        self.counter += 1
        return "%s_%04d" % (prefix, self.counter)

    def writes(self):
        return [c for c in self.calls if c["method"] != "GET" and c["path"] != "/workflows/search"]

    def _reply(self, status, payload, headers=None):
        return status, headers or {}, json.dumps(payload).encode("utf-8")

    # -- the transport signature the tool expects
    def __call__(self, method, url, headers, body, timeout):
        parsed = urllib.parse.urlsplit(url)
        path = parsed.path
        query = dict(urllib.parse.parse_qsl(parsed.query))
        payload = json.loads(body.decode("utf-8")) if body else None
        self.calls.append({"method": method, "path": path, "query": query, "body": payload, "headers": dict(headers)})
        if method not in ("GET", "POST"):
            raise AssertionError("the tool sent a %s request" % method)
        if parsed.netloc != "services.leadconnectorhq.com" or parsed.scheme != "https":
            raise AssertionError("unexpected host %s" % url)
        if headers.get("Authorization") != "Bearer " + TOKEN or not headers.get("Version"):
            return self._reply(401, {"message": "Invalid JWT"})
        if path in self.rate_limit_once:
            self.rate_limit_once.discard(path)
            return self._reply(429, {"message": "Too many requests"}, {"Retry-After": "1"})
        for prefix, (status, message) in self.deny.items():
            if path.startswith(prefix):
                if self.echo_auth_in_errors:
                    message = "%s (request had Authorization: %s)" % (message, headers.get("Authorization"))
                return self._reply(status, {"statusCode": status, "message": message})
        loc = self.location_id
        base = "/locations/" + loc
        if method == "GET":
            if path == base:
                return self._reply(200, {"location": {"id": loc, "name": self.name, "timezone": "America/Toronto"}})
            if path == base + "/customValues":
                return self._reply(200, {"customValues": self.custom_values})
            if path == base + "/customFields":
                return self._reply(200, {"customFields": self.custom_fields})
            if path == base + "/tags":
                return self._reply(200, {"tags": self.tags})
            if path == "/opportunities/pipelines":
                return self._reply(200, {"pipelines": self.pipelines})
            if path == "/calendars":
                return self._reply(200, {"calendars": self.calendars})
            if path == "/voice-ai/agents":
                return self._reply(200, {"total": len(self.agents), "page": 1, "pageSize": 50, "agents": self.agents})
            if path == "/forms":
                return self._reply(200, {"forms": [], "total": 0})
            return self._reply(404, {"message": "Not found"})
        # POST
        if path == "/workflows/search":
            if not self.workflow_api:
                return self._reply(403, {"statusCode": 403, "message": "WORKFLOW_API_NOT_ENABLED_FOR_LOCATION"})
            return self._reply(200, {"total": 0, "count": 0, "workflows": []})
        if path == base + "/customValues":
            item = {"id": self._id("cv"), "name": payload["name"], "value": payload["value"], "locationId": loc}
            self.custom_values.append(item)
            return self._reply(201, {"customValue": item})
        if path == base + "/customFields":
            item = {"id": self._id("cf"), "name": payload["name"], "dataType": payload["dataType"], "model": payload.get("model")}
            self.custom_fields.append(item)
            return self._reply(201, {"customField": item})
        if path == base + "/tags":
            if any(t["name"] == payload["name"].strip().lower() for t in self.tags):
                return self._reply(400, {"message": "Tag already exists"})
            item = {"id": self._id("tag"), "name": payload["name"].strip().lower(), "locationId": loc}
            self.tags.append(item)
            return self._reply(201, {"tag": item})
        if path == "/opportunities/pipelines":
            stages = [dict(s, id=self._id("stage")) for s in payload["stages"]]
            item = {"id": self._id("pipe"), "name": payload["name"], "stages": stages, "locationId": loc}
            self.pipelines.append(item)
            return self._reply(200, item)
        if path == "/calendars":
            item = dict(payload, id=self._id("cal"))
            self.calendars.append(item)
            return self._reply(200, {"calendar": item})
        if path == "/voice-ai/agents":
            item = dict(payload, id=self._id("agent"), actions=[])
            self.agents.append(item)
            return self._reply(201, item)
        if path == "/voice-ai/actions":
            item = {"id": self._id("action"), "actionType": payload["actionType"], "name": payload["name"],
                    "actionParameters": payload["actionParameters"]}
            for agent in self.agents:
                if agent["id"] == payload["agentId"]:
                    agent["actions"].append(item)
            return self._reply(201, item)
        return self._reply(404, {"message": "Not found"})


class Base(unittest.TestCase):
    def setUp(self):
        self.fake = FakeHL()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_dir = os.path.join(self.tmp.name, "state")
        self.env = {
            "HIGHLEVEL_NL_DEMO_API_TOKEN": TOKEN,
            "HIGHLEVEL_NL_DEMO_LOCATION_ID": LOC,
            "HIGHLEVEL_LOCATION_ID": RAY,
            "HIGHLEVEL_API_TOKEN": "pit-RAYHOMES-live-token",
        }
        self.sleeps = []

    def run_tool(self, *argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        args = list(argv) + ["--state-dir", self.state_dir]
        code = hl_build.main(args, env=self.env if env is None else env, transport=self.fake,
                             sleep=self.sleeps.append, out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def config(self):
        return hl_build.load_config(hl_build.DEFAULT_CONFIG)

    def creatable_count(self):
        c = self.config()
        count = sum(len(c[k]) for k in ("custom_values", "custom_fields", "tags", "pipelines", "calendars", "voice_agents"))
        count += sum(1 for a in c["voice_agents"] for x in a["actions"] if x.get("create_via_api"))
        return count

    def state_files(self):
        return os.listdir(self.state_dir) if os.path.isdir(self.state_dir) else []


class TokenSecrecy(Base):
    def test_token_never_appears_in_any_output(self):
        outputs = []
        for argv in (["preflight"], ["plan"], ["apply"], ["verify"], ["plan", "--json"],
                     ["apply", "--write", "--confirm-location-name", "wrong"],
                     ["apply", "--write", "--confirm-location-name", NAME],
                     ["apply", "--write", "--confirm-location-name", NAME, "--json"],
                     ["verify", "--json"], ["preflight", "--json"]):
            code, out, err = self.run_tool(*argv)
            outputs.append(out + err)
        self.assertTrue(self.fake.writes(), "the write run should have created items")
        for text in outputs:
            self.assertNotIn(TOKEN, text)
            self.assertNotIn("Bearer " + TOKEN[:8], text)

    def test_authorization_is_redacted_when_the_server_echoes_it(self):
        self.fake.echo_auth_in_errors = True
        self.fake.deny["/locations/%s/tags" % LOC] = (401, "The token does not have access to this scope")
        for argv in (["preflight"], ["plan"], ["plan", "--json"], ["apply", "--write", "--confirm-location-name", NAME]):
            code, out, err = self.run_tool(*argv)
            self.assertNotIn(TOKEN, out + err)
            self.assertNotEqual(code, 0)
        code, out, err = self.run_tool("plan")
        self.assertIn("[REDACTED]", err)

    def test_token_redacted_in_network_errors(self):
        def broken(method, url, headers, body, timeout):
            raise OSError("connection reset while sending %r" % (headers,))
        out, err = io.StringIO(), io.StringIO()
        code = hl_build.main(["plan", "--state-dir", self.state_dir], env=self.env, transport=broken,
                             sleep=lambda s: None, out=out, err=err)
        self.assertEqual(code, hl_build.EXIT_API)
        self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())

    def test_missing_token_is_a_config_error_without_any_call(self):
        env = dict(self.env)
        del env["HIGHLEVEL_NL_DEMO_API_TOKEN"]
        code, out, err = self.run_tool("plan", env=env)
        self.assertEqual(code, hl_build.EXIT_CONFIG)
        self.assertEqual(self.fake.calls, [])

    def test_token_is_sent_only_in_the_header(self):
        self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        for call in self.fake.calls:
            self.assertEqual(call["headers"]["Authorization"], "Bearer " + TOKEN)
            self.assertEqual(call["headers"]["Version"], "v3")
            self.assertNotIn(TOKEN, json.dumps(call["body"]) + json.dumps(call["query"]) + call["path"])


class ProtectedLocation(Base):
    def test_ray_homes_location_is_refused_for_every_subcommand(self):
        self.fake = FakeHL(name="Ray Homes", location_id=RAY)
        for argv in (["preflight"], ["plan"], ["verify"], ["apply"],
                     ["apply", "--write", "--confirm-location-name", "Ray Homes"]):
            code, out, err = self.run_tool(*(argv + ["--location", RAY]))
            self.assertEqual(code, hl_build.EXIT_PROTECTED, argv)
            self.assertIn("Refused", err)
        self.assertEqual(self.fake.calls, [], "no request may be sent for the protected location")
        self.assertEqual(self.state_files(), [])

    def test_refused_when_the_location_env_points_at_it(self):
        env = dict(self.env, HIGHLEVEL_NL_DEMO_LOCATION_ID=RAY)
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME, env=env)
        self.assertEqual(code, hl_build.EXIT_PROTECTED)
        self.assertEqual(self.fake.calls, [])

    def test_there_is_no_override_flag(self):
        help_text = hl_build.build_parser().format_help()
        for sub in ("preflight", "plan", "apply", "verify"):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                hl_build.build_parser().parse_args([sub, "--i-know-this-is-not-ray-homes"])
        self.assertNotIn("--force", help_text)

    def test_ray_homes_token_is_refused(self):
        code, out, err = self.run_tool("plan", "--token-env", "HIGHLEVEL_API_TOKEN")
        self.assertEqual(code, hl_build.EXIT_PROTECTED)
        env = dict(self.env, HIGHLEVEL_NL_DEMO_API_TOKEN=self.env["HIGHLEVEL_API_TOKEN"])
        code, out, err = self.run_tool("plan", env=env)
        self.assertEqual(code, hl_build.EXIT_PROTECTED)
        self.assertEqual(self.fake.calls, [])


class DryByDefault(Base):
    def test_apply_without_write_changes_nothing(self):
        code, out, err = self.run_tool("apply")
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("WOULD CREATE", out)
        self.assertEqual(self.fake.writes(), [])
        self.assertEqual(self.state_files(), [])

    def test_apply_without_write_ignores_a_correct_confirmation(self):
        code, out, err = self.run_tool("apply", "--confirm-location-name", NAME)
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.writes(), [])

    def test_plan_preflight_verify_send_no_writes(self):
        for argv in (["plan"], ["preflight"], ["verify"]):
            self.run_tool(*argv)
        self.assertEqual(self.fake.writes(), [])
        self.assertEqual(self.state_files(), [])
        self.assertEqual({c["method"] for c in self.fake.calls if c["path"] != "/workflows/search"}, {"GET"})

    def test_client_refuses_a_create_in_a_dry_run(self):
        client = hl_build.Client(TOKEN, "v3", transport=self.fake, sleep=lambda s: None)
        with self.assertRaises(hl_build.ToolError):
            client.request("POST", "/locations/%s/tags" % LOC, body={"name": "x"})
        self.assertEqual(self.fake.calls, [])

    def test_client_refuses_anything_off_the_allowlist(self):
        client = hl_build.Client(TOKEN, "v3", transport=self.fake, sleep=lambda s: None, allow_write=True)
        for method, path in (("PUT", "/workflows/abc/status"), ("POST", "/contacts/"), ("PATCH", "/voice-ai/agents/a1"),
                             ("POST", "/workflows/"), ("POST", "/locations/%s/tags/extra" % LOC)):
            with self.assertRaises(hl_build.ToolError):
                client.request(method, path, body={})
        self.assertEqual(self.fake.calls, [])


class ConfirmName(Base):
    def test_write_with_wrong_name_changes_nothing(self):
        for wrong in ("NL demo", "NL Demo ", "Next Level", ""):
            code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", wrong)
            self.assertEqual(code, hl_build.EXIT_CONFIRM, repr(wrong))
            self.assertIn("Nothing was changed", err)
        self.assertEqual(self.fake.writes(), [])
        self.assertEqual(self.state_files(), [])

    def test_write_without_the_flag_changes_nothing(self):
        code, out, err = self.run_tool("apply", "--write")
        self.assertEqual(code, hl_build.EXIT_CONFIRM)
        self.assertEqual(self.fake.writes(), [])

    def test_write_with_exact_name_creates_everything_once(self):
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.fake.writes()), self.creatable_count())
        self.assertEqual(len(self.fake.agents), 1)
        agent = self.fake.agents[0]
        self.assertIn("an AI assistant", agent["welcomeMessage"])
        self.assertLessEqual(len(agent["welcomeMessage"]), 190)
        self.assertEqual(agent["language"], "en-US")
        self.assertIn("## Never", agent["agentPrompt"])
        self.assertNotIn("inboundNumber", agent)
        self.assertFalse(self.fake.calendars[0]["isActive"])
        for line in [l for l in out.splitlines() if l.startswith("created ")]:
            self.assertRegex(line, r"id=\w+_\d{4}")
        code, out, err = self.run_tool("verify")
        self.assertEqual(code, 0, out)


class Idempotent(Base):
    def test_second_apply_creates_nothing(self):
        self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        first = len(self.fake.writes())
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fake.writes()), first)
        self.assertIn("Created 0 item(s)", out)

    def test_existing_items_are_not_recreated_or_changed(self):
        self.fake.tags.append({"id": "tag_old", "name": "nl-urgent"})
        self.fake.custom_values.append({"id": "cv_old", "name": "NL_Biz_Name", "value": "Client's real value"})
        self.fake.pipelines.append({"id": "pipe_old", "name": "nl | client pipeline (AGENT edition)",
                                    "stages": [{"id": "s1", "name": "Only stage", "position": 1}]})
        self.fake.agents.append({"id": "agent_old", "agentName": "NL Receptionist (agent edition)", "actions": []})
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        self.assertEqual(code, 0, err)
        created_names = [(c["path"], (c["body"] or {}).get("name") or (c["body"] or {}).get("agentName")) for c in self.fake.writes()]
        self.assertNotIn("nl-urgent", [n for _, n in created_names])
        self.assertNotIn("nl_biz_name", [n for _, n in created_names])
        self.assertFalse([p for p, _ in created_names if p in ("/opportunities/pipelines", "/voice-ai/agents", "/voice-ai/actions")])
        self.assertEqual(self.fake.custom_values[0]["value"], "Client's real value")
        self.assertEqual(len(self.fake.pipelines), 1)
        self.assertEqual(len(self.fake.agents), 1)
        self.assertEqual(len(self.fake.writes()), self.creatable_count() - 4)
        self.assertIn("stages differ", out)

    def test_actions_are_only_added_to_an_agent_this_tool_created(self):
        config = self.config()
        config["voice_agents"][0]["actions"] = [{
            "name": "NL | Test transfer", "actionType": "CALL_TRANSFER", "create_via_api": True,
            "actionParameters": {"triggerPrompt": "never", "transferToType": "number", "transferToValue": "placeholder",
                                 "triggerMessage": "one moment", "_verify": "note"}}]
        path = os.path.join(self.tmp.name, "config.json")
        with open(path, "w") as handle:
            json.dump(config, handle)
        self.fake.agents.append({"id": "agent_old", "agentName": "NL Receptionist (agent edition)", "actions": []})
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME, "--config", path)
        self.assertEqual(code, 0, err)
        self.assertFalse([c for c in self.fake.writes() if c["path"] == "/voice-ai/actions"])
        self.fake.agents.clear()
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME, "--config", path)
        actions = [c for c in self.fake.writes() if c["path"] == "/voice-ai/actions"]
        self.assertEqual(len(actions), 1)
        self.assertNotIn("_verify", actions[0]["body"]["actionParameters"])
        self.assertEqual(actions[0]["body"]["agentId"], self.fake.agents[0]["id"])

    def test_a_config_without_a_voice_agent_never_touches_voice_endpoints(self):
        config = self.config()
        config["voice_agents"] = []
        path = os.path.join(self.tmp.name, "sales.json")
        with open(path, "w") as handle:
            json.dump(config, handle)
        self.fake.deny["/voice-ai"] = (401, "no scope")
        for argv in (["preflight"], ["plan"], ["apply", "--write", "--confirm-location-name", NAME], ["verify"]):
            code, out, err = self.run_tool(*(argv + ["--config", path]))
            self.assertEqual(code, 0, err)
        self.assertFalse([c for c in self.fake.calls if c["path"].startswith("/voice-ai") and c["method"] == "POST"])

    def test_verify_reports_missing(self):
        code, out, err = self.run_tool("verify")
        self.assertEqual(code, hl_build.EXIT_VERIFY)
        self.assertIn("MISSING", out)


class Preflight(Base):
    def test_a_401_on_one_scope_is_reported_and_the_others_still_run(self):
        self.fake.deny["/locations/%s/tags" % LOC] = (401, "The token does not have access to this scope")
        code, out, err = self.run_tool("preflight", "--json")
        report = json.loads(out)
        self.assertEqual(code, hl_build.EXIT_PREFLIGHT)
        by_scope = {r["scope"]: r for r in report["scopes"]}
        self.assertFalse(by_scope["locations/tags.readonly"]["allowed"])
        self.assertEqual(by_scope["locations/tags.readonly"]["status"], 401)
        others = [r for s, r in by_scope.items() if s != "locations/tags.readonly"]
        self.assertEqual(len(others), 8)
        self.assertTrue(all(r["allowed"] for r in others))
        self.assertEqual(report["location"]["name"], NAME)
        self.assertEqual(report["workflow_api"], "enabled")
        self.assertEqual(len(self.fake.calls), 9)

    def test_human_output_shows_name_and_not_allowed(self):
        self.fake.deny["/calendars"] = (401, "no scope")
        code, out, err = self.run_tool("preflight")
        self.assertEqual(code, hl_build.EXIT_PREFLIGHT)
        self.assertIn("Location name: " + NAME, out)
        self.assertRegex(out, r"calendars\.readonly\s+required\s+NOT ALLOWED\s+401")
        self.assertRegex(out, r"locations/tags\.readonly\s+required\s+allowed")

    def test_workflow_api_not_enabled_is_reported_and_is_not_a_failure(self):
        self.fake.workflow_api = False
        code, out, err = self.run_tool("preflight")
        self.assertEqual(code, 0)
        self.assertIn("Workflow API for this location: not enabled", out)

    def test_all_allowed(self):
        code, out, err = self.run_tool("preflight")
        self.assertEqual(code, 0)
        self.assertIn("Workflow API for this location: enabled", out)
        self.assertIn("guard: active", out)


class StopsAndRetries(Base):
    def test_stops_on_a_4xx_during_apply_and_keeps_state(self):
        original = self.fake.__call__

        def transport(method, url, headers, body, timeout):
            if method == "POST" and url.endswith("/opportunities/pipelines"):
                self.fake.calls.append({"method": method, "path": "/opportunities/pipelines", "query": {}, "body": None, "headers": dict(headers)})
                return 422, {}, json.dumps({"message": ["stages.0.position must be unique"]}).encode()
            return original(method, url, headers, body, timeout)

        out, err = io.StringIO(), io.StringIO()
        code = hl_build.main(["apply", "--write", "--confirm-location-name", NAME, "--state-dir", self.state_dir],
                             env=self.env, transport=transport, sleep=self.sleeps.append, out=out, err=err)
        self.assertEqual(code, hl_build.EXIT_API)
        self.assertIn("422", err.getvalue())
        self.assertIn("position must be unique", err.getvalue())
        self.assertEqual(self.fake.calendars, [], "nothing after the failing call may be created")
        self.assertEqual(self.fake.agents, [])
        state = json.loads(read(os.path.join(self.state_dir, LOC + ".json")))
        self.assertEqual(len(state["created"]), len(self.fake.custom_values) + len(self.fake.custom_fields) + len(self.fake.tags))

    def test_429_is_retried_once_with_backoff(self):
        self.fake.rate_limit_once.add("/calendars")
        code, out, err = self.run_tool("plan")
        self.assertEqual(code, 0, err)
        self.assertEqual(len([c for c in self.fake.calls if c["path"] == "/calendars"]), 2)
        self.assertIn(1.0, self.sleeps)

    def test_second_429_stops(self):
        self.fake.deny["/calendars"] = (429, "Too many requests")
        code, out, err = self.run_tool("plan")
        self.assertEqual(code, hl_build.EXIT_API)
        self.assertEqual(len([c for c in self.fake.calls if c["path"] == "/calendars"]), 2)

    def test_pauses_between_calls(self):
        self.run_tool("plan")
        self.assertEqual(len(self.sleeps), len(self.fake.calls) - 1)
        self.assertTrue(all(s == 0.35 for s in self.sleeps))


class StateFile(Base):
    def test_state_file_has_ids_and_no_token(self):
        self.fake.echo_auth_in_errors = True
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state_files(), [LOC + ".json"])
        text = read(os.path.join(self.state_dir, LOC + ".json"))
        self.assertNotIn(TOKEN, text)
        self.assertNotIn("Bearer", text)
        self.assertNotIn("Authorization", text)
        self.assertNotIn("pit-", text)
        state = json.loads(text)
        self.assertEqual(state["locationId"], LOC)
        self.assertEqual(len(state["created"]), self.creatable_count())
        self.assertTrue(all(c["id"] for c in state["created"]))
        self.assertEqual(set(state), {"locationId", "locationName", "created", "updatedAt"})
        for record in state["created"]:
            self.assertLessEqual(set(record), {"kind", "name", "id", "createdAt", "parent"})

    def test_json_apply_lists_created_ids(self):
        code, out, err = self.run_tool("apply", "--write", "--confirm-location-name", NAME, "--json")
        report = json.loads(out)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(len(report["created"]), self.creatable_count())
        self.assertFalse(report["dry_run"])


class SourceAndConfig(unittest.TestCase):
    def test_source_has_no_removal_or_update_methods_and_no_contact_or_publish_paths(self):
        source = read(hl_build.__file__)
        for word in ('"DELETE"', "'DELETE'", '"PUT"', "'PUT'", '"PATCH"', "'PATCH'", "/contacts", "/status", "workflows.publish"):
            self.assertNotIn(word, source)
        self.assertNotIn("import requests", source)
        for path in hl_build.CREATE_PATHS:
            self.assertFalse(re.search(r"contact|workflow", path))

    def test_config_is_valid_and_holds_no_phone_number(self):
        config = hl_build.load_config(hl_build.DEFAULT_CONFIG)
        raw = read(hl_build.DEFAULT_CONFIG)
        self.assertIsNone(re.search(r"\+?\d{10,}", raw))
        self.assertNotIn(chr(8212), raw)
        agent = config["voice_agents"][0]
        self.assertIn("an AI assistant", agent["welcome_message"])
        self.assertEqual(agent["recording"]["setting"], "off")
        self.assertTrue(all(t["name"].startswith("nl-") for t in config["tags"]))
        self.assertTrue(all(v["name"].startswith("nl_") for v in config["custom_values"]))
        self.assertTrue(all(f["name"].startswith("NL | ") for f in config["custom_fields"]))

    def test_config_with_a_phone_number_is_rejected(self):
        config = hl_build.load_config(hl_build.DEFAULT_CONFIG)
        config["custom_values"][0]["value"] = "+1 416 555 0100"
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "c.json")
            with open(path, "w") as handle:
                json.dump(config, handle)
            with self.assertRaises(hl_build.ToolError) as caught:
                hl_build.load_config(path)
            self.assertEqual(caught.exception.code, hl_build.EXIT_CONFIG)

    def test_redact(self):
        self.assertNotIn("abc.def", hl_build.redact("Authorization: Bearer abc.def-123"))
        self.assertNotIn("s3cret", hl_build.redact("{'Authorization': 's3cret'}"))
        self.assertEqual(hl_build.redact("x TOKEN y", "TOKEN"), "x [REDACTED] y")


if __name__ == "__main__":
    unittest.main(verbosity=2)
