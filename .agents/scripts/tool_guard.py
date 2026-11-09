#!/usr/bin/env python3
"""Bezpečnostní guard pro Antigravity (hook PreToolUse v .agents/hooks.json).

Čte JSON ze stdin, vrací JSON s rozhodnutím na stdout:
  auto_approve  bezpečné čtení, povolené kontroly a testy, commit a add v rozsahu úkolu na větvi ag/*,
  allow         běžný zápis souboru ve workspace mimo chráněné zóny (rozhoduje výchozí politika Antigravity),
  force_ask     vše, co má potvrdit uživatel (git switch, nová větev, pull, merge, neznámé příkazy a nástroje),
  deny          tvrdý zákaz (push, změny remote a config, Docker, databáze, instalace, sudo, přístup mimo
                ~/odoo-review, tajemství, zápis do zakázaných souborů, obcházení shellu).

Zásada: při jakékoli chybě nebo neznámém vstupu nikdy auto_approve; chyba guardu = deny.
Guard i hooks.json jsou v zakázané zóně (.agents/), agent je nesmí měnit. Mění je jen Claude v ~/odoo-dev.
"""

import datetime
import json
import os
import re
import shlex
import sys
from pathlib import Path

EXPECTED_ROOT_NAME = "odoo-review"
# Záznam rozhodnutí mimo workspace (agent ho nesmí číst ani měnit); důkaz, že hook guard opravdu spustil.
LOG_PATH = Path(os.environ.get("INVESTRA_GUARD_LOG") or Path.home() / "Library/Logs/investra-tool-guard.log")

AUTO = "auto_approve"
ALLOW = "allow"
ASK = "force_ask"
DENY = "deny"

# --- zóny (musí odpovídat .agents/rules/10-zony.md) ------------------------------------------------

FORBIDDEN_PREFIXES = (".agents/", ".github/", ".git/", ".vscode/", "addons/third_party/")
FORBIDDEN_FILES = {
    "CLAUDE.md", "AGENTS.md", "GEMINI.md", ".gitignore", ".gitattributes",
    "docs/rozhodnuti.md", "docs/otevrene-body.md", "docs/architektura.md",
}
FORBIDDEN_PATTERNS = (re.compile(r"^docker-compose[^/]*\.ya?ml$"), re.compile(r"(^|/)\.env[^/]*$"))
RED_PREFIXES = (
    "addons/custom/investra_nav/engine.py", "addons/custom/investra_nav/models/",
    "addons/custom/investra_nav/tests/scenarios/", "addons/custom/investra_posting/",
    "addons/custom/investra_fx_revaluation/", "addons/custom/investra_allocation/",
    "addons/custom/investra_rates/", "addons/custom/investra_vat_identified/",
    "addons/custom/investra_entity/models/record_guard.py", "tools/nav_reference/",
)
RED_PATTERNS = (re.compile(r"^addons/custom/[^/]+/migrations/"),)

SECRET_NAMES = re.compile(
    r"(^\.env(?!\.example$).*|.*\.dump$|.*\.pem$|.*\.key$|^id_[a-z0-9]+.*|^\.netrc$|^\.git-credentials$|.*\.sql\.gz$)"
)
SECRET_DIRS = {"duverne", "zalohy", "filestore", ".ssh", ".gemini", ".aws", ".gnupg"}

# --- nástroje Antigravity (https://antigravity.google/docs/hooks, Supported tools) -------------------

# read_file, write_file, create_file a edit_file používá rozšíření pro VS Code (zjištěno 2026-11-09).
READ_TOOLS = {"view_file", "read_file", "list_dir", "find_by_name", "grep_search"}
WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "write_file", "create_file",
               "edit_file"}
DELEGATE_TOOLS = {"ask_question", "manage_task", "list_permissions", "ask_permission", "send_message"}
ASK_TOOLS = {"search_web", "read_url_content", "schedule", "invoke_subagent", "define_subagent",
             "manage_subagents", "generate_image"}
PATH_KEY = re.compile(r"(path|file|dir|directory|cwd)", re.I)

# --- příkazy -------------------------------------------------------------------------------------------

DENY_PROGRAMS = {
    "sudo", "su", "doas", "docker", "docker-compose", "podman", "kubectl", "colima",
    "psql", "pg_dump", "pg_restore", "pg_dumpall", "createdb", "dropdb", "mysql", "sqlite3", "odoo", "odoo-bin",
    "pip", "pip3", "pipx", "uv", "npm", "npx", "yarn", "pnpm", "brew", "port", "gem", "cargo", "apt", "apt-get",
    "sh", "bash", "zsh", "dash", "fish", "ksh", "csh", "tcsh", "eval", "exec", "source", ".", "env", "xargs",
    "nohup", "timeout", "nice", "time", "watch", "command", "builtin", "script", "expect",
    "curl", "wget", "nc", "ncat", "ssh", "scp", "sftp", "rsync", "ftp", "telnet",
    "base64", "xxd", "openssl", "uudecode", "perl", "ruby", "node", "php", "lua", "osascript", "swift",
    "chmod", "chown", "chflags", "xattr", "ln", "kill", "killall", "pkill", "launchctl", "crontab", "at",
    "open", "security", "defaults", "code", "gh", "dd", "mount", "diskutil", "tmutil",
}
READ_PROGRAMS = {"ls", "cat", "head", "tail", "wc", "grep", "egrep", "fgrep", "rg", "find", "pwd", "diff",
                 "file", "stat", "tree", "sort", "uniq", "cut", "echo", "true", "basename", "dirname", "realpath"}
WRITE_PROGRAMS = {"rm", "rmdir", "mv", "cp", "mkdir", "touch", "sed", "awk", "tee", "make", "patch"}
READ_DENY_FLAGS = {
    "find": {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls"},
    "sort": {"-o", "--output"},
    "tree": {"-o"},
}
PYTHON = {"python3", "python"}
XML_CHECK_CODE = "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])"
ET_CHECK = re.compile(r"^import xml\.etree\.ElementTree as ET; ET\.parse\('([^'\\]+)'\)$")

GIT_GLOBAL_OK = {"--no-pager", "-P", "--no-optional-locks"}
GIT_READ = {"status", "diff", "log", "show", "rev-parse", "ls-files", "blame", "grep", "describe", "shortlog",
            "cat-file", "reflog", "ls-tree", "merge-base", "rev-list", "name-rev", "whatchanged", "count-objects"}
GIT_READ_DENY_FLAGS = ("--output", "--ext-diff", "--textconv", "-O", "--open-files-in-pager", "--exec",
                       "--no-index", "--filters")
GIT_ASK = {"switch", "checkout", "pull", "fetch", "merge", "stash", "restore", "reset", "cherry-pick", "revert",
           "am", "apply", "mv", "rm", "gc", "archive", "submodule", "clean", "bisect"}
GIT_DENY = {"push", "rebase", "filter-branch", "filter-repo", "update-ref", "symbolic-ref", "replace", "notes",
            "credential", "credential-store", "credential-osxkeychain", "credential-cache", "daemon", "send-email",
            "instaweb", "worktree", "init", "clone", "hook", "upload-pack", "receive-pack", "http-push",
            "remote-ext", "fast-import", "update-index", "commit-tree", "write-tree", "read-tree", "prune"}
GIT_CONFIG_READ_FLAGS = {"--get", "--get-all", "--get-regexp", "--list", "-l", "--show-origin", "--show-scope",
                         "--name-only", "--null", "-z", "--local", "--global", "--system", "--includes"}


class Decision(Exception):
    def __init__(self, decision, reason):
        super().__init__(reason)
        self.decision = decision
        self.reason = reason


def result(decision, reason):
    return {"decision": decision, "reason": f"[tool_guard] {reason}"}


# --- cesty ---------------------------------------------------------------------------------------------

def resolve(path, base):
    if not isinstance(path, str) or not path or "\x00" in path:
        raise Decision(DENY, "neplatná cesta")
    if path.startswith("~"):
        raise Decision(DENY, f"cesta mimo workspace: {path}")
    candidate = Path(path) if os.path.isabs(path) else Path(base) / path
    return Path(os.path.realpath(candidate))


def relative(real, root):
    try:
        rel = real.relative_to(root)
    except ValueError:
        raise Decision(DENY, f"přístup mimo {root.name}: {real}")
    return rel.as_posix() if str(rel) != "." else ""


def check_secret(rel):
    parts = rel.split("/") if rel else []
    if any(p in SECRET_DIRS for p in parts) or (parts and SECRET_NAMES.match(parts[-1])):
        raise Decision(DENY, f"tajný nebo důvěrný soubor: {rel}")


def is_forbidden(rel):
    return (rel in FORBIDDEN_FILES or any(rel == p.rstrip("/") or rel.startswith(p) for p in FORBIDDEN_PREFIXES)
            or any(p.search(rel) for p in FORBIDDEN_PATTERNS))


def is_red(rel):
    return any(rel.startswith(p) for p in RED_PREFIXES) or any(p.search(rel) for p in RED_PATTERNS)


def read_path(path, base, root):
    rel = relative(resolve(path, base), root)
    check_secret(rel)
    return rel


def write_path(path, base, root):
    rel = read_path(path, base, root)
    if is_forbidden(rel):
        raise Decision(DENY, f"zápis do zakázaného souboru: {rel}")
    return rel


# --- stav repozitáře (čte se přímo ze souborů, bez spouštění gitu) -----------------------------------

def current_branch(root):
    head = (root / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    return head[len("ref: refs/heads/"):] if head.startswith("ref: refs/heads/") else None


def task_scope(root, branch):
    """Soubory z „Rozsahu souborů“ zadání aktuálního úkolu AG. Bez jistoty vrací None."""
    match = re.match(r"^ag/(AG-\d+)-", branch or "")
    if not match:
        return None
    tasks = sorted((root / "docs" / "ukoly").glob(f"{match.group(1)}-*.md"))
    if len(tasks) != 1:
        return None
    text = tasks[0].read_text(encoding="utf-8")
    block = re.search(r"\*\*Rozsah souborů:\*\*(.*?)(?:\n\s*\n|\Z)", text, re.S)
    if not block:
        return None
    files = {t for t in re.findall(r"`([^`]+)`", block.group(1)) if "/" in t and " " not in t}
    if not files:
        return None
    return files | {tasks[0].relative_to(root).as_posix()}


# --- shell ---------------------------------------------------------------------------------------------

def check_shell_syntax(line):
    """Povolí jen jednoduchý příkaz bez expanzí, řetězení, přesměrování a substitucí."""
    if not line.strip():
        raise Decision(DENY, "prázdný příkaz")
    if any(ord(c) < 32 for c in line):
        raise Decision(DENY, "řídicí znak nebo více řádků v příkazu")
    quote = None
    word_start = True
    for c in line:
        if quote == "'":
            if c == "'":
                quote = None
            word_start = False
            continue
        if quote == '"':
            if c in '$`\\':
                raise Decision(DENY, f"expanze v uvozovkách ({c})")
            if c == '"':
                quote = None
            word_start = False
            continue
        if c in "'\"":
            quote = c
            word_start = False
            continue
        if c in ";&|<>()$`\\":
            raise Decision(DENY, f"řetězení, přesměrování nebo substituce ({c})")
        if c in "*?[]{}":
            raise Decision(DENY, f"shellová expanze ({c}); vzor dejte do uvozovek")
        if word_start and c in "~#=":
            raise Decision(DENY, f"shellová expanze nebo komentář ({c})")
        word_start = c == " "
    if quote:
        raise Decision(DENY, "neuzavřené uvozovky")
    return shlex.split(line)


def program_name(argv0, root):
    if "/" not in argv0:
        return argv0
    if os.path.dirname(argv0) in ("/bin", "/usr/bin"):
        return os.path.basename(argv0)
    real = Path(os.path.realpath(argv0 if os.path.isabs(argv0) else root / argv0))
    try:
        real.relative_to(root)
    except ValueError:
        raise Decision(DENY, f"spuštění programu mimo workspace: {argv0}")
    raise Decision(ASK, f"spuštění skriptu z workspace: {argv0}")


def check_args_paths(args, cwd, root, deny_flags=()):
    for arg in args:
        if arg.startswith("-"):
            flag = arg.split("=", 1)[0]
            if flag in deny_flags:
                raise Decision(DENY, f"nepovolený přepínač {flag}")
            if "/" in arg or ".." in arg:
                raise Decision(ASK, f"přepínač s cestou: {arg}")
            continue
        real = resolve(arg, cwd)
        if "/" in arg or arg.startswith(".") or real.exists():
            read_path(arg, cwd, root)


def decide_python(args, cwd, root):
    if args[:2] == ["-m", "py_compile"] and len(args) > 2:
        for a in args[2:]:
            if a.startswith("-"):
                raise Decision(ASK, "py_compile s přepínačem")
            read_path(a, cwd, root)
        return AUTO, "kontrola syntaxe Pythonu"
    rest = [a for a in args if a not in ("-v", "-q")]
    if rest == ["-m", "unittest", "discover", "-s", "tools/nav_reference", "-p", "test_*.py"] and \
            Path(os.path.realpath(cwd)) == root:
        return AUTO, "referenční testy NAV"
    if len(args) == 3 and args[0] == "-c" and args[1] == XML_CHECK_CODE:
        read_path(args[2], cwd, root)
        return AUTO, "kontrola XML"
    if len(args) == 2 and args[0] == "-c":
        m = ET_CHECK.match(args[1])
        if m:
            read_path(m.group(1), cwd, root)
            return AUTO, "kontrola XML"
    if "-c" in args:
        raise Decision(DENY, "python -c s neschváleným kódem")
    if args[:1] == ["-m"] and len(args) > 1 and args[1] in ("pip", "ensurepip", "venv", "http.server"):
        raise Decision(DENY, f"python -m {args[1]} není povolený")
    raise Decision(ASK, "spuštění Pythonu mimo povolené kontroly")


def decide_git(args, cwd, root):
    while args and args[0].startswith("-"):
        if args[0] not in GIT_GLOBAL_OK:
            raise Decision(DENY, f"globální přepínač gitu {args[0]} není povolený")
        args = args[1:]
    if not args:
        raise Decision(ASK, "git bez podpříkazu")
    sub, rest = args[0], args[1:]
    if Path(os.path.realpath(cwd)) != root and not str(Path(os.path.realpath(cwd))).startswith(str(root) + os.sep):
        raise Decision(DENY, "git mimo workspace")
    branch = current_branch(root)
    on_ag = bool(branch and branch.startswith("ag/"))

    if sub in GIT_DENY:
        raise Decision(DENY, f"git {sub} je zakázaný")
    if sub in GIT_READ:
        for a in rest:
            if a.split("=", 1)[0] in GIT_READ_DENY_FLAGS:
                raise Decision(DENY, f"git {sub} {a} není povolený")
        return AUTO, f"git {sub} (čtení)"
    if sub == "config":
        return decide_git_config(rest)
    if sub == "remote":
        if not rest or rest in (["-v"], ["--verbose"]) or (rest[0] == "get-url" and len(rest) <= 3):
            return AUTO, "git remote (čtení)"
        if rest[0] == "show":
            return ASK, "git remote show kontaktuje server"
        raise Decision(DENY, f"změna remote: git remote {rest[0]}")
    if sub == "branch":
        return decide_git_branch(rest)
    if sub == "tag":
        if not rest or rest[0] in ("-l", "--list"):
            return AUTO, "git tag (čtení)"
        raise Decision(DENY, "vytváření a mazání tagů není povolené")
    if sub == "add":
        return decide_git_add(rest, cwd, root, branch, on_ag)
    if sub == "commit":
        if not on_ag:
            raise Decision(DENY, f"commit mimo větev ag/* (aktuálně {branch or 'odpojená HEAD'})")
        return decide_git_commit(rest)
    if sub in ("switch", "checkout"):
        for flag in ("-c", "-C", "-b", "-B", "--create", "--force-create", "--orphan"):
            if flag in rest:
                idx = rest.index(flag)
                name = rest[idx + 1] if idx + 1 < len(rest) else ""
                if not name.startswith("ag/"):
                    raise Decision(DENY, f"nová větev musí začínat ag/: {name or '?'}")
        return ASK, f"git {sub} mění pracovní větev"
    if sub == "pull":
        if any(a.startswith("--rebase") or a == "-r" for a in rest):
            raise Decision(DENY, "git pull --rebase není povolený")
        return ASK, "git pull"
    if sub == "merge":
        if not on_ag:
            raise Decision(DENY, "slučovat lze jen do větve ag/*")
        return ASK, "git merge"
    if sub == "reset" and any(a in ("--hard", "--merge", "--keep") for a in rest):
        raise Decision(DENY, "git reset --hard není povolený")
    if sub == "clean" and not any(a in ("-n", "--dry-run") for a in rest):
        raise Decision(DENY, "git clean bez -n není povolený")
    if sub in ("rm", "mv"):
        for a in rest:
            if not a.startswith("-"):
                write_path(a, cwd, root)
    if sub in GIT_ASK:
        return ASK, f"git {sub}"
    return ASK, f"neznámý podpříkaz git {sub}"


def decide_git_config(rest):
    if rest and rest[0] in ("get", "list"):
        if any(a.startswith("--file") or a in ("-f", "--blob") for a in rest):
            return ASK, "git config z jiného souboru"
        return AUTO, "git config (čtení)"
    if rest and rest[0] in ("set", "unset", "rename-section", "remove-section", "edit"):
        raise Decision(DENY, f"změna git config ({rest[0]})")
    flags = [a for a in rest if a.startswith("-")]
    values = [a for a in rest if not a.startswith("-")]
    if any(f.split("=", 1)[0] not in GIT_CONFIG_READ_FLAGS for f in flags):
        raise Decision(DENY, "změna git config")
    read_flag = any(f in ("--get", "--get-all", "--list", "-l") for f in flags)
    if "--get-regexp" in flags and len(values) <= 2:
        return AUTO, "git config (čtení)"
    if (read_flag and len(values) <= 1) or (not flags and len(values) == 1) or \
            (flags and all(f in ("--local", "--global", "--system", "--show-origin") for f in flags) and len(values) == 1):
        return AUTO, "git config (čtení)"
    raise Decision(DENY, "změna git config")


def decide_git_branch(rest):
    mutating = {"-d", "-D", "--delete", "-m", "-M", "--move", "-c", "-C", "--copy", "-f", "--force",
                "-u", "--set-upstream-to", "--unset-upstream", "--edit-description", "-t", "--track"}
    listing = {"-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "--list", "-l", "--show-current",
               "--sort", "--format", "--column", "--no-column", "--color", "--no-color", "--abbrev", "--no-abbrev"}
    filtering = {"--contains", "--no-contains", "--merged", "--no-merged", "--points-at"}
    flags = [a.split("=", 1)[0] for a in rest if a.startswith("-")]
    names = [a for a in rest if not a.startswith("-")]
    if any(f in mutating for f in flags):
        if names and all(n.startswith("ag/") for n in names):
            return ASK, "změna větve ag/*"
        raise Decision(DENY, "změna jiné než ag/* větve")
    if all(f in listing | filtering for f in flags) and (
            not names or any(f in filtering or f in ("--list", "-l") for f in flags)):
        return AUTO, "git branch (čtení)"
    if names and not flags and names[0].startswith("ag/"):
        return ASK, "vytvoření větve ag/*"
    if names and not names[0].startswith("ag/") and not flags:
        raise Decision(DENY, "nová větev musí začínat ag/")
    return ASK, "git branch s neznámými přepínači"


def decide_git_add(rest, cwd, root, branch, on_ag):
    paths = [a for a in rest if a != "--"]
    if not on_ag:
        raise Decision(DENY, "git add mimo větev ag/*")
    if not paths or any(a.startswith("-") for a in paths):
        for a in paths:
            if not a.startswith("-"):
                write_path(a, cwd, root)
        return ASK, "git add s přepínači nebo bez cest"
    rels = [write_path(a, cwd, root) for a in paths]
    scope = task_scope(root, branch)
    if scope is None:
        return ASK, "rozsah úkolu nejde spolehlivě zjistit"
    outside = [r for r in rels if r not in scope]
    if outside:
        return ASK, f"soubory mimo rozsah úkolu: {', '.join(outside)}"
    return AUTO, "git add v rozsahu úkolu"


def decide_git_commit(rest):
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in ("-m", "--message"):
            if i + 1 >= len(rest):
                raise Decision(ASK, "commit bez zprávy")
            i += 2
            continue
        if a.startswith("--message=") or (a.startswith("-m") and len(a) > 2):
            i += 1
            continue
        if a in ("-q", "--quiet"):
            i += 1
            continue
        if a.startswith("--author") or a.startswith("--date") or a in ("--no-verify", "-n"):
            raise Decision(DENY, f"git commit {a} není povolený")
        return ASK, f"git commit s přepínačem {a}"
    if not any(a in ("-m", "--message") or a.startswith("--message=") or (a.startswith("-m") and len(a) > 2)
               for a in rest):
        return ASK, "commit bez zprávy na příkazové řádce"
    return AUTO, "commit na větvi ag/*"


def decide_command(args_obj, root):
    line = args_obj.get("CommandLine")
    if not isinstance(line, str):
        raise Decision(DENY, "chybí příkaz")
    cwd_value = args_obj.get("Cwd") or str(root)
    cwd = resolve(cwd_value, root)
    relative(cwd, root)
    argv = check_shell_syntax(line)
    if "=" in argv[0]:
        raise Decision(DENY, "nastavení proměnné prostředí před příkazem")
    prog = program_name(argv[0], root)
    rest = argv[1:]
    if re.fullmatch(r"python3(\.\d+)?", prog):
        prog = "python3"
    if prog in DENY_PROGRAMS or prog.startswith("git-"):
        raise Decision(DENY, f"program {prog} je zakázaný")
    if prog == "git":
        return decide_git(rest, str(cwd), root)
    if prog in PYTHON:
        return decide_python(rest, str(cwd), root)
    if prog in READ_PROGRAMS:
        check_args_paths(rest, str(cwd), root, READ_DENY_FLAGS.get(prog, ()))
        return AUTO, f"{prog} (čtení ve workspace)"
    if prog in WRITE_PROGRAMS:
        if prog == "rm" and any(a.startswith("-") and ("r" in a or "R" in a or a == "--recursive") for a in rest):
            raise Decision(DENY, "rm -r není povolený")
        for a in rest:
            if not a.startswith("-") and prog not in ("sed", "awk", "make"):
                write_path(a, str(cwd), root)
        return ASK, f"{prog} mění soubory"
    return ASK, f"neznámý program {prog}"


# --- hlavní rozhodnutí ---------------------------------------------------------------------------------

def collect_paths(args_obj):
    found = []
    for key, value in (args_obj or {}).items():
        if PATH_KEY.search(key) and isinstance(value, str):
            found.append(value)
        elif PATH_KEY.search(key) and isinstance(value, list):
            found.extend(v for v in value if isinstance(v, str))
    return found


def decide(payload, root):
    try:
        root = Path(os.path.realpath(root))
        if root.name != EXPECTED_ROOT_NAME:
            raise Decision(DENY, f"guard smí běžet jen v ~/{EXPECTED_ROOT_NAME}")
        workspaces = payload.get("workspacePaths")
        if not isinstance(workspaces, list) or not workspaces:
            raise Decision(DENY, "chybí workspacePaths")
        if [Path(os.path.realpath(w)) for w in workspaces] != [root]:
            raise Decision(DENY, f"Antigravity smí pracovat jen ve workspace {root}")
        call = payload.get("toolCall")
        if not isinstance(call, dict) or not isinstance(call.get("name"), str):
            raise Decision(DENY, "chybí toolCall")
        name, args = call["name"], call.get("args") or {}
        if not isinstance(args, dict):
            raise Decision(DENY, "neplatné argumenty nástroje")

        if name == "run_command":
            decision, reason = decide_command(args, root)
        elif name in READ_TOOLS:
            paths = collect_paths(args)
            if not paths:
                raise Decision(ASK, f"{name} bez rozpoznané cesty")
            for p in paths:
                read_path(p, root, root)
            decision, reason = AUTO, f"{name} ve workspace"
        elif name in WRITE_TOOLS:
            paths = collect_paths(args)
            if not paths:
                raise Decision(DENY, f"{name} bez cílového souboru")
            rels = [write_path(p, root, root) for p in paths]
            if any(is_red(r) for r in rels):
                decision, reason = ASK, f"zápis do červené zóny: {', '.join(rels)}"
            else:
                decision, reason = ALLOW, "zápis ve workspace mimo chráněné zóny"
        elif name in DELEGATE_TOOLS:
            decision, reason = ALLOW, f"{name}"
        elif name in ASK_TOOLS:
            decision, reason = ASK, f"{name} vyžaduje potvrzení"
        else:
            decision, reason = ASK, f"neznámý nástroj {name}"
        return result(decision, reason)
    except Decision as d:
        return result(d.decision, d.reason)
    except Exception as exc:  # noqa: BLE001 - chyba guardu nesmí nikdy povolit
        return result(DENY, f"chyba guardu: {type(exc).__name__}")


def write_log(payload, out):
    """Zapíše jeden řádek JSON. Chyba zápisu rozhodnutí nikdy nemění."""
    try:
        call = payload.get("toolCall") if isinstance(payload, dict) else None
        name = call.get("name") if isinstance(call, dict) else None
        args = call.get("args") if isinstance(call, dict) and isinstance(call.get("args"), dict) else {}
        detail = args.get("CommandLine") or next(iter(collect_paths(args)), "")
        line = {
            "time": datetime.datetime.now().isoformat(timespec="seconds"),
            "tool": name if isinstance(name, str) else None,
            "detail": str(detail)[:200],
            "decision": out["decision"],
            "reason": out["reason"],
        }
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def main():
    payload = None
    try:
        root = Path(__file__).resolve().parents[2]
        raw = sys.stdin.read(1_000_000)
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload není objekt")
        out = decide(payload, root)
    except Exception as exc:  # noqa: BLE001
        out = result(DENY, f"neplatný vstup guardu: {type(exc).__name__}")
    write_log(payload, out)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
