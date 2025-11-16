from sqlalchemy import (
    MetaData, Table, Column,
    String, Float, Text, JSON
)

metadata = MetaData()

battles = Table(
    "battles",
    metadata,
    Column("id", String, primary_key=True),   # Q-ID
    Column("label", String),
    Column("description", Text),
    Column("start", String),
    Column("end", String),
    Column("latitude", Float),
    Column("longitude", Float),

    # full untouched Wikidata entity JSON
    Column("raw_entity", JSON),
)
