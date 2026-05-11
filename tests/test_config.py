"""Tests for anubis.toml loader."""
from anubis.config import load_config


def test_missing_file_returns_empty(tmp_path):
    assert load_config(tmp_path / "anubis.toml") == {}


def test_empty_obfuscate_section(tmp_path):
    (tmp_path / "anubis.toml").write_text("[obfuscate]\n")
    assert load_config(tmp_path / "anubis.toml") == {}


def test_no_obfuscate_section(tmp_path):
    (tmp_path / "anubis.toml").write_text("[other]\nfoo = true\n")
    assert load_config(tmp_path / "anubis.toml") == {}


def test_bool_flags_parsed(tmp_path):
    (tmp_path / "anubis.toml").write_text("[obfuscate]\ncarbon = true\njunk = false\n")
    assert load_config(tmp_path / "anubis.toml") == {"carbon": True, "junk": False}


def test_output_string_parsed(tmp_path):
    (tmp_path / "anubis.toml").write_text('[obfuscate]\noutput = "dist/out.py"\n')
    assert load_config(tmp_path / "anubis.toml") == {"output": "dist/out.py"}


def test_unknown_keys_ignored(tmp_path):
    (tmp_path / "anubis.toml").write_text("[obfuscate]\ncarbon = true\nunknown_key = 42\n")
    assert load_config(tmp_path / "anubis.toml") == {"carbon": True}


def test_wrong_type_ignored(tmp_path):
    # carbon must be bool, not int
    (tmp_path / "anubis.toml").write_text("[obfuscate]\ncarbon = 1\n")
    assert load_config(tmp_path / "anubis.toml") == {}


def test_all_bool_keys_accepted(tmp_path):
    toml = "[obfuscate]\n" + "\n".join(
        f"{k} = true"
        for k in ("antidebug", "junk", "mix_strings", "big_script",
                  "carbon", "import_alias", "encrypt", "rft", "bcc", "compile")
    )
    (tmp_path / "anubis.toml").write_text(toml)
    result = load_config(tmp_path / "anubis.toml")
    assert len(result) == 10
    assert all(v is True for v in result.values())
