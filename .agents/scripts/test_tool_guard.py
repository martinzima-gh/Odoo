"""Testy guardu Antigravity. Spuštění: python3 -m unittest discover -s .agents/scripts -p "test_*.py"

Testy běží nad dočasným workspace „odoo-review“ se syntetickým obsahem, nesahají na skutečné repozitáře.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tool_guard  # noqa: E402

TASK = """# AG-007 Zkušební úkol

**Rozsah souborů:** jen `addons/custom/investra_nav/views/nav_views.xml`, záznam `view_valuation_form`.
Plus sekce Výsledek v tomto souboru.

## Výsledek
"""


class GuardCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "odoo-review"
        for d in (".git", "docs/ukoly", "addons/custom/investra_nav/views", "addons/custom/investra_nav/models",
                  "tools/nav_reference", ".agents/scripts"):
            (self.root / d).mkdir(parents=True)
        self.set_branch("ag/AG-007-zkouska")
        (self.root / "docs/ukoly/AG-007-zkouska.md").write_text(TASK, encoding="utf-8")
        (self.root / "addons/custom/investra_nav/views/nav_views.xml").write_text("<odoo/>", encoding="utf-8")
        (self.root / "addons/custom/investra_nav/models/valuation.py").write_text("", encoding="utf-8")
        (self.root / "README.md").write_text("x", encoding="utf-8")
        (self.root / ".env.example").write_text("X=", encoding="utf-8")
        (self.root / ".env").write_text("SECRET=1", encoding="utf-8")
        self.outside = self.tmp / "odoo-dev"
        self.outside.mkdir()
        (self.outside / ".env").write_text("SECRET=1", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def set_branch(self, branch):
        head = f"ref: refs/heads/{branch}\n" if branch else "0123456789abcdef0123456789abcdef01234567\n"
        (self.root / ".git/HEAD").write_text(head, encoding="utf-8")

    def payload(self, name, args, workspaces=None):
        return {"conversationId": "t", "workspacePaths": workspaces or [str(self.root)],
                "toolCall": {"name": name, "args": args}, "stepIdx": 1}

    def decide(self, name, args, **kw):
        return tool_guard.decide(self.payload(name, args, **kw), self.root)["decision"]

    def cmd(self, line, cwd=None):
        return self.decide("run_command", {"CommandLine": line, "Cwd": cwd or str(self.root)})

    def assertCmd(self, expected, *lines):
        for line in lines:
            with self.subTest(line=line):
                self.assertEqual(self.cmd(line), expected, line)


class TestAllow(GuardCase):
    def test_safe_reads_run_without_prompt(self):
        self.assertCmd(tool_guard.AUTO,
                       "git status", "git diff", "git log -n 5 --oneline", "git show HEAD",
                       "git diff feature/nav-prototyp...HEAD --stat", "git branch", "git branch -a",
                       "git branch --show-current", "git rev-parse HEAD", "git ls-files",
                       "git config --get user.name", "git config user.name", "git config --list",
                       "git remote -v", "git remote", "git remote get-url origin", "git log HEAD~3",
                       "ls addons", "cat README.md", "grep -rn valuation addons", "find addons -name '*.xml'",
                       "head -5 README.md", "wc -l README.md", "pwd", "cat .env.example", "git --no-pager log")

    def test_checks_and_reference_tests_run_without_prompt(self):
        self.assertCmd(tool_guard.AUTO,
                       "python3 -m py_compile addons/custom/investra_nav/models/valuation.py",
                       'python3 -m unittest discover -s tools/nav_reference -p "test_*.py"',
                       "python3 -m unittest discover -s tools/nav_reference -p 'test_*.py' -v",
                       'python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse(sys.argv[1])" '
                       'addons/custom/investra_nav/views/nav_views.xml',
                       "python3 -c \"import xml.etree.ElementTree as ET; "
                       "ET.parse('addons/custom/investra_nav/views/nav_views.xml')\"")

    def test_commit_and_add_in_scope_on_ag_branch(self):
        self.assertCmd(tool_guard.AUTO,
                       'git commit -m "Upravit formulář"', "git commit -q -m 'Doplnit výsledek'",
                       "git add addons/custom/investra_nav/views/nav_views.xml",
                       "git add docs/ukoly/AG-007-zkouska.md addons/custom/investra_nav/views/nav_views.xml")

    def test_read_tools_inside_workspace(self):
        self.assertEqual(self.decide("view_file", {"AbsolutePath": str(self.root / "README.md")}), tool_guard.AUTO)
        self.assertEqual(self.decide("list_dir", {"DirectoryPath": str(self.root)}), tool_guard.AUTO)

    def test_ordinary_write_is_delegated_to_default_policy(self):
        target = str(self.root / "addons/custom/investra_nav/views/nav_views.xml")
        self.assertEqual(self.decide("write_to_file", {"TargetFile": target}), tool_guard.ALLOW)


class TestAsk(GuardCase):
    def test_branch_and_sync_commands_need_confirmation(self):
        self.assertCmd(tool_guard.ASK,
                       "git switch feature/nav-prototyp", "git switch -c ag/AG-008-dalsi",
                       "git checkout -b ag/AG-008-dalsi", "git branch ag/AG-008-dalsi", "git pull",
                       "git merge ag/AG-001-formular-oceneni", "git fetch", "git stash", "git restore README.md")

    def test_add_outside_scope_or_unclear_needs_confirmation(self):
        self.assertCmd(tool_guard.ASK, "git add README.md", "git add .", "git add -A",
                       "git add addons/custom/investra_nav/models/valuation.py")

    def test_add_without_reliable_scope_needs_confirmation(self):
        (self.root / "docs/ukoly/AG-007-zkouska.md").write_text("# bez rozsahu\n", encoding="utf-8")
        self.assertCmd(tool_guard.ASK, "git add addons/custom/investra_nav/views/nav_views.xml")

    def test_unknown_and_writing_programs_need_confirmation(self):
        self.assertCmd(tool_guard.ASK, "rm README.md", "mv README.md docs/README.md", "make test",
                       "python3 tools/nav_demo/demo.py", "jq . README.md", 'git commit -am "x"', "git commit")

    def test_red_zone_write_and_web_need_confirmation(self):
        target = str(self.root / "addons/custom/investra_nav/models/valuation.py")
        self.assertEqual(self.decide("write_to_file", {"TargetFile": target}), tool_guard.ASK)
        self.assertEqual(self.decide("search_web", {"Query": "odoo"}), tool_guard.ASK)
        self.assertEqual(self.decide("browser_click", {}), tool_guard.ASK)


class TestDeny(GuardCase):
    def test_push_remote_and_config_mutations(self):
        self.assertCmd(tool_guard.DENY,
                       "git push", "git push origin ag/AG-007-zkouska", "git remote add x https://example.com/r.git",
                       "git remote set-url --push origin https://example.com/r.git", "git remote remove origin",
                       "git config user.name Hacker", "git config --global user.email x@y",
                       "git config --unset remote.origin.pushurl", "git config set core.hooksPath x",
                       "git -c core.hooksPath=x commit -m y", "git -C /tmp status", "git rebase main",
                       "git reset --hard HEAD~1", "git clean -fd", "git tag v1", "git worktree add ../x",
                       "git branch -D feature/nav-prototyp", "git switch -c feature/x", "git commit --author=x -m y")

    def test_docker_database_install_sudo(self):
        self.assertCmd(tool_guard.DENY,
                       "docker ps", "docker compose up", "psql -h localhost", "pg_dump investra_dev",
                       "odoo shell", "pip install requests", "python3 -m pip install x", "npm install",
                       "brew install jq", "sudo ls", "curl https://example.com", "/bin/sh -c ls")

    def test_secrets_and_outside_workspace(self):
        self.assertCmd(tool_guard.DENY,
                       "cat .env", f"cat {self.outside}/.env", "cat ../odoo-dev/.env", "ls ..", "ls /etc",
                       "grep -r SECRET ../odoo-dev", "cat zalohy/x.dump")
        self.assertEqual(self.decide("view_file", {"AbsolutePath": str(self.root / ".env")}), tool_guard.DENY)
        self.assertEqual(self.decide("view_file", {"AbsolutePath": str(self.outside / ".env")}), tool_guard.DENY)
        self.assertEqual(self.cmd("ls", cwd=str(self.outside)), tool_guard.DENY)

    def test_symlink_out_of_workspace(self):
        os.symlink(self.outside / ".env", self.root / "odkaz.txt")
        os.symlink(self.outside, self.root / "venku")
        self.assertCmd(tool_guard.DENY, "cat odkaz.txt", "ls venku")
        self.assertEqual(self.decide("view_file", {"AbsolutePath": str(self.root / "venku/.env")}), tool_guard.DENY)

    def test_writes_to_forbidden_files(self):
        for rel in (".agents/hooks.json", ".agents/scripts/tool_guard.py", ".agents/rules/00-role-a-hranice.md",
                    "CLAUDE.md", "docs/rozhodnuti.md", ".github/copilot-instructions.md", ".gitignore",
                    "docker-compose.investra.yml", ".env", ".git/hooks/pre-commit", "AGENTS.md",
                    "addons/third_party/x.py", ".vscode/settings.json"):
            with self.subTest(rel=rel):
                self.assertEqual(self.decide("write_to_file", {"TargetFile": str(self.root / rel)}), tool_guard.DENY)
                self.assertEqual(self.decide("replace_file_content", {"TargetFile": str(self.root / rel)}),
                                 tool_guard.DENY)
        self.assertEqual(self.decide("write_to_file", {"TargetFile": str(self.outside / "x.py")}), tool_guard.DENY)
        self.assertCmd(tool_guard.DENY, "git add .agents/hooks.json", "git rm .agents/scripts/tool_guard.py",
                       "rm -rf addons", "cp README.md .agents/hooks.json", "mv README.md CLAUDE.md",
                       "touch .env", "chmod u+w .agents/hooks.json")

    def test_commit_and_add_outside_ag_branch(self):
        self.set_branch("feature/nav-prototyp")
        self.assertCmd(tool_guard.DENY, 'git commit -m "x"', "git add addons/custom/investra_nav/views/nav_views.xml",
                       "git merge ag/AG-007-zkouska")
        self.set_branch(None)
        self.assertCmd(tool_guard.DENY, 'git commit -m "x"')

    def test_wrong_workspace(self):
        self.assertEqual(self.decide("run_command", {"CommandLine": "git status", "Cwd": str(self.root)},
                                     workspaces=[str(self.outside)]), tool_guard.DENY)
        self.assertEqual(self.decide("run_command", {"CommandLine": "git status", "Cwd": str(self.root)},
                                     workspaces=[str(self.root), str(self.outside)]), tool_guard.DENY)
        other = self.tmp / "odoo-dev-copy"
        other.mkdir()
        payload = self.payload("run_command", {"CommandLine": "git status", "Cwd": str(other)}, [str(other)])
        self.assertEqual(tool_guard.decide(payload, other)["decision"], tool_guard.DENY)


class TestBypass(GuardCase):
    def test_shell_tricks_are_blocked(self):
        self.assertCmd(tool_guard.DENY,
                       "git status; git push", "git status && git push", "git status || git push",
                       "git status | sh", "echo Z2l0IHB1c2g= | base64 -d | sh", "ls $(echo /)", "ls `echo /`",
                       "cat $HOME/odoo-dev/.env", 'echo "$HOME"', "cat ~/odoo-dev/.env", "ls ~",
                       "eval git push", "sh -c 'git push'", "bash -c 'git push'", "zsh -c ls",
                       "env git push", "xargs git push", "GIT_DIR=/tmp git status", "ls > out.txt",
                       "cat < .env", "(git push)", "{ git push; }", "git status &", "ls\ngit push",
                       "ls *", "cat .e?v", "ls [a]", "ls {a,b}", r"git\ push", "exec git push",
                       "source x.sh", ". x.sh", "nohup git push", "command git push", "perl -e 'exec q(git push)'",
                       "python3 -c 'import os; os.system(\"git push\")'", "/tmp/git push", "git-receive-pack x",
                       "find . -exec git push ;", "find . -delete", "sort -o .env README.md",
                       "git diff --no-index /etc/passwd README.md", "git log --output=x", "git grep -O x",
                       "git diff --ext-diff", "")

    def test_relative_program_path_is_not_auto(self):
        self.assertNotEqual(self.cmd("./tools/x.sh"), tool_guard.AUTO)
        self.assertNotEqual(self.cmd("bin/git status"), tool_guard.AUTO)


class TestFailSafe(GuardCase):
    def test_unknown_or_broken_input_never_auto(self):
        broken = [
            {}, {"workspacePaths": [str(self.root)]},
            {"workspacePaths": [str(self.root)], "toolCall": "x"},
            {"workspacePaths": [str(self.root)], "toolCall": {"name": "run_command", "args": {"CommandLine": 5}}},
            {"workspacePaths": [str(self.root)], "toolCall": {"name": "run_command", "args": "ls"}},
            {"workspacePaths": [str(self.root)], "toolCall": {"name": "write_to_file", "args": {}}},
            {"workspacePaths": str(self.root), "toolCall": {"name": "view_file", "args": {}}},
        ]
        for payload in broken:
            with self.subTest(payload=payload):
                self.assertIn(tool_guard.decide(payload, self.root)["decision"], (tool_guard.DENY, tool_guard.ASK))

    def test_internal_error_denies(self):
        original = tool_guard.decide_command
        tool_guard.decide_command = lambda *a: 1 / 0
        try:
            self.assertEqual(self.cmd("git status"), tool_guard.DENY)
        finally:
            tool_guard.decide_command = original

    def test_unreadable_head_denies_commit(self):
        (self.root / ".git/HEAD").unlink()
        self.assertEqual(self.cmd('git commit -m "x"'), tool_guard.DENY)

    def test_main_process_outputs_valid_json_and_fails_closed(self):
        script = self.root / ".agents/scripts/tool_guard.py"
        shutil.copy(HERE / "tool_guard.py", script)

        log = self.tmp / "guard.log"
        env = dict(os.environ, INVESTRA_GUARD_LOG=str(log))

        def run(stdin):
            out = subprocess.run([sys.executable, "-I", str(script)], input=stdin, capture_output=True,
                                 text=True, timeout=10, env=env)
            self.assertEqual(out.returncode, 0)
            return json.loads(out.stdout)["decision"]

        self.assertEqual(run("není json"), tool_guard.DENY)
        self.assertEqual(run("[]"), tool_guard.DENY)
        self.assertEqual(run(""), tool_guard.DENY)
        good = json.dumps(self.payload("run_command", {"CommandLine": "git status", "Cwd": str(self.root)}))
        self.assertEqual(run(good), tool_guard.AUTO)
        bad = json.dumps(self.payload("run_command", {"CommandLine": "git push", "Cwd": str(self.root)}))
        self.assertEqual(run(bad), tool_guard.DENY)
        lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([x["decision"] for x in lines], ["deny", "deny", "deny", "auto_approve", "deny"])
        self.assertEqual(lines[-1]["detail"], "git push")
        self.assertTrue(lines[-1]["reason"].startswith("[tool_guard]"))

    def test_log_failure_does_not_change_decision(self):
        script = self.root / ".agents/scripts/tool_guard.py"
        shutil.copy(HERE / "tool_guard.py", script)
        env = dict(os.environ, INVESTRA_GUARD_LOG="/nonexistent-root-dir/x/guard.log")
        payload = json.dumps(self.payload("run_command", {"CommandLine": "docker --version", "Cwd": str(self.root)}))
        out = subprocess.run([sys.executable, "-I", str(script)], input=payload, capture_output=True, text=True,
                             timeout=10, env=env)
        self.assertEqual(json.loads(out.stdout)["decision"], tool_guard.DENY)

    def test_guard_copy_outside_odoo_review_denies_everything(self):
        other = self.tmp / "jinde"
        (other / ".agents/scripts").mkdir(parents=True)
        script = other / ".agents/scripts/tool_guard.py"
        shutil.copy(HERE / "tool_guard.py", script)
        payload = json.dumps({"workspacePaths": [str(other)],
                              "toolCall": {"name": "run_command", "args": {"CommandLine": "git status",
                                                                            "Cwd": str(other)}}})
        out = subprocess.run([sys.executable, "-I", str(script)], input=payload, capture_output=True, text=True,
                             timeout=10, env=dict(os.environ, INVESTRA_GUARD_LOG=str(self.tmp / "g.log")))
        self.assertEqual(json.loads(out.stdout)["decision"], tool_guard.DENY)

    def test_canary_commands_for_hook_check(self):
        self.assertEqual(self.cmd("git rev-parse --show-toplevel"), tool_guard.AUTO)
        self.assertEqual(self.cmd("uname -a"), tool_guard.ASK)
        self.assertEqual(self.cmd("docker --version"), tool_guard.DENY)

    def test_hooks_json_points_to_guard(self):
        config = json.loads((HERE.parent / "hooks.json").read_text(encoding="utf-8"))
        hook = config["investra-tool-guard"]
        self.assertTrue(hook["enabled"])
        entry = hook["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "*")
        self.assertIn("/odoo-review/.agents/scripts/tool_guard.py", entry["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
