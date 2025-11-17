from sqlalchemy import MetaData, Table, Column, String, Float, JSON

metadata = MetaData()

battles = Table(
    "battles",
    metadata,
    Column("id", String, primary_key=True),
    Column("label", String),
    Column("description", String),
    Column("start", String),
    Column("end", String),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("coord_source", String),   # NEW COLUMN
    Column("raw_entity", JSON),
)
