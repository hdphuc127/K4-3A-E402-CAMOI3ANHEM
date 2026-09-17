import html
from sqlite3 import Row

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.db.session import get_connection, initialize_database

app = FastAPI(title="MistakeTutor DB Viewer", docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    initialize_database()
    tables = list_tables()
    if not tables:
        return render_page("No tables found.", "")
    return render_table(tables[0])


@app.get("/table/{table_name}", response_class=HTMLResponse)
def table(table_name: str) -> str:
    initialize_database()
    tables = list_tables()
    if table_name not in tables:
        return render_page("Table not found.", render_table_links(tables))
    return render_table(table_name)


def list_tables() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
    return [str(row["name"]) for row in rows]


def read_table(table_name: str) -> tuple[list[str], list[Row]]:
    with get_connection() as connection:
        columns = connection.execute(
            f"PRAGMA table_info({_quote_identifier(table_name)})"
        ).fetchall()
        rows = connection.execute(
            f"SELECT * FROM {_quote_identifier(table_name)} LIMIT 100"
        ).fetchall()
    return [str(column["name"]) for column in columns], rows


def render_table(table_name: str) -> str:
    tables = list_tables()
    columns, rows = read_table(table_name)
    headers = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body = "".join(render_row(columns, row) for row in rows)
    content = f"""
    <h2>{html.escape(table_name)}</h2>
    <p>Showing up to 100 rows.</p>
    <table>
      <thead><tr>{headers}</tr></thead>
      <tbody>{body}</tbody>
    </table>
    """
    return render_page(content, render_table_links(tables, table_name))


def render_table_links(tables: list[str], active_table: str | None = None) -> str:
    return "".join(
        f'<a class="{"active" if table == active_table else ""}" '
        f'href="/table/{html.escape(table)}">{html.escape(table)}</a>'
        for table in tables
    )


def render_row(columns: list[str], row: Row) -> str:
    cells = "".join(
        f"<td>{html.escape(str(row[column]))}</td>"
        for column in columns
    )
    return f"<tr>{cells}</tr>"


def render_page(content: str, nav: str) -> str:
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>DB Viewer</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; }}
        nav {{ margin-bottom: 20px; }}
        nav a {{ margin-right: 12px; }}
        nav a.active {{ font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
      </style>
    </head>
    <body>
      <h1>MistakeTutor DB Viewer</h1>
      <nav>{nav}</nav>
      {content}
    </body>
    </html>
    """


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
