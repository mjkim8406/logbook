import pytest

from logbook_mcp.vault import Vault, VaultError


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "retro/daily").mkdir(parents=True)
    (tmp_path / "notes").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "retro/daily/2026-10-14.md").write_text("# 회고\nKafka 컨슈머 랙 해결\n", encoding="utf-8")
    (tmp_path / "notes/cdc.md").write_text("Debezium binlog\n", encoding="utf-8")
    (tmp_path / ".git/secret.md").write_text("kafka", encoding="utf-8")
    return Vault(tmp_path)


def test_list_skips_hidden(vault):
    assert vault.list() == ["notes/cdc.md", "retro/daily/2026-10-14.md"]
    assert vault.list("retro") == ["retro/daily/2026-10-14.md"]


def test_search_case_insensitive(vault):
    r = vault.search("kafka")
    assert [x["path"] for x in r] == ["retro/daily/2026-10-14.md"]
    assert r[0]["matches"][0]["line"] == 2


@pytest.mark.parametrize("bad", ["../etc/passwd.md", "/../../x.md", ".git/secret.md", "notes/x.txt"])
def test_read_rejects_unsafe(vault, bad):
    with pytest.raises(VaultError):
        vault.read(bad)


def test_write_scope_and_no_overwrite(vault):
    assert vault.write("inbox/a.md", "hi") == "inbox/a.md"
    with pytest.raises(VaultError):
        vault.write("inbox/a.md", "again")
    with pytest.raises(VaultError):
        vault.write("notes/b.md", "nope")


def test_append(vault):
    vault.append("retro/daily/2026-10-14.md", "## 추가\n내용")
    assert vault.read("retro/daily/2026-10-14.md").endswith("## 추가\n내용\n")
    with pytest.raises(VaultError):
        vault.append("notes/cdc.md", "x")
