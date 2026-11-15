#!/usr/bin/env python3
"""hl_build.py: a safe, create-only build tool for one HighLevel sub-account.

Python 3 standard library only. See README.md in this folder.

What it does: reads a declarative config, compares it with what exists in
the sub-account, and (only with `apply --write` and a confirmed location
name) creates what is missing. It never updates, removes, publishes or
sends anything, and it never creates contacts.

Exit codes
  0  success
  1  unexpected error
  2  bad command line (argparse)
  3  configuration problem (missing token or location, bad config file)
  4  refused: the location is the protected Ray Homes sub-account
  5  refused: --confirm-location-name missing or not equal to the API name
  6  API or network error (the run stopped)
  7  preflight: at least one required scope is not allowed
  8  verify: at least one configured item is missing
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://services.leadconnectorhq.com"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_PROTECTED = 4
EXIT_CONFIRM = 5
EXIT_API = 6
EXIT_PREFLIGHT = 7
EXIT_VERIFY = 8

# The live real estate CRM. Its location ID sits in this variable in the
# environment. This tool always refuses that location. There is no override.
PROTECTED_LOCATION_ENV = "HIGHLEVEL_LOCATION_ID"
# The token that belongs to the protected sub-account. Never used here.
PROTECTED_TOKEN_ENV = "HIGHLEVEL_API_TOKEN"

DEFAULT_TOKEN_ENV = "HIGHLEVEL_NL_DEMO_API_TOKEN"
DEFAULT_LOCATION_ENV = "HIGHLEVEL_NL_DEMO_LOCATION_ID"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "config", "next-level-answer.json")
DEFAULT_STATE_DIR = os.path.join(HERE, "state")

# The only calls that change anything. Each is a create. Paths are matched
# as full regular expressions. Anything else that is not a read is refused
# inside the client before a request is built.
CREATE_PATHS = [
    r"/locations/[A-Za-z0-9]+/customValues",
    r"/locations/[A-Za-z0-9]+/customFields",
    r"/locations/[A-Za-z0-9]+/tags",
    r"/opportunities/pipelines",
    r"/calendars",
    r"/voice-ai/agents",
    r"/voice-ai/actions",
]
# Reads that the API exposes as POST. They change nothing.
READ_POST_PATHS = [r"/workflows/search"]

WORKFLOW_API_OFF = "WORKFLOW_API_NOT_ENABLED_FOR_LOCATION"

# Scopes the create calls need, by the names on the reference pages.
WRITE_SCOPES = [
    ("locations/customValues.write", "custom values"),
    ("locations/customFields.write", "custom fields"),
    ("locations/tags.write", "tags"),
    ("pipelines.create", "pipeline"),
    ("calendars.write", "calendar"),
    ("voice-ai-agents.write", "voice agent"),
    ("voice-ai-agent-goals.write", "voice agent actions"),
]


class ToolError(Exception):
    """An expected failure with an exit code."""

    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


class ApiError(ToolError):
    def __init__(self, status, message, method, path):
        text = "API error %s on %s %s: %s" % (status, method, path, message)
        ToolError.__init__(self, EXIT_API, text)
        self.status = status


# ---------------------------------------------------------------- redaction

_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
_AUTH_PAIR = re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?)(?!bearer\b)[^\s'\",}]+")


def redact(text, token=None):
    """Remove the token and anything that looks like a credential."""
    text = "" if text is None else str(text)
    if token:
        text = text.replace(token, "[REDACTED]")
    text = _BEARER.sub(r"\1[REDACTED]", text)
    text = _AUTH_PAIR.sub(r"\1[REDACTED]", text)
    return text


# ---------------------------------------------------------------- transport


def urllib_transport(method, url, headers, body, timeout):
    """The real HTTP layer. Returns (status, headers, body_bytes)."""
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        try:
            payload = error.read()
        except Exception:
            payload = b""
        return error.code, dict(error.headers or {}), payload


class Client:
    """Every request goes through here: allowlist, pacing, one 429 retry."""

    def __init__(self, token, version, transport=None, sleep=None, pause=0.35,
                 backoff=5.0, timeout=30, allow_write=False):
        self._token = token
        self.version = version
        self.transport = transport or urllib_transport
        self.sleep = sleep or time.sleep
        self.pause = pause
        self.backoff = backoff
        self.timeout = timeout
        self.allow_write = allow_write
        self.calls = 0
        self.writes = 0

    def clean(self, text):
        return redact(text, self._token)

    def _classify(self, method, path):
        if method == "GET":
            return "read"
        if method == "POST":
            if any(re.fullmatch(p, path) for p in READ_POST_PATHS):
                return "read"
            if any(re.fullmatch(p, path) for p in CREATE_PATHS):
                return "create"
        raise ToolError(EXIT_ERROR, "Refused: %s %s is not on this tool's allowlist." % (method, path))

    def _send(self, method, path, query, body):
        kind = self._classify(method, path)
        if kind == "create" and not self.allow_write:
            raise ToolError(EXIT_ERROR, "Refused: a create call (%s) was attempted in a dry run." % path)
        url = BASE_URL + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "Authorization": "Bearer " + self._token,
            "Version": self.version,
            "Accept": "application/json",
            "User-Agent": "hl-build/1.0",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        attempt = 0
        while True:
            if self.calls > 0 and self.pause > 0:
                self.sleep(self.pause)
            self.calls += 1
            try:
                status, resp_headers, payload = self.transport(method, url, headers, data, self.timeout)
            except ToolError:
                raise
            except Exception as error:  # network failure, timeout, TLS
                raise ToolError(EXIT_API, "Network error on %s %s: %s" % (
                    method, path, self.clean("%s: %s" % (type(error).__name__, error))))
            if status == 429 and attempt == 0:
                attempt = 1
                wait = self.backoff
                retry_after = {str(k).lower(): v for k, v in (resp_headers or {}).items()}.get("retry-after")
                try:
                    if retry_after is not None:
                        wait = min(max(float(retry_after), 1.0), 60.0)
                except (TypeError, ValueError):
                    pass
                self.sleep(wait)
                continue
            break
        if kind == "create" and status < 400:
            self.writes += 1
        text = (payload or b"").decode("utf-8", "replace")
        parsed = None
        if text.strip():
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = None
        return status, parsed, text

    def _message(self, parsed, text):
        message = None
        if isinstance(parsed, dict):
            message = parsed.get("message") or parsed.get("error") or parsed.get("msg")
            if isinstance(message, (list, dict)):
                message = json.dumps(message)
        if not message:
            message = (text or "").strip()[:400] or "(no message)"
        return self.clean(message)

    def request(self, method, path, query=None, body=None, allow_404=False):
        """Returns parsed JSON. Stops on any status of 400 or more, except 404 when allowed."""
        status, parsed, text = self._send(method, path, query, body)
        if status == 404 and allow_404:
            return None
        if status >= 400:
            raise ApiError(status, self._message(parsed, text), method, path)
        return parsed if parsed is not None else {}

    def probe(self, method, path, query=None, body=None):
        """Like request, but reports the status instead of stopping. Reads only."""
        if self._classify(method, path) != "read":
            raise ToolError(EXIT_ERROR, "Refused: probe is for reads only.")
        status, parsed, text = self._send(method, path, query, body)
        message = "" if status < 400 else self._message(parsed, text)
        return status, parsed, message


# ---------------------------------------------------------------- config

_PHONE_LIKE = re.compile(r"\+?\d[\d\s().-]{8,}\d")


def _strip_notes(value):
    """Drop every key that starts with an underscore (notes such as _verify)."""
    if isinstance(value, dict):
        return {k: _strip_notes(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [_strip_notes(v) for v in value]
    return value


def _all_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            for text in _all_strings(item):
                yield text
    elif isinstance(value, list):
        for item in value:
            for text in _all_strings(item):
                yield text
    elif isinstance(value, str):
        yield value


def assemble_prompt(agent):
    parts = []
    for slot in agent.get("prompt_slots", []):
        parts.append("## %s\n%s" % (slot["slot"], slot["text"]))
    return "\n\n".join(parts)


def load_config(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, ValueError) as error:
        raise ToolError(EXIT_CONFIG, "Cannot read config %s: %s" % (path, error))
    problems = []
    for text in _all_strings(_strip_notes(config)):
        if _PHONE_LIKE.search(text):
            problems.append("something that looks like a phone number: %r" % text[:60])
    for kind in ("custom_values", "custom_fields", "tags", "pipelines", "calendars", "voice_agents"):
        seen = set()
        for item in config.get(kind, []):
            name = item.get("name")
            if not name or not isinstance(name, str):
                problems.append("%s: an item has no name" % kind)
                continue
            if norm(name) in seen:
                problems.append("%s: duplicate name %r" % (kind, name))
            seen.add(norm(name))
    for item in config.get("custom_values", []):
        if not isinstance(item.get("value"), str):
            problems.append("custom value %s: value must be a string" % item.get("name"))
    for item in config.get("custom_fields", []):
        if not item.get("dataType"):
            problems.append("custom field %s: dataType missing" % item.get("name"))
    for item in config.get("tags", []):
        if item.get("name") != str(item.get("name", "")).strip().lower():
            problems.append("tag %r: must be lower case and trimmed" % item.get("name"))
    for item in config.get("pipelines", []):
        stages = item.get("stages") or []
        if not stages or len(set(norm(s) for s in stages)) != len(stages):
            problems.append("pipeline %s: needs stages with unique names" % item.get("name"))
    for agent in config.get("voice_agents", []):
        name = agent.get("name", "")
        welcome = agent.get("welcome_message", "")
        if not 1 <= len(name) <= 40:
            problems.append("voice agent name must be 1 to 40 characters")
        if not 1 <= len(welcome) <= 190:
            problems.append("welcome message must be 1 to 190 characters (it is %d)" % len(welcome))
        needle = agent.get("ai_disclosure_must_contain") or "AI"
        if needle not in welcome:
            problems.append("welcome message must contain the AI disclosure words %r" % needle)
        duration = (agent.get("api_fields") or {}).get("maxCallDuration")
        if duration is not None and not 180 <= duration <= 900:
            problems.append("maxCallDuration must be 180 to 900")
        if not agent.get("prompt_slots"):
            problems.append("voice agent %s: prompt_slots missing" % name)
        for action in agent.get("actions", []):
            if action.get("create_via_api") and not isinstance(action.get("actionParameters"), dict):
                problems.append("action %s: create_via_api is true but actionParameters is missing" % action.get("name"))
    if problems:
        raise ToolError(EXIT_CONFIG, "Config problems in %s:\n  - %s" % (path, "\n  - ".join(problems)))
    return config


def norm(name):
    return str(name).strip().lower()


# ---------------------------------------------------------------- context


class Context:
    def __init__(self, args, env, transport, sleep, out, err):
        self.args = args
        self.env = env
        self.out = out
        self.err = err
        self.json_mode = bool(args.json)
        self.config = load_config(args.config)
        self.token_env = args.token_env
        self.location_id = self._resolve_location()
        self._guard_protected()
        token = self._resolve_token()
        version = args.api_version or self.config.get("api", {}).get("version_header") or "v3"
        self.client = Client(token, version, transport=transport, sleep=sleep,
                             pause=args.pause, timeout=args.timeout, allow_write=False)
        self.location_name = None

    def _resolve_location(self):
        location = (self.args.location or "").strip() or (self.env.get(self.args.location_env) or "").strip()
        if not location:
            raise ToolError(EXIT_CONFIG, "No location ID. Set the environment variable %s or pass --location." % self.args.location_env)
        if not re.fullmatch(r"[A-Za-z0-9]{6,64}", location):
            raise ToolError(EXIT_CONFIG, "The location ID has an unexpected shape (letters and digits only).")
        return location

    def _guard_protected(self):
        protected = (self.env.get(PROTECTED_LOCATION_ENV) or "").strip()
        if protected and self.location_id == protected:
            raise ToolError(EXIT_PROTECTED, "Refused: this location is the protected live sub-account named by %s. "
                            "This tool never runs against it. There is no override." % PROTECTED_LOCATION_ENV)
        if self.token_env == PROTECTED_TOKEN_ENV:
            raise ToolError(EXIT_PROTECTED, "Refused: %s is the token of the protected live sub-account. "
                            "Use a token created inside the target sub-account." % PROTECTED_TOKEN_ENV)

    def _resolve_token(self):
        token = (self.env.get(self.token_env) or "").strip()
        if not token:
            raise ToolError(EXIT_CONFIG, "No token. The environment variable %s is not set." % self.token_env)
        protected_token = (self.env.get(PROTECTED_TOKEN_ENV) or "").strip()
        if protected_token and token == protected_token:
            raise ToolError(EXIT_PROTECTED, "Refused: the token in %s is the same as the protected live sub-account's token." % self.token_env)
        return token

    def guard_status(self):
        if (self.env.get(PROTECTED_LOCATION_ENV) or "").strip():
            return "active"
        return "INACTIVE: %s is not set in this environment, so the tool cannot recognise the protected sub-account" % PROTECTED_LOCATION_ENV

    def say(self, text=""):
        if not self.json_mode:
            self.out.write(self.client.clean(text) + "\n")

    def fetch_location(self):
        data = self.client.request("GET", "/locations/%s" % self.location_id)
        location = data.get("location") if isinstance(data.get("location"), dict) else data
        returned_id = location.get("id")
        if returned_id and returned_id != self.location_id:
            raise ToolError(EXIT_ERROR, "The API returned a different location ID than the one asked for. Stopping.")
        self.location_name = location.get("name") or ""
        if not self.location_name:
            raise ToolError(EXIT_ERROR, "The API returned no name for this location. Stopping.")
        return self.location_name


# ---------------------------------------------------------------- reading


def _listing(data, key):
    if not isinstance(data, dict):
        return []
    items = data.get(key)
    return items if isinstance(items, list) else []


def fetch_existing(ctx):
    """Read what is in the sub-account. Names are compared ignoring case."""
    client, loc = ctx.client, ctx.location_id
    existing = {}
    real_request = client.request

    def request(method, path, query=None, allow_404=False, needs=None):
        # A kind that the config does not ask for is not read at all.
        if needs and not ctx.config.get(needs):
            return None
        return real_request(method, path, query=query, allow_404=allow_404)

    data = request("GET", "/locations/%s/customValues" % loc, allow_404=True, needs="custom_values")
    existing["custom_value"] = {norm(i.get("name", "")): {"id": i.get("id")} for i in _listing(data, "customValues")}
    data = request("GET", "/locations/%s/customFields" % loc, query={"model": "all"}, allow_404=True, needs="custom_fields")
    existing["custom_field"] = {norm(i.get("name", "")): {"id": i.get("id"), "dataType": i.get("dataType")}
                                for i in _listing(data, "customFields")}
    data = request("GET", "/locations/%s/tags" % loc, allow_404=True, needs="tags")
    existing["tag"] = {norm(i.get("name", "")): {"id": i.get("id")} for i in _listing(data, "tags")}
    data = request("GET", "/opportunities/pipelines", query={"locationId": loc}, allow_404=True, needs="pipelines")
    existing["pipeline"] = {}
    for item in _listing(data, "pipelines"):
        stages = sorted(item.get("stages") or [], key=lambda s: s.get("position") or 0)
        existing["pipeline"][norm(item.get("name", ""))] = {"id": item.get("id"), "stages": [s.get("name", "") for s in stages]}
    data = request("GET", "/calendars", query={"locationId": loc}, allow_404=True, needs="calendars")
    existing["calendar"] = {norm(i.get("name", "")): {"id": i.get("id")} for i in _listing(data, "calendars")}
    existing["voice_agent"] = {}
    page = 1
    while page <= 40 and ctx.config.get("voice_agents"):
        data = request("GET", "/voice-ai/agents", query={"locationId": loc, "page": page, "pageSize": 50}, allow_404=True)
        agents = _listing(data, "agents")
        for item in agents:
            actions = {norm(a.get("name", "")): a.get("id") for a in (item.get("actions") or [])}
            existing["voice_agent"][norm(item.get("agentName", ""))] = {"id": item.get("id"), "actions": actions}
        total = (data or {}).get("total") or 0
        if not agents or page * 50 >= total:
            break
        page += 1
    return existing


# ---------------------------------------------------------------- state


def state_path(ctx):
    return os.path.join(ctx.args.state_dir, ctx.location_id + ".json")


def load_state(ctx):
    path = state_path(ctx)
    if not os.path.exists(path):
        return {"locationId": ctx.location_id, "locationName": ctx.location_name, "created": []}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, ValueError) as error:
        raise ToolError(EXIT_CONFIG, "Cannot read state file %s: %s" % (path, error))
    if state.get("locationId") != ctx.location_id or not isinstance(state.get("created"), list):
        raise ToolError(EXIT_CONFIG, "State file %s does not belong to this location." % path)
    return state


def save_state(ctx, state):
    """Holds IDs and names only. The token is never written."""
    os.makedirs(ctx.args.state_dir, exist_ok=True)
    state["locationName"] = ctx.location_name
    state["updatedAt"] = _now()
    text = ctx.client.clean(json.dumps(state, indent=2, sort_keys=True))
    path = state_path(ctx)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    os.replace(temp, path)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def created_by_tool(state, kind, name):
    return any(c.get("kind") == kind and norm(c.get("name", "")) == norm(name) for c in state.get("created", []))


# ---------------------------------------------------------------- planning

KIND_LABEL = {
    "custom_value": "custom value",
    "custom_field": "custom field",
    "tag": "tag",
    "pipeline": "pipeline",
    "calendar": "calendar",
    "voice_agent": "voice agent",
    "voice_action": "agent action",
}


def _item(kind, name, action, item_id=None, note="", spec=None, parent=None):
    return {"kind": kind, "name": name, "action": action, "id": item_id, "note": note, "_spec": spec, "_parent": parent}


def build_plan(config, existing, state):
    """One row per configured item: create, exists (left alone), manual or blocked."""
    rows = []
    simple = [("custom_values", "custom_value"), ("custom_fields", "custom_field"), ("tags", "tag"),
              ("pipelines", "pipeline"), ("calendars", "calendar")]
    for config_key, kind in simple:
        for spec in config.get(config_key, []):
            found = existing[kind].get(norm(spec["name"]))
            if not found:
                rows.append(_item(kind, spec["name"], "create", spec=spec))
                continue
            note = ""
            if kind == "pipeline" and [norm(s) for s in found.get("stages", [])] != [norm(s) for s in spec["stages"]]:
                note = "stages differ from the config; left as they are"
            if kind == "custom_field" and found.get("dataType") and found["dataType"] != spec["dataType"]:
                note = "type is %s, config says %s; left as it is" % (found["dataType"], spec["dataType"])
            rows.append(_item(kind, spec["name"], "exists", found.get("id"), note, spec=spec))
    for agent in config.get("voice_agents", []):
        found = existing["voice_agent"].get(norm(agent["name"]))
        ours = created_by_tool(state, "voice_agent", agent["name"])
        if found:
            rows.append(_item("voice_agent", agent["name"], "exists", found.get("id"), spec=agent))
        else:
            rows.append(_item("voice_agent", agent["name"], "create", note="no number, no voice: set by hand", spec=agent))
        for action in agent.get("actions", []):
            label = "%s (%s)" % (action["name"], action.get("actionType", "?"))
            if found and norm(action["name"]) in found.get("actions", {}):
                rows.append(_item("voice_action", label, "exists", found["actions"][norm(action["name"])], spec=action, parent=agent["name"]))
            elif not action.get("create_via_api"):
                rows.append(_item("voice_action", label, "manual", note="build by hand in the agent (see _verify in the config)", spec=action, parent=agent["name"]))
            elif found and not ours:
                rows.append(_item("voice_action", label, "blocked", note="the agent exists and was not created by this tool; add the action by hand", spec=action, parent=agent["name"]))
            else:
                rows.append(_item("voice_action", label, "create", spec=action, parent=agent["name"]))
    return rows


ACTION_WORDS = {"create": "WOULD CREATE", "exists": "exists, leave alone", "manual": "by hand", "blocked": "skipped"}


def public_rows(rows):
    return [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]


def render_table(headers, lines):
    widths = [len(h) for h in headers]
    for line in lines:
        for index, cell in enumerate(line):
            widths[index] = max(widths[index], len(str(cell)))
    widths = [min(w, 70) for w in widths]

    def fmt(cells):
        return "  ".join(str(c)[:70].ljust(widths[i]) for i, c in enumerate(cells)).rstrip()

    output = [fmt(headers), fmt(["-" * w for w in widths])]
    output.extend(fmt(line) for line in lines)
    return "\n".join(output)


def summarize(rows):
    counts = {}
    for row in rows:
        counts[row["action"]] = counts.get(row["action"], 0) + 1
    return counts


def print_plan(ctx, rows, words=None):
    words = words or ACTION_WORDS
    lines = [[KIND_LABEL[r["kind"]], r["name"], words.get(r["action"], r["action"]), r["id"] or "", r["note"]] for r in rows]
    ctx.say(render_table(["KIND", "NAME", "ACTION", "ID", "NOTE"], lines))
    counts = summarize(rows)
    ctx.say()
    ctx.say("Totals: " + ", ".join("%s: %d" % (words.get(k, k), counts[k]) for k in sorted(counts)))


# ---------------------------------------------------------------- creating


def _new_id(response, wrapper):
    if isinstance(response, dict):
        inner = response.get(wrapper)
        if isinstance(inner, dict) and inner.get("id"):
            return inner["id"]
        if response.get("id"):
            return response["id"]
    return None


def create_item(ctx, row, ids):
    """One create call for one missing item. Returns the new ID (or None if the API gave none)."""
    client, loc, spec, kind = ctx.client, ctx.location_id, row["_spec"], row["kind"]
    api = ctx.config.get("api", {})
    if kind == "custom_value":
        response = client.request("POST", "/locations/%s/customValues" % loc, body={"name": spec["name"], "value": spec["value"]})
        return _new_id(response, "customValue")
    if kind == "custom_field":
        body = {"name": spec["name"], "dataType": spec["dataType"], "model": spec.get("model", "contact")}
        if spec.get("placeholder"):
            body["placeholder"] = spec["placeholder"]
        if spec.get("options"):
            body[api.get("custom_field_options_request_field") or "options"] = list(spec["options"])
        response = client.request("POST", "/locations/%s/customFields" % loc, body=body)
        return _new_id(response, "customField")
    if kind == "tag":
        response = client.request("POST", "/locations/%s/tags" % loc, body={"name": spec["name"]})
        return _new_id(response, "tag")
    if kind == "pipeline":
        stages = [{"name": name, "position": index + 1} for index, name in enumerate(spec["stages"])]
        response = client.request("POST", "/opportunities/pipelines", body={"name": spec["name"], "stages": stages, "locationId": loc})
        return _new_id(response, "pipeline")
    if kind == "calendar":
        body = _strip_notes(spec.get("api_fields") or {})
        body.update({"locationId": loc, "name": spec["name"]})
        response = client.request("POST", "/calendars", body=body)
        return _new_id(response, "calendar")
    if kind == "voice_agent":
        body = _strip_notes(spec.get("api_fields") or {})
        for forbidden in ("inboundNumber", "numberPoolId"):
            body.pop(forbidden, None)  # numbers are attached by hand, never here
        body.update({"locationId": loc, "agentName": spec["name"], "welcomeMessage": spec["welcome_message"],
                     "agentPrompt": assemble_prompt(spec)})
        response = client.request("POST", "/voice-ai/agents", body=body)
        return _new_id(response, "agent")
    if kind == "voice_action":
        agent_id = ids.get(("voice_agent", norm(row["_parent"])))
        if not agent_id:
            raise ToolError(EXIT_ERROR, "No agent ID for action %s. Stopping." % row["name"])
        parameters = _resolve_refs(_strip_notes(spec["actionParameters"]), ids)
        body = {"agentId": agent_id, "locationId": loc, "actionType": spec["actionType"], "name": spec["name"],
                "actionParameters": parameters}
        response = client.request("POST", "/voice-ai/actions", body=body)
        return _new_id(response, "action")
    raise ToolError(EXIT_ERROR, "Unknown kind %s" % kind)


def _resolve_refs(value, ids):
    """Replace "$calendar_id:<calendar name>" with the ID of that calendar."""
    if isinstance(value, dict):
        return {k: _resolve_refs(v, ids) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_refs(v, ids) for v in value]
    if isinstance(value, str) and value.startswith("$calendar_id:"):
        found = ids.get(("calendar", norm(value.split(":", 1)[1])))
        if not found:
            raise ToolError(EXIT_ERROR, "Cannot resolve %s. Stopping." % value)
        return found
    return value


# ---------------------------------------------------------------- commands


def header(ctx, title):
    ctx.say("%s. Location: %s (%s)" % (title, ctx.location_name, ctx.location_id))
    ctx.say("Protected sub-account guard: %s" % ctx.guard_status())
    ctx.say()


def cmd_preflight(ctx):
    loc = ctx.location_id
    need = lambda key: bool(ctx.config.get(key))  # required only if the config asks for that kind
    checks = [
        ("locations.readonly", True, "GET", "/locations/%s" % loc, None, None),
        ("locations/customValues.readonly", need("custom_values"), "GET", "/locations/%s/customValues" % loc, None, None),
        ("locations/customFields.readonly", need("custom_fields"), "GET", "/locations/%s/customFields" % loc, {"model": "all"}, None),
        ("locations/tags.readonly", need("tags"), "GET", "/locations/%s/tags" % loc, None, None),
        ("opportunities.readonly", need("pipelines"), "GET", "/opportunities/pipelines", {"locationId": loc}, None),
        ("calendars.readonly", need("calendars"), "GET", "/calendars", {"locationId": loc}, None),
        ("voice-ai-agents.readonly", need("voice_agents"), "GET", "/voice-ai/agents", {"locationId": loc, "page": 1, "pageSize": 1}, None),
        ("forms.readonly", False, "GET", "/forms", {"locationId": loc, "limit": 1}, None),
        # Search is a POST on the reference page, but it only reads.
        ("workflows.readonly", False, "POST", "/workflows/search", {"locationId": loc}, {"limit": 1}),
    ]
    results = []
    workflow_api = "unknown"
    location_name = None
    for scope, required, method, path, query, body in checks:
        try:
            status, parsed, message = ctx.client.probe(method, path, query, body)
        except ToolError as error:
            status, parsed, message = None, None, error.message
        allowed = status is not None and status < 400
        note = ""
        if scope == "locations.readonly" and allowed and isinstance(parsed, dict):
            location = parsed.get("location") if isinstance(parsed.get("location"), dict) else parsed
            location_name = location.get("name")
        if scope == "workflows.readonly":
            if allowed:
                workflow_api = "enabled"
            elif WORKFLOW_API_OFF in (message or "") or WORKFLOW_API_OFF in json.dumps(parsed or {}):
                workflow_api = "not enabled for this location"
                note = "the scope may be fine; HighLevel has not switched the workflow API on here"
            else:
                workflow_api = "unknown (the read was refused)"
        if not allowed and not note:
            note = message or ""
        results.append({"scope": scope, "required": required, "allowed": allowed, "status": status,
                        "call": "%s %s" % (method, path.replace(loc, "{locationId}")), "note": note})
    ctx.location_name = location_name
    failed = [r for r in results if r["required"] and not r["allowed"]]
    code = EXIT_PREFLIGHT if failed else EXIT_OK
    report = {
        "command": "preflight", "location": {"id": loc, "name": location_name},
        "protected_guard": ctx.guard_status(), "workflow_api": workflow_api, "scopes": results,
        "write_scopes_not_tested": [s for s, _ in WRITE_SCOPES], "exit_code": code,
    }
    if ctx.json_mode:
        emit_json(ctx, report)
        return code
    ctx.say("Preflight (read-only).")
    ctx.say("Location name: %s" % (location_name or "NOT READ (locations.readonly was refused)"))
    ctx.say("Location ID:   %s" % loc)
    ctx.say("Check that this is the sub-account you mean before going on.")
    ctx.say("Protected sub-account guard: %s" % ctx.guard_status())
    ctx.say()
    lines = [[r["scope"], "required" if r["required"] else "optional", "allowed" if r["allowed"] else "NOT ALLOWED",
              r["status"] if r["status"] is not None else "", r["note"]] for r in results]
    ctx.say(render_table(["SCOPE", "NEED", "RESULT", "HTTP", "NOTE"], lines))
    ctx.say()
    ctx.say("Workflow API for this location: %s" % workflow_api)
    ctx.say()
    ctx.say("Write scopes cannot be tested without writing, so they are not tested here.")
    ctx.say("They show up at `apply --write`, which stops at the first refusal:")
    for scope, what in WRITE_SCOPES:
        ctx.say("  %s (%s)" % (scope, what))
    ctx.say()
    ctx.say("Result: %s" % ("every required read scope is allowed." if not failed else
                            "%d required scope(s) not allowed. Fix the ticks and run preflight again." % len(failed)))
    return code


def cmd_plan(ctx, title="Plan (read-only)", dry_note=None):
    ctx.fetch_location()
    existing = fetch_existing(ctx)
    rows = build_plan(ctx.config, existing, load_state(ctx))
    report = {"command": ctx.args.command, "dry_run": True, "location": {"id": ctx.location_id, "name": ctx.location_name},
              "items": public_rows(rows), "summary": summarize(rows), "created": [], "exit_code": EXIT_OK}
    if ctx.json_mode:
        emit_json(ctx, report)
        return EXIT_OK
    header(ctx, title)
    print_plan(ctx, rows)
    ctx.say()
    ctx.say(dry_note or "Nothing was changed. This command only reads.")
    return EXIT_OK


def cmd_apply(ctx):
    args = ctx.args
    if not args.write:
        return cmd_plan(ctx, title="Apply, DRY RUN (no --write)",
                        dry_note="DRY RUN. Nothing was changed. To create the items marked WOULD CREATE, run again with "
                                 "--write and --confirm-location-name \"<the exact location name above>\".")
    name = ctx.fetch_location()
    if args.confirm_location_name is None:
        raise ToolError(EXIT_CONFIRM, "Refused: --write needs --confirm-location-name \"<exact name>\". "
                        "The API says this location is named %r. Nothing was changed." % name)
    if args.confirm_location_name != name:
        raise ToolError(EXIT_CONFIRM, "Refused: --confirm-location-name %r does not equal the name the API returned, %r. "
                        "Nothing was changed." % (args.confirm_location_name, name))
    existing = fetch_existing(ctx)
    state = load_state(ctx)
    rows = build_plan(ctx.config, existing, state)
    ids = {}
    for row in rows:
        if row["action"] == "exists" and row["id"]:
            ids[(row["kind"], norm(row["name"]))] = row["id"]
    created = []
    if not ctx.json_mode:
        header(ctx, "Apply, WRITING")
    ctx.client.allow_write = True
    failure = None
    try:
        for row in rows:
            if row["action"] != "create":
                continue
            new_id = create_item(ctx, row, ids)
            ids[(row["kind"], norm(row["name"]))] = new_id
            row["action"], row["id"] = "created", new_id
            record = {"kind": row["kind"], "name": row["name"], "id": new_id, "createdAt": _now()}
            if row.get("_parent"):
                record["parent"] = row["_parent"]
            created.append(record)
            state["created"].append(record)
            save_state(ctx, state)
            ctx.say("created  %-13s %-45s id=%s" % (KIND_LABEL[row["kind"]], row["name"], new_id or "(no ID in the response)"))
    except ToolError as error:
        failure = error
    finally:
        ctx.client.allow_write = False
    words = dict(ACTION_WORDS, created="CREATED", create="NOT CREATED (run stopped)")
    code = failure.code if failure else EXIT_OK
    report = {"command": "apply", "dry_run": False, "location": {"id": ctx.location_id, "name": ctx.location_name},
              "items": public_rows(rows), "summary": summarize(rows), "created": created,
              "state_file": state_path(ctx) if created else None, "exit_code": code}
    if failure:
        report["error"] = ctx.client.clean(failure.message)
    if ctx.json_mode:
        emit_json(ctx, report)
        return code
    ctx.say()
    print_plan(ctx, rows, words)
    ctx.say()
    ctx.say("Created %d item(s). Nothing that already existed was changed." % len(created))
    if created:
        ctx.say("State file: %s" % state_path(ctx))
    if failure:
        ctx.err.write(ctx.client.clean("STOPPED: %s\nItems created before the stop are listed above and in the state file. "
                                       "It is safe to run apply again after fixing the cause.\n" % failure.message))
    return code


def cmd_verify(ctx):
    ctx.fetch_location()
    existing = fetch_existing(ctx)
    rows = build_plan(ctx.config, existing, load_state(ctx))
    words = {"exists": "present", "create": "MISSING", "manual": "by hand, not checked", "blocked": "MISSING (by hand)"}
    missing = [r for r in rows if r["action"] in ("create", "blocked")]
    code = EXIT_VERIFY if missing else EXIT_OK
    report = {"command": "verify", "location": {"id": ctx.location_id, "name": ctx.location_name},
              "items": [dict(r, action=words.get(r["action"], r["action"])) for r in public_rows(rows)],
              "missing": len(missing), "exit_code": code}
    if ctx.json_mode:
        emit_json(ctx, report)
        return code
    header(ctx, "Verify (read-only)")
    print_plan(ctx, rows, words)
    ctx.say()
    ctx.say("Result: %s" % ("every item the API can create is present." if not missing else "%d item(s) missing." % len(missing)))
    return code


def emit_json(ctx, report):
    ctx.out.write(ctx.client.clean(json.dumps(report, indent=2)) + "\n")


# ---------------------------------------------------------------- CLI


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--token-env", default=DEFAULT_TOKEN_ENV, metavar="NAME",
                        help="name of the environment variable that holds the private integration token (default: %(default)s). The token itself is never passed on the command line.")
    common.add_argument("--location-env", default=DEFAULT_LOCATION_ENV, metavar="NAME",
                        help="name of the environment variable that holds the location ID (default: %(default)s)")
    common.add_argument("--location", metavar="ID", help="location ID, instead of --location-env")
    common.add_argument("--config", default=DEFAULT_CONFIG, metavar="FILE", help="build definition (default: config/next-level-answer.json)")
    common.add_argument("--state-dir", default=DEFAULT_STATE_DIR, metavar="DIR", help="where the state file of created IDs is kept (default: state/)")
    common.add_argument("--api-version", metavar="VALUE", help="value of the Version header (default: from the config, v3)")
    common.add_argument("--pause", type=float, default=0.35, metavar="SECONDS", help="pause between API calls (default: %(default)s)")
    common.add_argument("--timeout", type=float, default=30, metavar="SECONDS", help="timeout per API call (default: %(default)s)")
    common.add_argument("--json", action="store_true", help="machine-readable output on stdout")

    parser = argparse.ArgumentParser(
        prog="hl_build.py",
        description="Create-only build tool for one HighLevel sub-account. Every subcommand is a dry, read-only run "
                    "unless it is `apply --write` with a confirmed location name. It never updates or removes anything, "
                    "never creates contacts, never publishes a workflow, and always refuses the location named by "
                    "the environment variable %s." % PROTECTED_LOCATION_ENV,
        epilog="Exit codes: 0 ok, 1 unexpected error, 2 bad command line, 3 configuration, 4 protected location refused, "
               "5 location name not confirmed, 6 API or network error, 7 preflight failed, 8 verify found missing items.")
    sub = parser.add_subparsers(dest="command", metavar="{preflight,plan,apply,verify}")
    sub.required = True
    sub.add_parser("preflight", parents=[common],
                   help="read-only: test each read scope, report the workflow API, print the location name",
                   description="Read-only. Makes one harmless read per scope the build needs and reports allowed or not allowed. "
                               "Reports whether the workflow API is enabled for the location. Prints the location name so you can "
                               "confirm it is the right sub-account. Exit 7 if a required scope is not allowed.")
    sub.add_parser("plan", parents=[common], help="read-only: show what would be created and what would be left alone",
                   description="Read-only. Fetches what exists and prints a table of what would be created or left alone.")
    apply_parser = sub.add_parser("apply", parents=[common], help="create what is missing (needs --write and --confirm-location-name)",
                                  description="Creates only what is missing. Never updates or removes an existing item. Without --write "
                                              "it behaves like plan. With --write it refuses to run unless --confirm-location-name equals "
                                              "the name the API returns. Prints each created item with its ID and records the IDs in the state file.")
    apply_parser.add_argument("--write", action="store_true", help="make the changes. Without this flag apply is a dry run")
    apply_parser.add_argument("--confirm-location-name", metavar="NAME", help="the exact name of the sub-account, as printed by preflight or plan")
    sub.add_parser("verify", parents=[common], help="read-only: confirm each configured item exists",
                   description="Read-only. Reads the sub-account again and confirms each configured item exists. Exit 8 if any is missing.")
    return parser


def main(argv=None, env=None, transport=None, sleep=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    env = os.environ if env is None else env
    args = build_parser().parse_args(argv)
    token_value = (env.get(args.token_env) or "").strip() or None

    def fail(code, message):
        message = redact(message, token_value)
        if args.json:
            out.write(json.dumps({"command": args.command, "error": message, "exit_code": code}, indent=2) + "\n")
        else:
            err.write("ERROR: %s\n" % message)
        return code

    try:
        ctx = Context(args, env, transport, sleep, out, err)
        handler = {"preflight": cmd_preflight, "plan": cmd_plan, "apply": cmd_apply, "verify": cmd_verify}[args.command]
        return handler(ctx)
    except ToolError as error:
        return fail(error.code, error.message)
    except KeyboardInterrupt:
        return fail(EXIT_ERROR, "Interrupted.")
    except Exception as error:  # never let a traceback carry a header
        return fail(EXIT_ERROR, "Unexpected %s: %s" % (type(error).__name__, error))


if __name__ == "__main__":
    sys.exit(main())
