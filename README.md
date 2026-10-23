# logbook

개인 업무 회고 아카이브(`logbook-vault`, 마크다운)를 MCP로 여는 서버와 배포 설정.

## 구조
```
mcp/            MCP 서버 (Python, mcp SDK 2.x MCPServer)
  src/logbook_mcp/vault.py   파일 접근 + 경로/쓰기 범위 규칙 (MCP 의존 없음)
  src/logbook_mcp/server.py  MCP 툴 정의
  tests/
```

## 툴
| 툴 | 설명 |
|---|---|
| `list_notes(directory)` | 노트 목록 |
| `read_note(path)` | 노트 읽기 |
| `search_notes(query, directory, limit)` | 경로·본문 부분일치 검색 (대소문자 무시) |
| `write_note(path, content)` | 새 노트 생성. 기존 파일은 덮어쓰지 않음 |
| `append_note(path, content)` | 기존 노트 끝에 추가 |
| `vault_guide()` | vault README(규칙) 반환 |

안전 규칙: vault 밖 경로, 숨김 경로(`.git` 등), `.md` 외 파일 거부. 새 노트 생성은 `WRITE_DIRS`(기본 `inbox,retro,docs,career,study`) 아래만, `APPEND_ONLY_DIRS`(기본 `journal`)는 append만 허용. vault 최상위 파일(`Home.md`, `README.md`)과 `templates/`, `notes/`는 AI가 수정 불가. 삭제·덮어쓰기 툴 없음.

## 로컬 실행
```bash
cd mcp
uv sync
uv run pytest
VAULT_PATH=~/projects/logbook-vault uv run logbook-mcp            # stdio
VAULT_PATH=~/projects/logbook-vault MCP_TRANSPORT=streamable-http uv run logbook-mcp  # http://127.0.0.1:8000/mcp
```

## Claude Code 연결 (로컬)
```bash
claude mcp add logbook -s user \
  -e VAULT_PATH=$HOME/projects/logbook-vault \
  -- uv run --directory $HOME/projects/logbook/mcp logbook-mcp
```

## TODO
- [ ] Dockerfile / docker-compose (MCP + Caddy)
- [ ] 인증 (OAuth / Bearer)
- [ ] 서버 vault git 동기화 (pull --rebase → commit → push, cron)
