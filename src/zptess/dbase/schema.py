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

from typing import Optional, List
from datetime import datetime

# ------------------
# SQLAlchemy imports
# -------------------

from sqlalchemy import create_engine, String, ForeignKey, PrimaryKeyConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine

import anyio

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)

# ---------------------
# Data Model as classes
# ---------------------

Base = declarative_base()

class Config(Base):

    __tablename__ = "config_t"

    section:   Mapped[str] = mapped_column(String(32))
    prop:      Mapped[str] = mapped_column('property', String(255))
    value:     Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        PrimaryKeyConstraint(
            section,
            prop),
        {})

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, nname={self.name!r}, mac={self.mac!r})"


class Tess(Base):

    __tablename__ = "tess_t"

    id:        Mapped[int] = mapped_column(primary_key=True)
    session:   Mapped[datetime]
    name:      Mapped[str] = mapped_column(String(10))
    mac:       Mapped[str] = mapped_column(String(17))

    # This is not a real column, it s meant for the ORM
    samples:   Mapped[List['Samples']] = relationship(back_populates="tess")

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, nname={self.name!r}, mac={self.mac!r})"
   

class Samples(Base):
    __tablename__ = "samples_t"

    id:        Mapped[int] = mapped_column(primary_key=True)
    tess_id:   Mapped[int] = mapped_column(ForeignKey("tess_t.id"))
   
    tstamp:    Mapped[datetime]
    session:   Mapped[datetime]
    seq:       Mapped[int]
    mag:       Mapped[float]
    freq:      Mapped[float]
    temp_box:  Mapped[float]

    # This is not a real column, it s meant for the ORM
    tess:      Mapped['Tess'] = relationship(back_populates="samples")

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r})"

# -------------------
# Auxiliary functions
# -------------------

async def schema() -> None:
    '''The main entry point specified by pyproject.toml'''
    log.info("Creating schema")
    engine = create_async_engine("sqlite+aiosqlite:///zptess.db", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        #await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

def main():

    from zptess import __version__
    from zptess.photometer.protocol.transport import UDPTransport, SerialTransport
    from zptess.photometer.protocol.photinfo import HTMLInfo
    from zptess.utils.argsparse import args_parser
    from zptess.utils.logging import configure

    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "Example Textual App"
    )
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    anyio.run(schema)