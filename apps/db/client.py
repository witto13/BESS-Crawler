import logging
import os

from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


def get_pool():
    dsn = os.getenv("POSTGRES_DSN", "postgresql://bess:bess@db:5432/bess")
    return ConnectionPool(conninfo=dsn, open=True, max_size=5, min_size=1, timeout=30)







