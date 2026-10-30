from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.orm import Session


@contextmanager
def collect_queries(db: Session):
    connection = db.connection()
    queries = []

    def record_query(conn, cursor, statement, parameters, context, executemany):
        queries.append(" ".join(statement.split()))

    event.listen(connection, "before_cursor_execute", record_query)
    try:
        yield queries
    finally:
        event.remove(connection, "before_cursor_execute", record_query)
