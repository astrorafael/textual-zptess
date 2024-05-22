# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import asyncio
import logging

from typing import Optional
from datetime import datetime

# ------------------
# SQLAlchemy imports
# -------------------

from sqlalchemy import create_engine

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine

import anyio

#--------------
# local imports
# -------------

from zptess import __version__
from zptess.main import arg_parser, configure_logging

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# ---------------------
# Data Model as classes
# ---------------------

Base = declarative_base()

class Samples(Base):
    __tablename__ = "samples_t"

    id:        Mapped[int] = mapped_column(primary_key=True)
    tstamp:    Mapped[datetime]
    session:   Mapped[datetime]
    seq:       Mapped[int]
    mag:       Mapped[Optional[float]]
    freq:      Mapped[float]
    temp_box:  Mapped[float]

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r})"

# -------------------
# Auxiliary functions
# -------------------

async def schema() -> None:
    '''The main entry point specified by pyproject.toml'''
    log.info("Creating schema")
    engine = create_async_engine("sqlite+aiosqlite:///zptext.db", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

def main():
    parser = arg_parser(
        name = __name__,
        version = __version__,
        description = "Example Textual App"
    )
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args)
    anyio.run(schema)