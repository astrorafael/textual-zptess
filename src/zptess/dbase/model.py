# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------


#--------------------
# System wide imports
# -------------------

import logging

from typing import Optional, List
from datetime import datetime

# ---------------------
# Third party libraries
# ---------------------

from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lica.sqlalchemy.asyncio.dbase import Model

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__)

# ---------------------------------
# Data Model, declarative ORM style
# ---------------------------------

class Config(Model):

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


class Photometer(Model):
    __tablename__ = "photometer_t"

    id:             Mapped[int] = mapped_column(primary_key=True)
    name:           Mapped[str] = mapped_column(String(10))
    mac:            Mapped[str] = mapped_column(String(17))
    sensor:         Mapped[str] = mapped_column(String(12))
    model:          Mapped[str] = mapped_column(String(8))
    firmware:       Mapped[str] = mapped_column(String(17))
    zero_point:     Mapped[float]
    freq_offset:    Mapped[float]

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, name={self.name!r}, mac={self.mac!r})"
   

# Samples per round
# Due to the sliding window collect process, a sample may belong to several rounds
# This part is not part of the ORM, as it uses the basic Table API
SamplesRounds = Table(
    "samples_rounds_t",
    Model.metadata,
    Column('round_id', ForeignKey('rounds_t.id'), nullable=False, primary_key=True),
    Column('sample_id', ForeignKey('samples_t.id'), nullable=False, primary_key=True),
)


class Sample(Model):
    __tablename__ = "samples_t"

    id:         Mapped[int] = mapped_column(primary_key=True)
    phot_id:    Mapped[int] = mapped_column(ForeignKey("photometer_t.id"), index=True)
    tstamp:     Mapped[datetime] = mapped_column(DateTime)
    role:       Mapped[str] = mapped_column(String(4))
    session:    Mapped[int]
    seq:        Mapped[int]
    mag:        Mapped[float]
    freq:       Mapped[float]
    temp_box:   Mapped[float]

    # rounds per sample (at least 1...)
    # This is not a real column, it s meant for the ORM
    rounds: Mapped[List['Round']] = relationship(secondary=SamplesRounds, back_populates="samples")

    __table_args__ = (
        UniqueConstraint(
            tstamp,
            role),
        {})

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r}, wave={self.wave})"


class Round(Model):
    __tablename__ = "rounds_t"

    id:         Mapped[int] = mapped_column(primary_key=True)
    seq:        Mapped[int] = mapped_column(Integer) # Round number form 1..NRounds
    role:       Mapped[str] = mapped_column(String(4))
    session:    Mapped[int] = mapped_column(Integer)
    freq:       Mapped[Optional[float]] # Average of Median method
    central:    Mapped[Optional[str]] = mapped_column(String(6))  # ether 'mean' or 'median'
    stddev:     Mapped[Optional[float]] # Standard deviation for frequency central estimate

    # samples per round. Shoudl match the window size
    # This is not a real column, it s meant for the ORM
    samples: Mapped[List['Sample']] = relationship(secondary=SamplesRounds, back_populates="rounds")

    __table_args__ = (
        UniqueConstraint(
            session,
            seq,
            role),
        {})

