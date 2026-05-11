"""Integration tests for --ci and --output CLI flags."""

import os
import subprocess
import sys


def _run(*args, extra_env=None, cwd=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CI", "ANUBIS_CI")}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "anubis", *args],
        capture_output=True, text=True, env=env, cwd=str(cwd) if cwd else None,
    )


def test_ci_missing_file_exits_1(tmp_path):
    result = _run("nonexistent.py", "--ci", cwd=tmp_path)
    assert result.returncode == 1
    assert "error:" in result.stderr


def test_ci_success_default_output(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    result = _run(str(tmp_path / "script.py"), "--ci", cwd=tmp_path)
    assert result.returncode == 0
    assert "Obfuscated:" in result.stdout
    assert (tmp_path / "script-obf.py").exists()


def test_ci_custom_output(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    out = tmp_path / "custom-out.py"
    result = _run(str(tmp_path / "script.py"), "--ci", "--output", str(out), cwd=tmp_path)
    assert result.returncode == 0
    assert out.exists()


def test_output_flag_without_ci_flag(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    out = tmp_path / "via-output-flag.py"
    # Use CI env var to avoid pause, but don't pass --ci flag explicitly
    result = _run(
        str(tmp_path / "script.py"), "--output", str(out),
        extra_env={"CI": "true"}, cwd=tmp_path,
    )
    assert result.returncode == 0
    assert out.exists()


def test_ci_env_var_triggers_ci_mode(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    result = _run(
        str(tmp_path / "script.py"),
        extra_env={"CI": "true"}, cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "Obfuscated:" in result.stdout


def test_toml_config_sets_default(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    out = tmp_path / "from-toml.py"
    (tmp_path / "anubis.toml").write_text(
        f'[obfuscate]\noutput = "{out}"\n'
    )
    result = _run(str(tmp_path / "script.py"), "--ci", cwd=tmp_path)
    assert result.returncode == 0
    assert out.exists()


def test_cli_flag_overrides_toml(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    toml_out = tmp_path / "from-toml.py"
    cli_out = tmp_path / "from-cli.py"
    (tmp_path / "anubis.toml").write_text(
        f'[obfuscate]\noutput = "{toml_out}"\n'
    )
    result = _run(
        str(tmp_path / "script.py"), "--ci", "--output", str(cli_out),
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert cli_out.exists()
    assert not toml_out.exists()


def test_ci_no_banner_in_stdout(tmp_path):
    (tmp_path / "script.py").write_text("x = 1\n")
    result = _run(str(tmp_path / "script.py"), "--ci", cwd=tmp_path)
    assert "ANUBIS" not in result.stdout
    assert "$$$$" not in result.stdout
