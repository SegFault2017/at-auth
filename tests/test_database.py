from app.database import normalize_database_url


def test_neon_url_gets_asyncpg_driver_and_ssl():
    url = "postgresql://u:p@ep-x.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    assert normalize_database_url(url) == "postgresql+asyncpg://u:p@ep-x.aws.neon.tech/neondb?ssl=require"


def test_postgres_scheme_alias():
    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"


def test_explicit_asyncpg_url_unchanged():
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/at_user"
    assert normalize_database_url(url) == url


def test_sqlite_url_unchanged():
    url = "sqlite+aiosqlite:///./at_user.db"
    assert normalize_database_url(url) == url


def test_settings_ignore_unknown_env_file_keys(tmp_path):
    # `neon init` / `neon env pull` add DATABASE_URL_UNPOOLED and NEON_BRANCH to .env
    from app.config import Settings

    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=sqlite+aiosqlite:///x.db\nNEON_BRANCH=main\n")
    assert Settings(_env_file=env).database_url == "sqlite+aiosqlite:///x.db"
