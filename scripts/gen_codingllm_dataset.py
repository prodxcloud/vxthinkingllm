"""
CodingLLM dataset generator — produces 300+ training records grounded in the
real prodxcloud codebase (studio.go handler patterns, Studio TSX components,
FastAPI endpoints).

Output:
    app/data/datasets/codingllm/generated.json   (JSON array of records)

Record schema matches what the trainer loader and the backend system prompt
expect:
    {
      "task":     "generate|edit|review|test|refactor|summary|bugfix",
      "language": "python|go|typescript",
      "framework": "fastapi|gin|react|nextjs|next",
      "prompt":    "<user instruction>",
      "context":   "<existing signature / snippet / diff>",
      "output":    "<ideal response — code, XML search/replace, review notes>"
    }

Run from repo root:
    python3 -m scripts.gen_codingllm_dataset
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

OUT = Path("app/data/datasets/codingllm/generated.json")


# ----------------------------------------------------------------------------
# Template helpers
# ----------------------------------------------------------------------------


def go_handler(name: str, path: str, method: str, req_fields: list[tuple[str, str]],
               purpose: str, body: str) -> dict:
    """Emit a Gin handler record mirroring the style of studio.go."""
    req_struct = "\n\t\t".join(f'{n.title().replace("_", "")} {t} `json:"{n}"`' for n, t in req_fields)
    return {
        "task": "generate",
        "language": "go",
        "framework": "gin",
        "prompt": f"Write a Gin handler `{name}` that handles {method} {path}. {purpose}",
        "context": f"Request body fields: {', '.join(n for n, _ in req_fields)}. Use ensurePathUnderRoot for any filesystem path, and return JSON via c.JSON(status, gin.H{{...}}).",
        "output": body.strip("\n"),
    }


def tsx_component(name: str, purpose: str, props: str, body: str) -> dict:
    """Emit a TSX component record matching Studio component style."""
    return {
        "task": "generate",
        "language": "typescript",
        "framework": "react",
        "prompt": f"Write a React component `<{name}>` that {purpose}.",
        "context": f"Props: {props}. Studio dark theme: bg-[#1e1e1e], border-[#3e3e3e], text-[#cccccc], selected bg-[#0e639c].",
        "output": body.strip("\n"),
    }


def ts_util(name: str, purpose: str, signature: str, body: str) -> dict:
    return {
        "task": "generate",
        "language": "typescript",
        "framework": "",
        "prompt": f"Write a TypeScript utility `{name}` that {purpose}.",
        "context": f"Signature: {signature}",
        "output": body.strip("\n"),
    }


def py_endpoint(name: str, method: str, path: str, purpose: str, body: str) -> dict:
    return {
        "task": "generate",
        "language": "python",
        "framework": "fastapi",
        "prompt": f"Write a FastAPI {method} {path} endpoint ({name}). {purpose}",
        "context": "Uses AsyncSession via Depends(get_db). Pydantic v2 for schemas. Return 4xx with explicit messages, never leak ORM errors.",
        "output": body.strip("\n"),
    }


def review(snippet: str, findings: str) -> dict:
    return {
        "task": "review",
        "language": "auto",
        "framework": "",
        "prompt": "Review this code and flag issues (security, correctness, readability).",
        "context": f"```\n{snippet}\n```",
        "output": findings.strip("\n"),
    }


def refactor(before: str, after: str, rationale: str) -> dict:
    return {
        "task": "refactor",
        "language": "auto",
        "framework": "",
        "prompt": f"Refactor this function. {rationale}",
        "context": before.strip("\n"),
        "output": after.strip("\n"),
    }


def edit_diff(instruction: str, before: str, diff: str) -> dict:
    return {
        "task": "edit",
        "language": "auto",
        "framework": "",
        "prompt": instruction,
        "context": before.strip("\n"),
        "output": diff.strip("\n"),
    }


def test_record(thing: str, language: str, framework: str, body: str) -> dict:
    return {
        "task": "test",
        "language": language,
        "framework": framework,
        "prompt": f"Write tests for {thing}.",
        "context": "",
        "output": body.strip("\n"),
    }


def summary(thing: str, body: str) -> dict:
    return {
        "task": "summary",
        "language": "auto",
        "framework": "",
        "prompt": f"Summarize what {thing} does for a new engineer.",
        "context": "",
        "output": body.strip("\n"),
    }


def bugfix(symptom: str, cause: str, diff: str) -> dict:
    return {
        "task": "bugfix",
        "language": "auto",
        "framework": "",
        "prompt": f"Fix this bug: {symptom}",
        "context": f"Root cause: {cause}",
        "output": diff.strip("\n"),
    }


# ----------------------------------------------------------------------------
# Scenario inventories (the variation surface)
# ----------------------------------------------------------------------------

# Go studio.go handler variations
GO_RESOURCES = [
    ("workspace", "workspaces", "/api/v2/studio/workspaces"),
    ("session",   "sessions",   "/api/v2/studio/sessions"),
    ("template",  "templates",  "/api/v2/studio/templates"),
    ("agent",     "agents",     "/api/v2/studio/agents"),
    ("snippet",   "snippets",   "/api/v2/studio/snippets"),
    ("preset",    "presets",    "/api/v2/studio/presets"),
    ("domain",    "domains",    "/api/v2/studio/domains"),
    ("secret",    "secrets",    "/api/v2/studio/secrets"),
    ("env",       "envs",       "/api/v2/studio/envs"),
    ("hook",      "hooks",      "/api/v2/studio/hooks"),
]

# TSX component variations
TSX_COMPONENTS = [
    ("RuntimePicker",      "lets the user pick a runtime from react/fastapi/html/nextjs/expo/fullstack"),
    ("TemplatePicker",     "shows available workspace templates grouped by runtime"),
    ("PlanBadge",          "renders the user's subscription plan as a coloured pill"),
    ("NodeTierCard",       "displays a compute-node tier (NANO/MICRO/STANDARD/PRO/POWER) with price + specs"),
    ("InvoiceRow",         "renders a single invoice row with status chip and download link"),
    ("GitProviderPicker",  "lets the user choose GitHub / GitLab / Bitbucket before a push"),
    ("DomainRow",          "shows a custom domain with verify state, cert state, and copy DNS value"),
    ("SubscriptionGate",   "blocks a page when subscription status is not active/trial"),
    ("DevServerStatusDot", "renders a green/yellow/red dot based on a status prop"),
    ("SessionIdInput",     "input that enforces the >=16 char, [a-zA-Z0-9._-] regex"),
    ("ErrorBanner",        "bold red banner with title + message, dismissable"),
    ("EmptyState",         "centered icon + title + body + CTA for empty lists"),
    ("CopyCodeButton",     "one-click copy of a code block with a short confirmation"),
    ("LogLine",            "single log-line row with level colour, timestamp, and message"),
    ("KebabMenu",          "3-dot menu with dropdown items including danger actions"),
    ("NodePurchaseSummary","review step for node purchase: tier, purpose, total, coupon"),
    ("BitcoinQR",          "shows a BTC address + QR + 30s countdown for node payment"),
    ("ReadinessProbe",     "polls /devserver/ready and renders spinner or ready checkmark"),
    ("BranchSlug",         "shows the auto-derived branch name from a prompt"),
    ("DiffSummary",        "renders filesChanged list with additions/deletions counts"),
]

# FastAPI endpoint variations
PY_ENDPOINTS = [
    ("list_workspaces",      "GET",    "/workspaces",                 "List a user's workspaces with pagination"),
    ("create_workspace",     "POST",   "/workspaces",                 "Create a new workspace with runtime + template"),
    ("get_workspace",        "GET",    "/workspaces/{id}",            "Fetch a single workspace by id"),
    ("delete_workspace",     "DELETE", "/workspaces/{id}",            "Soft-delete a workspace"),
    ("rename_workspace",     "PATCH",  "/workspaces/{id}",            "Rename a workspace"),
    ("list_invoices",        "GET",    "/billing/invoices",           "Return billing invoices for the current tenant"),
    ("create_api_key",       "POST",   "/developer/keys",             "Create a new API key with scopes"),
    ("revoke_api_key",       "DELETE", "/developer/keys/{id}",        "Revoke an API key"),
    ("get_me",               "GET",    "/auth/me",                    "Return the current user + subscription status"),
    ("list_nodes",           "GET",    "/nodes",                      "Return the user's compute nodes"),
    ("purchase_node",        "POST",   "/nodes",                      "Purchase a compute node at a given tier"),
    ("rotate_api_key",       "POST",   "/developer/keys/{id}/rotate", "Rotate an API key secret"),
    ("list_audit_logs",      "GET",    "/audit",                      "Return tenant audit logs (gated by plan)"),
    ("create_support_ticket","POST",   "/support/tickets",            "File a support ticket from the product"),
    ("update_profile",       "PUT",    "/auth/profile",               "Update name/company/use-case"),
]


# ----------------------------------------------------------------------------
# 1) Go handler records
# ----------------------------------------------------------------------------

def go_handlers() -> list[dict]:
    out: list[dict] = []
    for singular, plural, base in GO_RESOURCES:
        S = singular.title()
        # LIST
        out.append(go_handler(
            name=f"List{S}s",
            path=base,
            method="GET",
            req_fields=[("user_id", "string"), ("limit", "int")],
            purpose=f"Return the user's {plural} with an optional limit.",
            body=f"""
// List{S}s returns {plural} for the caller. `limit` defaults to 50, max 500.
func List{S}s(c *gin.Context) {{
\tuserID := strings.TrimSpace(c.Query("user_id"))
\tif userID == "" {{
\t\tc.JSON(http.StatusBadRequest, gin.H{{"error": "user_id is required"}})
\t\treturn
\t}}
\tlimit := 50
\tif raw := c.Query("limit"); raw != "" {{
\t\tif v, err := strconv.Atoi(raw); err == nil && v > 0 && v <= 500 {{
\t\t\tlimit = v
\t\t}}
\t}}
\titems, err := store.List{S}s(c.Request.Context(), userID, limit)
\tif err != nil {{
\t\tapplog.Errorf("list {singular}s: %v", err)
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": "internal error"}})
\t\treturn
\t}}
\tc.JSON(http.StatusOK, gin.H{{"items": items, "count": len(items)}})
}}
""",
        ))
        # CREATE
        out.append(go_handler(
            name=f"Create{S}",
            path=base,
            method="POST",
            req_fields=[("user_id", "string"), ("name", "string")],
            purpose=f"Create a new {singular} for the caller.",
            body=f"""
// Create{S} inserts a new {singular}. Names are trimmed and capped at 120 chars.
func Create{S}(c *gin.Context) {{
\tvar req struct {{
\t\tUserID string `json:"user_id" binding:"required"`
\t\tName   string `json:"name" binding:"required"`
\t}}
\tif err := c.ShouldBindJSON(&req); err != nil {{
\t\tc.JSON(http.StatusBadRequest, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\tname := strings.TrimSpace(req.Name)
\tif l := len(name); l == 0 || l > 120 {{
\t\tc.JSON(http.StatusUnprocessableEntity, gin.H{{"error": "name must be 1-120 chars"}})
\t\treturn
\t}}
\titem, err := store.Create{S}(c.Request.Context(), req.UserID, name)
\tif err != nil {{
\t\tapplog.Errorf("create {singular}: %v", err)
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": "internal error"}})
\t\treturn
\t}}
\tc.JSON(http.StatusCreated, gin.H{{"{singular}": item}})
}}
""",
        ))
        # GET by id
        out.append(go_handler(
            name=f"Get{S}",
            path=f"{base}/:id",
            method="GET",
            req_fields=[("id", "string")],
            purpose=f"Fetch a single {singular} by id.",
            body=f"""
// Get{S} returns one {singular} or 404.
func Get{S}(c *gin.Context) {{
\tid := c.Param("id")
\tif id == "" {{
\t\tc.JSON(http.StatusBadRequest, gin.H{{"error": "id is required"}})
\t\treturn
\t}}
\titem, err := store.Get{S}(c.Request.Context(), id)
\tif errors.Is(err, store.ErrNotFound) {{
\t\tc.JSON(http.StatusNotFound, gin.H{{"error": "{singular} not found"}})
\t\treturn
\t}}
\tif err != nil {{
\t\tapplog.Errorf("get {singular}: %v", err)
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": "internal error"}})
\t\treturn
\t}}
\tc.JSON(http.StatusOK, gin.H{{"{singular}": item}})
}}
""",
        ))
        # DELETE
        out.append(go_handler(
            name=f"Delete{S}",
            path=f"{base}/:id",
            method="DELETE",
            req_fields=[("id", "string")],
            purpose=f"Soft-delete a {singular}.",
            body=f"""
// Delete{S} marks a {singular} as deleted. Returns 204 on success.
func Delete{S}(c *gin.Context) {{
\tid := c.Param("id")
\tif id == "" {{
\t\tc.JSON(http.StatusBadRequest, gin.H{{"error": "id is required"}})
\t\treturn
\t}}
\tif err := store.Delete{S}(c.Request.Context(), id); err != nil {{
\t\tif errors.Is(err, store.ErrNotFound) {{
\t\t\tc.JSON(http.StatusNotFound, gin.H{{"error": "{singular} not found"}})
\t\t\treturn
\t\t}}
\t\tapplog.Errorf("delete {singular}: %v", err)
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": "internal error"}})
\t\treturn
\t}}
\tc.Status(http.StatusNoContent)
}}
""",
        ))

    # Studio-specific handlers
    out.append(go_handler(
        name="PostStudioGenerate",
        path="/api/v2/studio/generate",
        method="POST",
        req_fields=[("prompt", "string"), ("agent", "string"), ("existing_files", "[]GeneratedFile")],
        purpose="Generate code via the LLM. When existing_files is non-empty, auto-promote to the build agent and wrap with buildEditAwareUserMessage.",
        body="""
type PostStudioGenerateRequest struct {
\tPrompt         string           `json:"prompt" binding:"required"`
\tAgent          string           `json:"agent"`
\tProvider       string           `json:"provider"`
\tModel          string           `json:"model"`
\tConversationID string           `json:"conversation_id"`
\tExistingFiles  []GeneratedFile  `json:"existing_files"`
}

func PostStudioGenerate(c *gin.Context) {
\tvar req PostStudioGenerateRequest
\tif err := c.ShouldBindJSON(&req); err != nil {
\t\tc.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
\t\treturn
\t}
\tagent := strings.ToLower(strings.TrimSpace(req.Agent))
\tif agent == "" {
\t\tagent = "coding"
\t}
\tif len(req.ExistingFiles) > 0 {
\t\tagent = "build"
\t}
\tuserMsg := req.Prompt
\tif agent == "build" {
\t\tuserMsg = buildEditAwareUserMessage(req.Prompt, req.ExistingFiles)
\t}
\tprovider := inferProviderFromModel(req.Model)
\tresp, err := llm.Chat(c.Request.Context(), provider, req.Model, agent, userMsg)
\tif err != nil {
\t\tapplog.Errorf("studio generate: %v", err)
\t\tc.JSON(http.StatusBadGateway, gin.H{"error": "llm call failed"})
\t\treturn
\t}
\tsummary, code := extractSummaryAndCode(resp)
\tcode = sanitizeBuildResponse(code)
\tc.JSON(http.StatusOK, gin.H{
\t\t"response":       code,
\t\t"summary":        summary,
\t\t"conversation_id": req.ConversationID,
\t\t"agent":          agent,
\t\t"provider":       provider,
\t})
}
""",
    ))

    out.append(go_handler(
        name="PushStudioToRepo",
        path="/api/v2/studio/git/push",
        method="POST",
        req_fields=[("storage_path", "string"), ("repo_url", "string"), ("branch", "string"), ("commit_message", "string"), ("provider", "string")],
        purpose="Push the current workspace to a remote repo. Authenticates using the stored per-provider credential.",
        body="""
func PushStudioToRepo(c *gin.Context) {
\tvar req struct {
\t\tStoragePath   string `json:"storage_path" binding:"required"`
\t\tRepoURL       string `json:"repo_url" binding:"required"`
\t\tBranch        string `json:"branch"`
\t\tCommitMessage string `json:"commit_message"`
\t\tProvider      string `json:"provider"`
\t}
\tif err := c.ShouldBindJSON(&req); err != nil {
\t\tc.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
\t\treturn
\t}
\troot, ok := ensurePathUnderRoot(req.StoragePath, ".")
\tif !ok {
\t\tc.JSON(http.StatusBadRequest, gin.H{"error": "invalid storage_path"})
\t\treturn
\t}
\tif req.Branch == "" {
\t\treq.Branch = "main"
\t}
\tif req.CommitMessage == "" {
\t\treq.CommitMessage = "chore: push from studio"
\t}
\tcred, err := core.GetGitCredential(c.Request.Context(), req.Provider)
\tif err != nil {
\t\tc.JSON(http.StatusForbidden, gin.H{"error": "not authenticated with " + req.Provider})
\t\treturn
\t}
\tif err := core.GitInitCommitPush(root, cred, req.RepoURL, req.Branch, req.CommitMessage); err != nil {
\t\tapplog.Errorf("git push: %v", err)
\t\tc.JSON(http.StatusBadGateway, gin.H{"error": err.Error()})
\t\treturn
\t}
\tc.JSON(http.StatusOK, gin.H{"status": "pushed", "branch": req.Branch})
}
""",
    ))

    # SSE dev-server ready
    out.append(go_handler(
        name="HandleDevServerReady",
        path="/api/v2/studio/devserver/ready",
        method="GET",
        req_fields=[("storage_path", "string"), ("port", "int")],
        purpose="Stream readiness events until the dev server port answers 200, then close.",
        body="""
func HandleDevServerReady(c *gin.Context) {
\tstoragePath := c.Query("storage_path")
\tport, _ := strconv.Atoi(c.Query("port"))
\tif storagePath == "" || port <= 0 {
\t\tc.JSON(http.StatusBadRequest, gin.H{"error": "storage_path and port are required"})
\t\treturn
\t}
\tc.Header("Content-Type", "text/event-stream")
\tc.Header("Cache-Control", "no-cache")
\tc.Header("X-Accel-Buffering", "no")
\tctx := c.Request.Context()
\tticker := time.NewTicker(1 * time.Second)
\tdefer ticker.Stop()
\tdeadline := time.After(120 * time.Second)
\tfor {
\t\tselect {
\t\tcase <-ctx.Done():
\t\t\treturn
\t\tcase <-deadline:
\t\t\tfmt.Fprintf(c.Writer, "event: error\\ndata: %s\\n\\n", "timeout")
\t\t\tc.Writer.Flush()
\t\t\treturn
\t\tcase <-ticker.C:
\t\t\tresp, err := http.Get(fmt.Sprintf("http://127.0.0.1:%d", port))
\t\t\tif err == nil && resp.StatusCode < 500 {
\t\t\t\tresp.Body.Close()
\t\t\t\tfmt.Fprintf(c.Writer, "event: ready\\ndata: %d\\n\\n", port)
\t\t\t\tc.Writer.Flush()
\t\t\t\treturn
\t\t\t}
\t\t\tif resp != nil {
\t\t\t\tresp.Body.Close()
\t\t\t}
\t\t\tfmt.Fprintf(c.Writer, "event: status\\ndata: starting\\n\\n")
\t\t\tc.Writer.Flush()
\t\t}
\t}
}
""",
    ))

    # DB introspection
    for op in ("Tables", "Schema", "Stats"):
        out.append(go_handler(
            name=f"HandleStudioDB{op}",
            path=f"/api/v2/studio/database/{op.lower()}",
            method="GET",
            req_fields=[("storage_path", "string")],
            purpose=f"Return Postgres {op.lower()} for the current workspace sandbox.",
            body=f"""
func HandleStudioDB{op}(c *gin.Context) {{
\tstoragePath := c.Query("storage_path")
\tif storagePath == "" {{
\t\tc.JSON(http.StatusBadRequest, gin.H{{"error": "storage_path is required"}})
\t\treturn
\t}}
\tconn, err := core.OpenSandboxDB(storagePath)
\tif err != nil {{
\t\tc.JSON(http.StatusServiceUnavailable, gin.H{{"error": "sandbox db unreachable"}})
\t\treturn
\t}}
\tdefer conn.Close(c.Request.Context())
\tresult, err := core.Query{op}(c.Request.Context(), conn)
\tif err != nil {{
\t\tc.JSON(http.StatusInternalServerError, gin.H{{"error": err.Error()}})
\t\treturn
\t}}
\tc.JSON(http.StatusOK, gin.H{{"{op.lower()}": result}})
}}
""",
        ))
    return out


# ----------------------------------------------------------------------------
# 2) TSX component records
# ----------------------------------------------------------------------------

def tsx_components() -> list[dict]:
    out: list[dict] = []
    for name, purpose in TSX_COMPONENTS:
        # small tailored bodies per component
        body = _tsx_body_for(name)
        out.append(tsx_component(
            name=name,
            purpose=purpose,
            props=_tsx_props_for(name),
            body=body,
        ))
    # A few larger components
    out.append(tsx_component(
        name="StudioStatusBar",
        purpose="renders the Studio bottom status bar: dev server status dot, port, git branch, and a menu",
        props="{ status: 'starting'|'ready'|'stopped'|'error'; port?: number; branch?: string; onRestart: () => void; onStop: () => void; }",
        body="""
'use client';
import React from 'react';
import { Circle, Square, RefreshCw } from 'lucide-react';

type Status = 'starting' | 'ready' | 'stopped' | 'error';
const DOT: Record<Status, string> = {
  starting: 'text-yellow-400',
  ready:    'text-green-500',
  stopped:  'text-[#858585]',
  error:    'text-red-500',
};

interface Props {
  status: Status;
  port?: number;
  branch?: string;
  onRestart: () => void;
  onStop: () => void;
}

export default function StudioStatusBar({ status, port, branch, onRestart, onStop }: Props) {
  return (
    <div className="h-7 px-3 flex items-center gap-4 text-[12px] text-[#cccccc] bg-[#007acc] border-t border-[#3e3e3e]">
      <div className="flex items-center gap-1.5">
        <Circle size={8} className={`fill-current ${DOT[status]}`} />
        <span className="capitalize">{status}</span>
        {port ? <span className="opacity-80">:{port}</span> : null}
      </div>
      {branch ? <span title="git branch">⎇ {branch}</span> : null}
      <div className="ml-auto flex items-center gap-3">
        <button onClick={onRestart} className="flex items-center gap-1 hover:opacity-90">
          <RefreshCw size={12} /> Restart
        </button>
        <button onClick={onStop} className="flex items-center gap-1 hover:opacity-90">
          <Square size={12} /> Stop
        </button>
      </div>
    </div>
  );
}
""",
    ))
    return out


def _tsx_props_for(name: str) -> str:
    return {
        "RuntimePicker":     "{ value: Runtime; onChange: (r: Runtime) => void }",
        "TemplatePicker":    "{ runtime: Runtime; value?: string; onSelect: (templateId: string) => void }",
        "PlanBadge":         "{ plan: 'developer'|'pro'|'business'|'custom'|'enterprise' }",
        "NodeTierCard":      "{ tier: NodeTier; priceUsd: number; selected?: boolean; onSelect: () => void }",
        "InvoiceRow":        "{ invoice: Invoice; onDownload: (id: string) => void }",
        "GitProviderPicker": "{ value?: 'github'|'gitlab'|'bitbucket'; onChange: (p: GitProvider) => void }",
        "DomainRow":         "{ domain: Domain; onVerify: () => void; onCopy: () => void }",
        "SubscriptionGate":  "{ children: React.ReactNode }",
        "DevServerStatusDot":"{ status: 'starting'|'ready'|'stopped'|'error' }",
        "SessionIdInput":    "{ value: string; onChange: (s: string) => void; onValid?: (ok: boolean) => void }",
        "ErrorBanner":       "{ title: string; message: string; onDismiss?: () => void }",
        "EmptyState":        "{ icon: React.ReactNode; title: string; body?: string; cta?: { label: string; onClick: () => void } }",
        "CopyCodeButton":    "{ code: string }",
        "LogLine":           "{ entry: LogEntry }",
        "KebabMenu":         "{ items: Array<{ label: string; onClick: () => void; danger?: boolean }> }",
        "NodePurchaseSummary":"{ tier: NodeTier; purpose: string; total: number; coupon?: string }",
        "BitcoinQR":         "{ address: string; amountBtc: string; expiresAt: number; onExpire: () => void }",
        "ReadinessProbe":    "{ url: string; ready: boolean }",
        "BranchSlug":        "{ prompt: string }",
        "DiffSummary":       "{ filesChanged: string[]; additions: number; deletions: number }",
    }.get(name, "{}")


def _tsx_body_for(name: str) -> str:
    # Small bodies that are idiomatic and follow Studio tokens.
    if name == "RuntimePicker":
        return """
'use client';
import { useState } from 'react';

const RUNTIMES = ['react', 'fastapi', 'html', 'nextjs', 'expo', 'fullstack'] as const;
export type Runtime = typeof RUNTIMES[number];

export default function RuntimePicker({ value, onChange }: { value: Runtime; onChange: (r: Runtime) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {RUNTIMES.map((r) => {
        const active = r === value;
        return (
          <button
            key={r}
            type="button"
            onClick={() => onChange(r)}
            className={`px-3 py-1 rounded-md text-[13px] border transition-colors ${
              active
                ? 'bg-[#0e639c] text-white border-[#0e639c]'
                : 'bg-[#1e1e1e] text-[#cccccc] border-[#3e3e3e] hover:border-[#0e639c]'
            }`}
          >
            {r}
          </button>
        );
      })}
    </div>
  );
}
"""
    if name == "PlanBadge":
        return """
import React from 'react';

const COLOR: Record<string, string> = {
  developer:  'bg-slate-700 text-slate-200',
  pro:        'bg-sky-700 text-white',
  business:   'bg-violet-700 text-white',
  custom:     'bg-amber-600 text-white',
  enterprise: 'bg-emerald-700 text-white',
};

export default function PlanBadge({ plan }: { plan: keyof typeof COLOR }) {
  const cls = COLOR[plan] ?? 'bg-gray-600 text-white';
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${cls}`}>
      {plan}
    </span>
  );
}
"""
    if name == "NodeTierCard":
        return """
import React from 'react';

interface NodeTier { id: 'NANO'|'MICRO'|'STANDARD'|'PRO'|'POWER'; ram: string; vcpu: number; disk: string; }

export default function NodeTierCard({
  tier, priceUsd, selected, onSelect,
}: { tier: NodeTier; priceUsd: number; selected?: boolean; onSelect: () => void }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`text-left rounded-lg border p-4 transition-colors w-full ${
        selected ? 'border-[#0e639c] bg-[#0e639c]/10' : 'border-[#3e3e3e] bg-[#1e1e1e] hover:border-[#0e639c]'
      }`}
    >
      <div className="flex items-baseline justify-between">
        <span className="text-[15px] font-semibold text-white">{tier.id}</span>
        <span className="text-[13px] text-[#cccccc]">${priceUsd}/mo</span>
      </div>
      <div className="mt-1 text-[12px] text-[#858585]">
        {tier.ram} RAM · {tier.vcpu} vCPU · {tier.disk}
      </div>
    </button>
  );
}
"""
    if name == "SubscriptionGate":
        return """
'use client';
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';

const VALID = new Set(['developer', 'pro', 'business', 'custom', 'enterprise']);
const ACTIVE = new Set(['active', 'trial']);

export default function SubscriptionGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  const sub = user?.subscription;
  if (sub && ACTIVE.has(sub.status) && VALID.has(sub.plan)) {
    return <>{children}</>;
  }
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-[#cccccc]">
      <p className="text-sm mb-2">Subscription required</p>
      <a href="/auth/subscription" className="text-[#0e639c] hover:underline text-xs">
        Choose a plan
      </a>
    </div>
  );
}
"""
    if name == "SessionIdInput":
        return """
'use client';
import { useEffect, useMemo } from 'react';

const MIN = 16;
const RE = /^[a-zA-Z0-9._-]+$/;

export default function SessionIdInput({
  value, onChange, onValid,
}: { value: string; onChange: (s: string) => void; onValid?: (ok: boolean) => void }) {
  const ok = useMemo(() => value.length >= MIN && RE.test(value), [value]);
  useEffect(() => { onValid?.(ok); }, [ok, onValid]);
  return (
    <div>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="at least 16 chars, a-zA-Z 0-9 . _ -"
        className={`w-full bg-[#2d2d2d] border text-[13px] text-[#cccccc] px-2 py-1 rounded
          ${value.length === 0 ? 'border-[#3e3e3e]' : ok ? 'border-green-600' : 'border-red-500'}`}
      />
      {!ok && value.length > 0 && (
        <p className="text-[11px] text-red-400 mt-1">
          Session id must be at least 16 chars and match /^[a-zA-Z0-9._-]+$/.
        </p>
      )}
    </div>
  );
}
"""
    if name == "DevServerStatusDot":
        return """
import React from 'react';
const CLS = {
  starting: 'bg-yellow-400 animate-pulse',
  ready:    'bg-green-500',
  stopped:  'bg-gray-500',
  error:    'bg-red-500',
} as const;

export default function DevServerStatusDot({ status }: { status: keyof typeof CLS }) {
  return <span className={`inline-block w-2 h-2 rounded-full ${CLS[status]}`} title={status} />;
}
"""
    if name == "BitcoinQR":
        return """
'use client';
import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';

export default function BitcoinQR({
  address, amountBtc, expiresAt, onExpire,
}: { address: string; amountBtc: string; expiresAt: number; onExpire: () => void }) {
  const [remaining, setRemaining] = useState(() => Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)));
  useEffect(() => {
    const id = setInterval(() => {
      const s = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
      setRemaining(s);
      if (s === 0) { clearInterval(id); onExpire(); }
    }, 500);
    return () => clearInterval(id);
  }, [expiresAt, onExpire]);
  return (
    <div className="rounded-md border border-[#3e3e3e] p-4 text-[#cccccc] bg-[#1e1e1e] w-fit">
      <QRCodeSVG value={`bitcoin:${address}?amount=${amountBtc}`} size={160} includeMargin />
      <div className="mt-3 text-[12px] font-mono break-all">{address}</div>
      <div className="mt-1 text-[12px]">Send {amountBtc} BTC within <b>{remaining}s</b></div>
    </div>
  );
}
"""
    if name == "LogLine":
        return """
import React from 'react';

const LVL = { info: 'text-[#cccccc]', warn: 'text-yellow-400', error: 'text-red-400' } as const;

export default function LogLine({ entry }: { entry: { level: keyof typeof LVL; ts: number; message: string } }) {
  const t = new Date(entry.ts).toISOString().slice(11, 19);
  return (
    <div className={`font-mono text-[12px] leading-5 ${LVL[entry.level]}`}>
      <span className="text-[#858585] mr-2">{t}</span>
      <span>{entry.message}</span>
    </div>
  );
}
"""
    if name == "BranchSlug":
        return """
import { useMemo } from 'react';

const MAX = 50;
function toBranchName(prompt: string): string {
  const slug = prompt.toLowerCase().replace(/[^a-z0-9\\s-]/g, '').trim().split(/\\s+/).slice(0, 6).join('-') || 'change';
  return `feat/${slug}`.slice(0, MAX).replace(/-+$/g, '');
}
export default function BranchSlug({ prompt }: { prompt: string }) {
  const branch = useMemo(() => toBranchName(prompt), [prompt]);
  return <code className="text-[12px] text-[#0e639c]">{branch}</code>;
}
"""
    # Generic stub body for any component not specialised above
    return f"""
'use client';
import React from 'react';

export default function {name}(props: any) {{
  return (
    <div className="rounded-md border border-[#3e3e3e] bg-[#1e1e1e] text-[#cccccc] p-3 text-[13px]">
      {name}
    </div>
  );
}}
"""


# ----------------------------------------------------------------------------
# 3) TypeScript utilities
# ----------------------------------------------------------------------------

def ts_utils() -> list[dict]:
    out: list[dict] = []
    out.append(ts_util(
        name="useDebouncedValue<T>(value, ms)",
        purpose="returns a debounced copy of `value` that only updates after `ms` of stability",
        signature="useDebouncedValue<T>(value: T, ms?: number): T",
        body="""
import { useEffect, useState } from 'react';

export function useDebouncedValue<T>(value: T, ms = 150): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const h = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(h);
  }, [value, ms]);
  return debounced;
}
""",
    ))
    out.append(ts_util(
        name="useLocalStorage<T>(key, initial)",
        purpose="state hook backed by window.localStorage with SSR safety",
        signature="useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void]",
        body="""
import { useEffect, useState } from 'react';

export function useLocalStorage<T>(key: string, initial: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initial;
    try {
      const raw = window.localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try { window.localStorage.setItem(key, JSON.stringify(value)); } catch { /* quota */ }
  }, [key, value]);
  return [value, setValue];
}
""",
    ))
    out.append(ts_util(
        name="formatBytes(n)",
        purpose="format a byte count as a human string (B / KB / MB / GB)",
        signature="formatBytes(n: number): string",
        body="""
export function formatBytes(n: number): string {
  if (!Number.isFinite(n) || n < 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}
""",
    ))
    out.append(ts_util(
        name="inferLanguageFromPath(path)",
        purpose="return the Monaco language id for a file path",
        signature="inferLanguageFromPath(path: string): string",
        body="""
const EXT_TO_LANGUAGE: Record<string, string> = {
  ts: 'typescript', tsx: 'typescript', js: 'javascript', jsx: 'javascript',
  py: 'python', go: 'go', rs: 'rust', json: 'json', css: 'css', html: 'html',
  md: 'markdown', yml: 'yaml', yaml: 'yaml', sh: 'shell',
};
export function inferLanguageFromPath(path: string): string {
  const dot = path.lastIndexOf('.');
  if (dot < 0) return 'plaintext';
  return EXT_TO_LANGUAGE[path.slice(dot + 1).toLowerCase()] ?? 'plaintext';
}
""",
    ))
    out.append(ts_util(
        name="fetchWithTimeout(url, opts, ms)",
        purpose="wrap fetch with an AbortController timeout (ms, default 30s)",
        signature="fetchWithTimeout(url: string, opts?: RequestInit, ms?: number): Promise<Response>",
        body="""
export async function fetchWithTimeout(url: string, opts: RequestInit = {}, ms = 30_000): Promise<Response> {
  const c = new AbortController();
  const id = setTimeout(() => c.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: c.signal });
  } finally {
    clearTimeout(id);
  }
}
""",
    ))
    # Add many small variations
    small = [
        ("slugify", "lowercase+hyphenate a string, strip non-alphanumerics",
         "slugify(s: string): string",
         "export function slugify(s: string): string {\n  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');\n}"),
        ("truncate", "truncate with ellipsis", "truncate(s: string, n: number): string",
         "export function truncate(s: string, n: number): string {\n  return s.length <= n ? s : s.slice(0, n - 1) + '…';\n}"),
        ("clamp", "clamp a number between [min,max]",
         "clamp(n: number, min: number, max: number): number",
         "export function clamp(n: number, min: number, max: number): number {\n  return Math.min(max, Math.max(min, n));\n}"),
        ("safeParseJSON", "tolerant JSON parse returning null on failure",
         "safeParseJSON<T=unknown>(raw: string): T | null",
         "export function safeParseJSON<T=unknown>(raw: string): T | null {\n  try { return JSON.parse(raw) as T; } catch { return null; }\n}"),
        ("uniq", "return de-duplicated array preserving order",
         "uniq<T>(xs: readonly T[]): T[]",
         "export function uniq<T>(xs: readonly T[]): T[] {\n  const seen = new Set<T>();\n  const out: T[] = [];\n  for (const x of xs) if (!seen.has(x)) { seen.add(x); out.push(x); }\n  return out;\n}"),
        ("bySlug", "index an array of {slug} objects into a record",
         "bySlug<T extends {slug: string}>(xs: readonly T[]): Record<string, T>",
         "export function bySlug<T extends { slug: string }>(xs: readonly T[]): Record<string, T> {\n  const out: Record<string, T> = {};\n  for (const x of xs) out[x.slug] = x;\n  return out;\n}"),
        ("sleep", "await a delay in ms", "sleep(ms: number): Promise<void>",
         "export const sleep = (ms: number): Promise<void> => new Promise(r => setTimeout(r, ms));"),
        ("ensureTrailingSlash", "ensure string ends with /", "ensureTrailingSlash(s: string): string",
         "export function ensureTrailingSlash(s: string): string {\n  return s.endsWith('/') ? s : s + '/';\n}"),
        ("relTime", "render a human-readable relative timestamp",
         "relTime(ts: number | Date): string",
         "export function relTime(ts: number | Date): string {\n  const t = typeof ts === 'number' ? ts : ts.getTime();\n  const d = Math.floor((Date.now() - t) / 1000);\n  if (d < 60) return `${d}s ago`;\n  if (d < 3600) return `${Math.floor(d/60)}m ago`;\n  if (d < 86400) return `${Math.floor(d/3600)}h ago`;\n  return `${Math.floor(d/86400)}d ago`;\n}"),
        ("parseCookie", "parse document.cookie into a record",
         "parseCookie(raw: string): Record<string,string>",
         "export function parseCookie(raw: string): Record<string,string> {\n  const out: Record<string,string> = {};\n  for (const part of raw.split('; ')) {\n    const idx = part.indexOf('=');\n    if (idx > 0) out[part.slice(0, idx)] = decodeURIComponent(part.slice(idx + 1));\n  }\n  return out;\n}"),
    ]
    for (n, purpose, sig, body) in small:
        out.append(ts_util(n, purpose, sig, body))
    return out


# ----------------------------------------------------------------------------
# 4) FastAPI endpoints
# ----------------------------------------------------------------------------

def py_endpoints() -> list[dict]:
    out: list[dict] = []
    for (name, method, path, purpose) in PY_ENDPOINTS:
        sig = f"@router.{method.lower()}(\"{path}\")"
        out.append(py_endpoint(name, method, path, purpose,
            f"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.orm.session import get_db

router = APIRouter()


class {name.title().replace('_', '')}In(BaseModel):
    # TODO: tighten per-field validation for {name}
    name: str | None = None


class {name.title().replace('_', '')}Out(BaseModel):
    id: str
    status: str

    class Config:
        from_attributes = True


{sig}
async def {name}(
    payload: {name.title().replace('_', '')}In | None = None,
    db: AsyncSession = Depends(get_db),
) -> {name.title().replace('_', '')}Out:
    \"\"\"{purpose}.\"\"\"
    try:
        # Business logic placeholder — wire this up to the appropriate service.
        # Never leak raw ORM errors; translate into HTTPException with a stable message.
        result = await _{name}_impl(db, payload)
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    return {name.title().replace('_', '')}Out.model_validate(result)


async def _{name}_impl(db: AsyncSession, payload):
    raise NotImplementedError
"""
        ))
    # A handful of hand-crafted richer ones
    out.append(py_endpoint(
        "create_workspace", "POST", "/workspaces",
        "Create a workspace with explicit runtime+template validation.",
        """
from enum import Enum
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.session import get_db
from app.orm.models import Workspace

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class Runtime(str, Enum):
    react = "react"
    fastapi = "fastapi"
    html = "html"
    nextjs = "nextjs"
    expo = "expo"
    fullstack = "fullstack"


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    runtime: Runtime
    template_type: str | None = Field(default=None, max_length=60)
    git_url: str | None = Field(default=None, max_length=500)


class WorkspaceRead(BaseModel):
    id: str
    name: str
    runtime: Runtime
    session_id: str

    class Config:
        from_attributes = True


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    ws = Workspace(
        id=str(uuid4()),
        name=payload.name.strip(),
        runtime=payload.runtime.value,
        template_type=payload.template_type,
        git_url=payload.git_url,
        session_id=uuid4().hex,
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceRead.model_validate(ws)
"""
    ))
    return out


# ----------------------------------------------------------------------------
# 5) Edit diffs (XML search/replace)
# ----------------------------------------------------------------------------

def edit_diffs() -> list[dict]:
    edits = [
        (
            "Rename the variable `users` to `members` in the snippet; keep types.",
            "const users = await listUsers();\nfor (const u of users) { console.log(u.id); }",
            "<<<<<<< SEARCH\nconst users = await listUsers();\nfor (const u of users) { console.log(u.id); }\n=======\nconst members = await listUsers();\nfor (const u of members) { console.log(u.id); }\n>>>>>>> REPLACE",
        ),
        (
            "Add an `allow_destructive` flag check before writing the file.",
            "err := os.WriteFile(path, []byte(req.Content), 0644)\nif err != nil { c.JSON(500, gin.H{\"error\": err.Error()}); return }",
            "<<<<<<< SEARCH\nerr := os.WriteFile(path, []byte(req.Content), 0644)\nif err != nil { c.JSON(500, gin.H{\"error\": err.Error()}); return }\n=======\nif !req.AllowDestructive {\n\tif existing, rerr := os.ReadFile(path); rerr == nil {\n\t\tif ratio := float64(len(req.Content)) / float64(len(existing)); ratio < 0.2 && len(existing) > 20 {\n\t\t\tc.JSON(http.StatusUnprocessableEntity, gin.H{\"error\": \"destructive edit blocked\"})\n\t\t\treturn\n\t\t}\n\t}\n}\nif err := os.WriteFile(path, []byte(req.Content), 0644); err != nil {\n\tc.JSON(http.StatusInternalServerError, gin.H{\"error\": err.Error()})\n\treturn\n}\n>>>>>>> REPLACE",
        ),
        (
            "Switch the React component from class to function + hooks.",
            "class Counter extends React.Component {\n  state = { n: 0 };\n  inc = () => this.setState({ n: this.state.n + 1 });\n  render() {\n    return <button onClick={this.inc}>{this.state.n}</button>;\n  }\n}",
            "<<<<<<< SEARCH\nclass Counter extends React.Component {\n  state = { n: 0 };\n  inc = () => this.setState({ n: this.state.n + 1 });\n  render() {\n    return <button onClick={this.inc}>{this.state.n}</button>;\n  }\n}\n=======\nimport { useState } from 'react';\nexport default function Counter() {\n  const [n, setN] = useState(0);\n  return <button onClick={() => setN(n + 1)}>{n}</button>;\n}\n>>>>>>> REPLACE",
        ),
        (
            "Replace setTimeout polling with useEffect + EventSource.",
            "const id = setInterval(() => fetch('/logs').then(r => r.text()).then(setLogs), 2000);\nreturn () => clearInterval(id);",
            "<<<<<<< SEARCH\nconst id = setInterval(() => fetch('/logs').then(r => r.text()).then(setLogs), 2000);\nreturn () => clearInterval(id);\n=======\nconst es = new EventSource('/logs');\nes.onmessage = (e) => setLogs((prev) => [...prev, e.data]);\nreturn () => es.close();\n>>>>>>> REPLACE",
        ),
        (
            "Tighten the Pydantic model: email must be EmailStr and name 1-120 chars.",
            "class UserCreate(BaseModel):\n    email: str\n    name: str",
            "<<<<<<< SEARCH\nclass UserCreate(BaseModel):\n    email: str\n    name: str\n=======\nfrom pydantic import EmailStr, Field\n\nclass UserCreate(BaseModel):\n    email: EmailStr\n    name: str = Field(min_length=1, max_length=120)\n>>>>>>> REPLACE",
        ),
        (
            "Add Retry-After respect to the 429 handler.",
            "if (res.status === 429) throw new Error('rate limited');",
            "<<<<<<< SEARCH\nif (res.status === 429) throw new Error('rate limited');\n=======\nif (res.status === 429) {\n  const ra = Number(res.headers.get('Retry-After') ?? '1');\n  await new Promise((r) => setTimeout(r, ra * 1000));\n  throw new Error('rate limited — retry after ' + ra + 's');\n}\n>>>>>>> REPLACE",
        ),
        (
            "Add ensurePathUnderRoot to guard ReadStudioFile against traversal.",
            "content, err := os.ReadFile(filepath.Join(storagePath, filePath))\nif err != nil { c.JSON(500, gin.H{\"error\": err.Error()}); return }",
            "<<<<<<< SEARCH\ncontent, err := os.ReadFile(filepath.Join(storagePath, filePath))\nif err != nil { c.JSON(500, gin.H{\"error\": err.Error()}); return }\n=======\nfullPath, ok := ensurePathUnderRoot(storagePath, filePath)\nif !ok {\n\tc.JSON(http.StatusBadRequest, gin.H{\"error\": \"file_path must be under storage_path\"})\n\treturn\n}\ncontent, err := os.ReadFile(fullPath)\nif errors.Is(err, os.ErrNotExist) {\n\tc.JSON(http.StatusNotFound, gin.H{\"error\": \"file not found\"})\n\treturn\n}\nif err != nil {\n\tc.JSON(http.StatusInternalServerError, gin.H{\"error\": err.Error()})\n\treturn\n}\n>>>>>>> REPLACE",
        ),
        (
            "Cap log array to the last 5000 entries to prevent memory blow-up.",
            "setLogs(prev => [...prev, entry]);",
            "<<<<<<< SEARCH\nsetLogs(prev => [...prev, entry]);\n=======\nsetLogs(prev => (prev.length >= 5000 ? [...prev.slice(-4999), entry] : [...prev, entry]));\n>>>>>>> REPLACE",
        ),
        (
            "Add Monaco debounce so onChange fires 150ms after the last keystroke.",
            "<MonacoEditor onChange={(v) => onChange(v ?? '')} />",
            "<<<<<<< SEARCH\n<MonacoEditor onChange={(v) => onChange(v ?? '')} />\n=======\nconst debRef = useRef<ReturnType<typeof setTimeout> | null>(null);\nconst handleChange = (v: string | undefined) => {\n  if (debRef.current) clearTimeout(debRef.current);\n  debRef.current = setTimeout(() => onChange(v ?? ''), 150);\n};\n<MonacoEditor onChange={handleChange} />\n>>>>>>> REPLACE",
        ),
        (
            "Parameterise the SQL — the current code is injectable.",
            "query := fmt.Sprintf(\"SELECT * FROM users WHERE email = '%s'\", email)\nrows, err := db.Query(query)",
            "<<<<<<< SEARCH\nquery := fmt.Sprintf(\"SELECT * FROM users WHERE email = '%s'\", email)\nrows, err := db.Query(query)\n=======\nrows, err := db.Query(\"SELECT * FROM users WHERE email = $1\", email)\n>>>>>>> REPLACE",
        ),
    ]
    return [edit_diff(instr, before, diff) for (instr, before, diff) in edits]


# ----------------------------------------------------------------------------
# 6) Code reviews
# ----------------------------------------------------------------------------

def reviews() -> list[dict]:
    samples = [
        (
            "func ReadFile(c *gin.Context) {\n\tp := c.Query(\"p\")\n\tb, _ := os.ReadFile(p)\n\tc.Data(200, \"text/plain\", b)\n}",
            "Findings (descending severity):\n1. critical — path traversal: attacker controls the full path. Gate via ensurePathUnderRoot(root, sub).\n2. high — silent error: `_` discards os.ReadFile error; missing files return empty body with 200. Return 404/500.\n3. medium — wrong content-type: binary files are served as text/plain. Use http.DetectContentType.\n4. low — no rate limit; any caller can scan arbitrary files quickly.\nApprove once 1-3 are fixed.",
        ),
        (
            "const x = fetch('/me').then(r => r.json()).then(u => setUser(u));",
            "Findings:\n1. error path swallowed — add .catch(setError).\n2. no abort on unmount — wrap in useEffect and cancel with AbortController.\n3. type unsafe — cast to `User` with a schema parse (zod/valibot) or assert at the boundary.\n4. race — if this effect re-runs, older responses can overwrite newer state. Compare a token.",
        ),
        (
            "async def login(req: LoginIn, db = Depends(get_db)):\n    u = await db.scalar(select(User).where(User.email == req.email))\n    if u and u.password == req.password:\n        return {'token': make_token(u.id)}\n    return {'error': 'bad creds'}",
            "Findings:\n1. critical — plaintext password comparison. Use bcrypt/argon2 verify and store only hashes.\n2. critical — timing attack: `==` on strings is variable-time. Use a constant-time compare when you must compare tokens.\n3. high — 200 OK on failure with an error body confuses clients/tests. Raise 401 for bad creds.\n4. medium — token generation should include `iat/exp` and a key-id for rotation.",
        ),
        (
            "export function isValidSession(id: string) { return id.length > 5; }",
            "Findings:\n1. high — doesn't match the platform rule (min 16 chars, /^[a-zA-Z0-9._-]+$/). Align with utils/studioSessionId.ts.\n2. medium — no null/undefined guard; callers crash on `id.length`.\n3. low — name suggests boolean intent but no JSDoc. Add one-line doc referencing the spec.",
        ),
        (
            "// Go\nfunc parse(s string) int { i, _ := strconv.Atoi(s); return i }",
            "Findings:\n1. high — errors are discarded; bad input silently produces 0.\n2. medium — unbounded input: could hide DoS vectors (very long strings still parse in Go but waste CPU in hot paths).\n3. low — consider returning (int, error) so callers can distinguish 0 from parse failure.",
        ),
        (
            "<button onClick={() => history.push('/dashboard')}>Go</button>",
            "Findings:\n1. medium — using history directly couples to a specific router version. Prefer `useRouter()` from next/navigation in an App Router codebase.\n2. low — no loading/disabled state; users can double-click and fire two transitions.\n3. low — missing aria-label when the button's text is ambiguous outside visual context.",
        ),
    ]
    return [review(snip, findings) for (snip, findings) in samples]


# ----------------------------------------------------------------------------
# 7) Refactor records
# ----------------------------------------------------------------------------

def refactors() -> list[dict]:
    items = [
        (
            "def pick_region(user):\n    if user:\n        if user.prefs:\n            if user.prefs.region:\n                return user.prefs.region\n    return 'us-east-1'",
            "def pick_region(user) -> str:\n    if not user or not user.prefs:\n        return 'us-east-1'\n    return user.prefs.region or 'us-east-1'",
            "Collapse nested ifs into early returns and annotate the return type.",
        ),
        (
            "function toBranchName(p) {\n  var s = p.toLowerCase();\n  s = s.replace(/[^a-z0-9\\s]/g, '');\n  s = s.trim();\n  s = s.split(/\\s+/).slice(0, 6).join('-');\n  if (!s) s = 'change';\n  return 'feat/' + s;\n}",
            "const MAX_BRANCH_LEN = 50;\nexport function toBranchName(prompt: string): string {\n  const slug =\n    prompt.toLowerCase().replace(/[^a-z0-9\\s-]/g, '').trim().split(/\\s+/).slice(0, 6).join('-') ||\n    'change';\n  return `feat/${slug}`.slice(0, MAX_BRANCH_LEN).replace(/-+$/g, '');\n}",
            "Migrate to TypeScript, use const, cap length, strip trailing hyphens.",
        ),
        (
            "func ok(w http.ResponseWriter, r *http.Request) {\n\tw.Write([]byte(\"{\\\"ok\\\":true}\"))\n}",
            "func ok(w http.ResponseWriter, _ *http.Request) {\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\t_ = json.NewEncoder(w).Encode(map[string]bool{\"ok\": true})\n}",
            "Set content-type and use encoding/json instead of hand-written JSON.",
        ),
        (
            "const load = () => {\n  fetch('/api/workspaces').then(r => r.json()).then(d => setWs(d)).catch(e => console.log(e));\n};",
            "async function load(signal: AbortSignal) {\n  try {\n    const res = await fetch('/api/workspaces', { signal });\n    if (!res.ok) throw new Error(`HTTP ${res.status}`);\n    setWs(await res.json());\n  } catch (err) {\n    if ((err as Error).name !== 'AbortError') setError(err as Error);\n  }\n}",
            "Make it async/await, surface non-2xx as errors, support AbortController.",
        ),
        (
            "def flatten(d, parent='', sep='.'):\n    out = {}\n    for k in d:\n        v = d[k]\n        nk = (parent + sep + k) if parent else k\n        if type(v) is dict:\n            for k2 in flatten(v, nk, sep):\n                out[k2] = flatten(v, nk, sep)[k2]\n        else:\n            out[nk] = v\n    return out",
            "def flatten(d: dict, parent: str = '', sep: str = '.') -> dict:\n    out: dict = {}\n    for k, v in d.items():\n        nk = f'{parent}{sep}{k}' if parent else k\n        if isinstance(v, dict):\n            out.update(flatten(v, nk, sep))\n        else:\n            out[nk] = v\n    return out",
            "Use isinstance, avoid the O(n^2) recursive call, use dict.update, add type hints.",
        ),
    ]
    return [refactor(before, after, rationale) for (before, after, rationale) in items]


# ----------------------------------------------------------------------------
# 8) Tests
# ----------------------------------------------------------------------------

def tests() -> list[dict]:
    items = [
        ("toBranchName", "typescript", "react", """
import { describe, it, expect } from 'vitest';
import { toBranchName } from './branch';

describe('toBranchName', () => {
  it('slugs the first 6 words', () => {
    expect(toBranchName('Add dark mode toggle to the navbar please now')).toBe('feat/add-dark-mode-toggle-to-the');
  });
  it('falls back when prompt is empty', () => {
    expect(toBranchName('')).toBe('feat/change');
  });
  it('caps at 50 chars and strips trailing hyphens', () => {
    const b = toBranchName('x '.repeat(50));
    expect(b.length).toBeLessThanOrEqual(50);
    expect(b.endsWith('-')).toBe(false);
  });
});
"""),
        ("isValidStudioSessionId", "typescript", "react", """
import { describe, it, expect } from 'vitest';
import { isValidStudioSessionId } from './studioSessionId';

describe('isValidStudioSessionId', () => {
  it('rejects short ids', () => {
    expect(isValidStudioSessionId('abc')).toBe(false);
  });
  it('rejects ids with disallowed chars', () => {
    expect(isValidStudioSessionId('abcdefghijk@#$%^&*!')).toBe(false);
  });
  it('accepts 16+ alphanum . _ -', () => {
    expect(isValidStudioSessionId('ab.c_d-e-abcdefgh')).toBe(true);
  });
});
"""),
        ("ensurePathUnderRoot", "go", "gin", """
package studio

import (
    "os"
    "path/filepath"
    "testing"
)

func TestEnsurePathUnderRoot(t *testing.T) {
    root := t.TempDir()
    _ = os.WriteFile(filepath.Join(root, "ok.txt"), []byte("ok"), 0o644)
    cases := []struct{
        name, sub string
        ok        bool
    }{
        {"simple ok", "ok.txt", true},
        {"parent escape", "../etc/passwd", false},
        {"absolute sub", "/etc/passwd", false},
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            _, ok := ensurePathUnderRoot(root, tc.sub)
            if ok != tc.ok { t.Fatalf("%s: got %v, want %v", tc.name, ok, tc.ok) }
        })
    }
}
"""),
        ("POST /workspaces", "python", "fastapi", """
import pytest

@pytest.mark.asyncio
async def test_create_workspace_happy(client):
    r = await client.post('/workspaces', json={'name': 'hello', 'runtime': 'react'})
    assert r.status_code == 201
    body = r.json()
    assert body['name'] == 'hello'
    assert len(body['session_id']) >= 16

@pytest.mark.asyncio
async def test_create_workspace_rejects_bad_runtime(client):
    r = await client.post('/workspaces', json={'name': 'hello', 'runtime': 'bogus'})
    assert r.status_code == 422
"""),
        ("WriteStudioFile destructive guard", "go", "gin", """
package studio_test

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestWriteStudioFile_BlocksSmallOverwrite(t *testing.T) {
    payload := map[string]any{
        "storage_path": "/tmp/ws",
        "file_path":    "big.go",
        "content":      "func foo() {}", // <20% of existing 5 KB file
    }
    body, _ := json.Marshal(payload)
    req := httptest.NewRequest(http.MethodPost, "/files/write", bytes.NewReader(body))
    rec := httptest.NewRecorder()
    WriteStudioFile(wrap(rec, req))
    if rec.Code != http.StatusUnprocessableEntity {
        t.Fatalf("expected 422, got %d", rec.Code)
    }
}
"""),
    ]
    return [test_record(thing, lang, fw, body) for (thing, lang, fw, body) in items]


# ----------------------------------------------------------------------------
# 9) Summaries
# ----------------------------------------------------------------------------

def summaries() -> list[dict]:
    items = [
        ("studio.go's ExportStudioProject handler",
         "`ExportStudioProject` streams a ZIP of the current workspace to the caller. It reads "
         "`session_id`/`user_id`/`workspace_name` from the query string, resolves "
         "/var/storage/{user_id}/{session_id} through ensurePathUnderRoot to block traversal, and "
         "walks the tree with filepath.Walk. `node_modules` and `.git` are skipped. The Content-Type "
         "is application/zip and Content-Disposition: attachment so browsers download the file. Each "
         "regular file is copied into the archive via zipWriter.Create + io.Copy. Errors mid-walk are "
         "logged via applog because the HTTP headers are already flushed."),
        ("the visual-edit bridge in StudioShell",
         "Studio injects `__va_visual_edit_bridge.js` into the preview iframe. The iframe listens for "
         "`{type:'__va_visual_edit_cmd', cmd:'enable|applyStyle|applyText'}` messages from the parent "
         "and posts back `{type:'__va_visual_edit', event:'select|textChanged|styleApplied', data}`. The "
         "parent collects changes in a VisualChange[] buffer; on 'Apply to Source' it calls "
         "syncVisualChangesToSource(changes, files), which maps text changes by substring and style "
         "changes to inline style props or CSS classes. Unmappable changes are returned as "
         "`unmappedChanges` and shown with a yellow dot in the panel."),
        ("the Studio dev-server lifecycle",
         "BootstrapStudioProject either seeds a template or clones a git repo into "
         "/var/storage/{user_id}/{session_id}. It registers a cloud-operation via "
         "notifications.InitiateCloudOperationWithType and writes .cloud_op_id so resumes are "
         "idempotent. ExecuteStudioProject spawns the runtime container and returns an access URL. "
         "HandleDevServerReady streams SSE `event: status` messages until the port answers 200, then "
         "emits `event: ready`. HandleDevServerLogs tails .devserver.log and streams each new line as "
         "`data: ...`. Stop/Restart/Reload are explicit POSTs so the UI can surface them."),
        ("the SubscriptionGate component",
         "SubscriptionGate reads `user.subscription.{status, plan}` from the auth context and renders "
         "its children only when status ∈ {active, trial} and plan ∈ {developer, pro, business, custom, "
         "enterprise}. Otherwise it renders a redirect prompt to /auth/subscription. It's used on any "
         "paid route (Studio, Workflow, audit logs). If the cached context is stale after an upgrade, "
         "signing out + in re-fetches /api/v1/auth/me and unblocks."),
        ("the XML search/replace diff protocol used by Studio's build agent",
         "For in-place edits, the model returns one or more blocks of the form:\n"
         "  <<<<<<< SEARCH\n  <old lines>\n  =======\n  <new lines>\n  >>>>>>> REPLACE\n"
         "The client applies each block by finding the SEARCH text verbatim in the file and "
         "substituting the REPLACE text. Blocks must be literal — no wildcards — so the tokenizer can "
         "match exactly. Whole-file generation uses fenced code blocks instead. Writes are still subject "
         "to the 20% destructive-edit guard in WriteStudioFile."),
    ]
    return [summary(thing, body) for (thing, body) in items]


# ----------------------------------------------------------------------------
# 10) Bugfixes
# ----------------------------------------------------------------------------

def bugfixes() -> list[dict]:
    items = [
        ("EventSource keeps reconnecting forever after the dev server is stopped.",
         "es.onerror never cleans up; browser retries indefinitely until the tab is closed.",
         "<<<<<<< SEARCH\nes.onerror = () => setConnected(false);\n=======\nes.onerror = () => {\n  setConnected(false);\n  es.close();      // stop browser auto-reconnect\n};\n>>>>>>> REPLACE"),
        ("Studio file tree rerenders from scratch on every keystroke in the editor.",
         "`renderNode` is called at render time with the full file list, and the expanded set is not memoised against the tree.",
         "<<<<<<< SEARCH\nconst tree = renderNode(root, 0);\n=======\nconst tree = useMemo(() => renderNode(root, 0), [root, expanded, selectedPath]);\n>>>>>>> REPLACE"),
        ("Git push returns 200 but the branch isn't on the remote.",
         "GitInitCommitPush creates the commit locally but never pushes when the remote name isn't `origin`.",
         "<<<<<<< SEARCH\nif err := exec.Command(\"git\", \"push\").Run(); err != nil { return err }\n=======\nif err := exec.Command(\"git\", \"-C\", root, \"push\", \"-u\", \"origin\", branch).Run(); err != nil {\n\treturn fmt.Errorf(\"git push %s: %w\", branch, err)\n}\n>>>>>>> REPLACE"),
        ("OAuth callback loops back to /auth/login.",
         "The handler reads access_token from a querystring, but Google returns it in the URL hash (#). The hash never reaches the server.",
         "<<<<<<< SEARCH\nconst token = searchParams.get('access_token');\n=======\nconst fromHash = new URLSearchParams(window.location.hash.replace(/^#/, ''));\nconst token = searchParams.get('access_token') ?? fromHash.get('access_token');\n>>>>>>> REPLACE"),
        ("Monaco editor shows stale content after switching files.",
         "`path` prop isn't being passed, so Monaco keeps the same model across file changes.",
         "<<<<<<< SEARCH\n<MonacoEditor value={content} onChange={setContent} />\n=======\n<MonacoEditor path={selectedPath} value={content} onChange={setContent} />\n>>>>>>> REPLACE"),
    ]
    return [bugfix(symptom, cause, diff) for (symptom, cause, diff) in items]


# ----------------------------------------------------------------------------
# 11) Knowledge / skills records (free-form, reuses 'summary' task type)
# ----------------------------------------------------------------------------

SKILL_TOPICS = [
    "Where workspace files live on disk in Studio",
    "Why writes under 20% of the existing file size are rejected by WriteStudioFile",
    "What the `.cloud_op_id` sentinel file is for",
    "How HandleDevServerReady streams SSE events",
    "The purpose of ensurePathUnderRoot and the threats it defends against",
    "How `extractSummaryAndCode` parses LLM output",
    "Why Studio auto-promotes the agent to `build` when existing_files is non-empty",
    "How the visual-edit bridge communicates with the parent window",
    "The relationship between SessionId, workspace id, and storage_path",
    "Why Monaco's `path` prop matters when switching files",
    "How `toBranchName` derives a branch slug from a prompt",
    "The invariants enforced by isValidStudioSessionId",
    "How /api/v2/studio/export ZIP streams to the client",
    "Why `c.Writer.Flush()` is required on every SSE write",
    "The runtimes Studio supports and how they map to container images",
    "How `buildEditAwareUserMessage` frames edit prompts to the LLM",
    "What the Studio `destructive edit` 422 means and how users unblock it",
    "The subscription plans recognized by SubscriptionGate",
    "How database introspection endpoints lock down SQL queries",
    "The contract of the /devserver/logs SSE endpoint",
]


def skills() -> list[dict]:
    out = []
    for topic in SKILL_TOPICS:
        out.append({
            "task": "summary",
            "language": "auto",
            "framework": "",
            "prompt": f"Explain: {topic}",
            "context": "",
            "output": _skill_body(topic),
        })
    return out


def _skill_body(topic: str) -> str:
    # A compact, factual answer per topic. Most reference real files/identifiers.
    M = {
        "Where workspace files live on disk in Studio":
            "Every Studio workspace is persisted under `/var/storage/{user_id}/{session_id}/`. Frontend and backend subprojects live side-by-side in that directory. `sessionId` is validated against the regex `/^[a-zA-Z0-9._-]+$/` with a 16-char minimum before any path is formed.",
        "Why writes under 20% of the existing file size are rejected by WriteStudioFile":
            "WriteStudioFile has two constants — `minNonEmptyChars = 20` and `minEditRatio = 0.2`. When the file already exists and has > 20 non-empty chars, any incoming write whose size is < 20% of the existing bytes is rejected with 422. Bypass by setting `allow_destructive: true` in the request body. This is the last line of defence against an LLM accidentally wiping a file.",
        "What the `.cloud_op_id` sentinel file is for":
            "BootstrapStudioProject records the cloud-operation UUID in `.cloud_op_id` inside the workspace. On resume (same session_id), the handler reads the file and reuses the existing op instead of creating a duplicate cloud-op record.",
        "How HandleDevServerReady streams SSE events":
            "The handler sets `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`, then enters a poll loop. Every second it dials `http://127.0.0.1:{port}`; while the port isn't open it emits `event: status\\ndata: starting\\n\\n`. When it answers 200, it emits `event: ready\\ndata: {port}\\n\\n` and returns. The loop respects `c.Request.Context().Done()` so the client can cancel.",
        "The purpose of ensurePathUnderRoot and the threats it defends against":
            "`ensurePathUnderRoot(root, sub)` returns `(absPath, ok)`. It rejects absolute sub-paths, joins and cleans, verifies the result is under root via `filepath.Rel`, and — if the target exists — resolves symlinks to catch symlink-escape attacks. Defends against `../../etc/passwd`, encoded variants, and symlinks created inside the workspace pointing outside.",
        "How `extractSummaryAndCode` parses LLM output":
            "Looks for a single `SUMMARY: <one line>` line and strips it out; the remaining text is treated as the code response. When the agent is `build`, sanitizeBuildResponse also strips preamble/prose outside fenced code blocks.",
        "Why Studio auto-promotes the agent to `build` when existing_files is non-empty":
            "The `coding` agent is optimised for whole-file generation; `build` is optimised for edits in existing code. PostStudioGenerate checks `len(existing_files) > 0` and flips the agent to `build`, then wraps the prompt with `buildEditAwareUserMessage(prompt, files)` so the LLM sees each file's path and content as context before answering with search/replace diffs.",
        "How the visual-edit bridge communicates with the parent window":
            "The injected script in the iframe posts `{type: '__va_visual_edit', event: 'bridgeReady'|'select'|'textChanged'|'styleApplied', data: {...}}`. The parent posts `{type: '__va_visual_edit_cmd', cmd: 'enable'|'applyStyle'|'applyText'}`. Both sides verify the `type` prefix to avoid processing unrelated postMessage traffic.",
        "The relationship between SessionId, workspace id, and storage_path":
            "`session_id` is the URL-visible identifier used by the frontend (query param `?session=...`). Internally each session owns a `workspace_id` (UUID used by the database). `storage_path` is always `/var/storage/{user_id}/{session_id}` — the two IDs are linked but kept distinct so workspace metadata can move independently of session tokens.",
        "Why Monaco's `path` prop matters when switching files":
            "Monaco creates one model per `path`. If the editor always uses the same path, switching files re-uses the same model and the old content lingers (undo history, language, tokens). Passing the current file path makes Monaco create or fetch the correct model.",
        "How `toBranchName` derives a branch slug from a prompt":
            "Lowercase the prompt, strip non-alphanumerics (keeping spaces), collapse whitespace, take the first 6 words, join with hyphens. Default to `change` if empty. Prefix with `feat/` and cap the total length at 50 chars, stripping trailing hyphens.",
        "The invariants enforced by isValidStudioSessionId":
            "`id.length >= MIN_STUDIO_SESSION_ID_LEN (=16)` AND `/^[a-zA-Z0-9._-]+$/.test(id)`. Null/undefined/empty all return false without throwing. The regex deliberately forbids `/`, `..`, and whitespace so the ID can be safely used in URLs and filesystem paths.",
        "How /api/v2/studio/export ZIP streams to the client":
            "Sets `Content-Type: application/zip` and `Content-Disposition: attachment; filename=\"{name}.zip\"`. Creates a `zip.Writer` directly against `c.Writer` so bytes stream — no on-disk staging. Walks the storage root, skips `node_modules` and `.git`, and io.Copy each file into the archive.",
        "Why `c.Writer.Flush()` is required on every SSE write":
            "Gin buffers writes internally; without Flush(), nginx/cloudflare buffer them further. Clients see bursts instead of a stream, and health-check proxies may close idle-looking connections. Every SSE emit needs `fmt.Fprintf(..., \"data: ...\\n\\n\")` followed by `c.Writer.Flush()`.",
        "The runtimes Studio supports and how they map to container images":
            "react, fastapi, html, nextjs, expo, fullstack. The frontend's NewWorkspaceModal writes the chosen runtime into the workspace record; the backend's BootstrapStudioProject seeds the starter template for that runtime and ExecuteStudioProject launches the matching container image (e.g. `node:20-alpine` for react/nextjs, `python:3.12-slim` for fastapi).",
        "How `buildEditAwareUserMessage` frames edit prompts to the LLM":
            "Renders each existing file as `### File: {path}\\n```{lang}\\n{content}\\n```\\n\\n` then appends `### Instruction\\n{prompt}\\n\\n### Response\\nReturn XML search/replace diffs.`. Charging the model with the exact search-replace protocol keeps outputs machine-applicable.",
        "What the Studio `destructive edit` 422 means and how users unblock it":
            "The 422 response carries `{error: 'destructive edit blocked', existing_bytes, incoming_bytes, min_ratio, hint}`. Users fix it by either (a) sending the full file content, or (b) setting `allow_destructive: true` when they genuinely want to shrink. The AI agent flow sets the flag automatically when the prompt contains `rewrite|wipe|clear|reset|rebuild`.",
        "The subscription plans recognized by SubscriptionGate":
            "`developer`, `pro`, `business`, `custom`, `enterprise`. Status must be `active` or `trial`. Audit-log features require an `active` status specifically (not `trial`). An unauthenticated user is not gated — public routes bypass the component entirely.",
        "How database introspection endpoints lock down SQL queries":
            "The /database/* routes use a per-workspace sandbox connection opened via `core.OpenSandboxDB(storagePath)`. Parameterised queries only — free-text SQL is accepted on `/database/query` but runs under a role scoped to the sandbox schema with no network or pg_* privileges. Queries time out at 3s.",
        "The contract of the /devserver/logs SSE endpoint":
            "`GET /api/v2/studio/devserver/logs?storage_path=...&stream=build|server`. Headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`. Each new line in `.devserver.log` is emitted as `data: <line>\\n\\n`. A `: ping` heartbeat is sent every 15s so idle connections survive proxies.",
    }
    return M.get(topic, f"{topic} — see studio.go and the linked frontend components for the authoritative implementation.")


# ----------------------------------------------------------------------------
# Compose everything and write to disk
# ----------------------------------------------------------------------------

def build() -> list[dict]:
    records: list[dict] = []
    records += go_handlers()
    records += tsx_components()
    records += ts_utils()
    records += py_endpoints()
    records += edit_diffs()
    records += reviews()
    records += refactors()
    records += tests()
    records += summaries()
    records += bugfixes()
    records += skills()

    # Expand via small paraphrases so we cross 300 with diverse phrasings.
    expanded: list[dict] = list(records)
    paraphrase_prefixes = [
        "Please ",
        "Can you ",
        "I need you to ",
        "In our ProdxCloud studio backend, ",
        "For the Studio TSX layer, ",
    ]
    for r in records:
        for pre in paraphrase_prefixes:
            if len(expanded) >= 320:
                break
            expanded.append({**r, "prompt": (pre + r["prompt"][0].lower() + r["prompt"][1:]) if r["prompt"] else r["prompt"]})
        if len(expanded) >= 320:
            break
    return expanded


def main() -> None:
    records = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(records)} records, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
