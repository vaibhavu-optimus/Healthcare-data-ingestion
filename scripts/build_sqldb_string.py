import argparse
import getpass

from sqlalchemy.engine import URL

def _escape_odbc_value(value: str) -> str:
    """Wrap in {...} (doubling any literal }) only if it actually needs it."""
    if any(c in value for c in ";{}="):
        return "{" + value.replace("}", "}}") + "}"
    return value

def build_sql_db_url(server: str, database: str, username: str, password: str, port: int = 1433) -> str:
    raw_odbc = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{server},{port};"
        f"Database={database};"
        f"Uid={_escape_odbc_value(username)};"
        f"Pwd={_escape_odbc_value(password)};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "ConnectTimeout=30;"
    )
    return URL.create(drivername="mssql+pyodbc", query={"odbc_connect": raw_odbc}).render_as_string(
        hide_password=False
    )

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", required=True, help="e.g. sqlserver-healthcare-01.database.windows.net")
    parser.add_argument("--database", required=True, help="e.g. sqldb-healthcare-01")
    parser.add_argument("--username", required=True, help="e.g. sqladmin")
    parser.add_argument("--port", type=int, default=1433)
    args = parser.parse_args()

    password = getpass.getpass("SQL password (not echoed): ")

    url = build_sql_db_url(args.server, args.database, args.username, password, args.port)
    print("\nSQL_DB_URL=" + url)
    print("\nCopy the line above into .env. Nothing was written to disk by this script.")


if __name__ == "__main__":
    main()