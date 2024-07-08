# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 


## # # # # # # # # # 
# System wide imports
# # # # # # # # # # -

import logging

from typing import Optional, List
from datetime import datetime

# # # # # # # # # # # -
# Third party libraries
# # # # # # # # # # # -

from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lica.sqlalchemy.asyncio.dbase import Model

# # # # # # # # # 
# Module constants
# # # # # # # # # 

# # # # # # # # # # # # -
# Module global variables
# # # # # # # # # # # # -

# get the module logger
log = logging.getLogger(__name__)

# # # # # # # # # # # # # # # # # -
# Data Model, declarative ORM style
# # # # # # # # # # # # # # # # # -

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
    sensor:         Mapped[str] = mapped_column(String(12)) # Sensor model: TSL237, S9705-01DT
    model:          Mapped[str] = mapped_column(String(8))
    firmware:       Mapped[str] = mapped_column(String(17))
    zero_point:     Mapped[float]
    freq_offset:    Mapped[float]

    # This is not a real column, it s meant for the ORM
    samples: Mapped[List['Sample']] = relationship(back_populates="photometer")
    # This is not a real column, it s meant for the ORM
    calibrations: Mapped[List['Summary']] = relationship(back_populates="photometer")

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

    # This is not a real column, it s meant for the ORM
    photometer: Mapped['Photometer'] = relationship(back_populates="samples")

    # rounds per sample (at least 1...)
    # This is not a real column, it s meant for the ORM
    rounds: Mapped[List['Round']] = relationship(secondary=SamplesRounds, back_populates="samples")

    __table_args__ = (
        UniqueConstraint(
            tstamp,
            role),
        {})

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r})"


class Round(Model):
    __tablename__ = "rounds_t"

    id:         Mapped[int] = mapped_column(primary_key=True)
    seq:        Mapped[int] = mapped_column('round', Integer) # Round number form 1..NRounds
    role:       Mapped[str] = mapped_column(String(4))
    session:    Mapped[int] = mapped_column(Integer)
    freq:       Mapped[Optional[float]]         # Average of Median method
    central:    Mapped[Optional[str]] = mapped_column(String(6))  # ether 'mean' or 'median'
    stddev:     Mapped[Optional[float]]         # Standard deviation for frequency central estimate
    mag:        Mapped[Optional[float]]         # magnitiude corresponding to central frequency and summing ficticious zero point 
    zp_fict:    Mapped[Optional[float]]         # Ficticious ZP to estimate instrumental magnitudes (=20.50)
    zero_point: Mapped[Optional[float]]         # Estimated Zero Point for this round ('test' photometer round only, else NULL)
    nsamples:   Mapped[Optional[int]]           # Number of samples for this round
    duration:   Mapped[Optional[float]]         # Approximate duration, in seconds

    # samples per round. Shoudl match the window size
    # This is not a real column, it s meant for the ORM
    samples: Mapped[List['Sample']] = relationship(secondary=SamplesRounds, back_populates="rounds")

    __table_args__ = (
        UniqueConstraint(
            session,
            seq,
            role),
        {})


class Summary(Model):
    __tablename__ = "summary_t"

    id:             Mapped[int] = mapped_column(primary_key=True)
    phot_id:        Mapped[int] = mapped_column(ForeignKey("photometer_t.id"), index=True)

    session:        Mapped[int] = mapped_column(Integer)                # calibration session identifier
    role:           Mapped[str] = mapped_column(String(4))              # either 'test' or 'ref'
    calibration:    Mapped[Optional[str]] = mapped_column(String(6))    # Either 'MANUAL' or 'AUTO'
    calversion:     Mapped[Optional[str]] = mapped_column(String(64))   # calibration software version
    prev_zp:        Mapped[Optional[float]]                             # previous ZP before calibration
    author:         Mapped[Optional[str]]                               # who run the calibration
    nrounds:        Mapped[Optional[int]]                               # Number of rounds passed
    offset:         Mapped[Optional[float]]                             # Additional offset that was summed to the computed zero_point
    upd_flag:       Mapped[Optional[bool]]                              # 1 => TESS-W ZP was updated, 0 => TESS-W ZP was not updated
    zero_point:         Mapped[Optional[float]]                         #  calibrated zero point
    zero_point_method:  Mapped[Optional[str]]  = mapped_column(String(6))  #  either the 'mode' or 'median' of the different rounds
    freq:               Mapped[Optional[float]]                            # final chosen frequency
    freq_method:        Mapped[Optional[str]]  = mapped_column(String(6))  #  either the 'mode' or 'median' of the different rounds
    mag:                Mapped[Optional[float]]                            #  final chosen magnitude uzing ficticious ZP
    filter:             Mapped[Optional[str]] = mapped_column(String(32))  #  Filter type (i.e. UV-IR/740)
    plug:               Mapped[Optional[str]] = mapped_column(String(16))  #  Plug type (i.e. USB-A)
    box:                Mapped[Optional[str]] = mapped_column(String(16))  #  Box model (i.e. FSH714)
    collector:          Mapped[Optional[str]] = mapped_column(String(16))  #  Collector model
    comment:            Mapped[Optional[str]] = mapped_column(String(255)) #  Additional comment for the callibration process

    # This is not a real column, it s meant for the ORM
    photometer: Mapped['Photometer'] = relationship(back_populates="calibrations")

    __table_args__ = (
        UniqueConstraint(
            session,
            role),
        {})


class Batch(Model):
    __tablename__ = "batch_t"

    begin_tstamp:   Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    end_tstamp:     Mapped[Optional[datetime]] = mapped_column(DateTime)
    email_sent:     Mapped[Optional[bool]]
    calibrations:   Mapped[Optional[int]]
    comment:        Mapped[Optional[str]] = mapped_column(String(255))
