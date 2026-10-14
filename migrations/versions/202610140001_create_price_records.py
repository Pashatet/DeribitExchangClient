"""Create the price records table.

Revision ID: 202610140001
Revises:
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa


revision = "202610140001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The application previously used metadata.create_all() at startup. If that
    # already created this table, preserve it and just record this baseline revision.
    if not sa.inspect(op.get_bind()).has_table("price_records"):
        op.create_table(
            "price_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ticker", sa.String(length=20), nullable=False),
            sa.Column("price", sa.Numeric(precision=30, scale=12), nullable=False),
            sa.Column("timestamp", sa.BigInteger(), nullable=False),
            sa.CheckConstraint(
                "ticker IN ('btc_usd', 'eth_usd')",
                name="ck_price_records_ticker",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("price_records"):
        index_names = {index["name"] for index in inspector.get_indexes("price_records")}
        if "ix_price_records_ticker_timestamp" not in index_names:
            op.create_index(
                "ix_price_records_ticker_timestamp",
                "price_records",
                ["ticker", "timestamp"],
                unique=False,
            )


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("price_records"):
        op.drop_table("price_records")
