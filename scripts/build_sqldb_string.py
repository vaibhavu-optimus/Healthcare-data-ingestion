import argparse
import getpass

from sqlalchemy.engine import URL


def build_sql_db_url(server: str, database: str, username: str, password: str, port: int = 1433) -> str:
    return URL.create(
        drivername="mssql+pymssql",
        username=username,
        password=password,
        host=server,
        port=port,
        database=database,
    ).render_as_string(hide_password=False)


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