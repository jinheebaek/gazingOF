from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, Table, JSON

Base = declarative_base()

session_chamber = Table(
    "session_chamber", Base.metadata,
    Column("session_id", Integer, ForeignKey("session.id")),
    Column("chamber_id", Integer, ForeignKey("chamber.id"))
)


class SessionModel(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    status = Column(Text)
    session_params = Column(JSON)
    protocol_name = Column(Text)
    protocol_params = Column(JSON)

    chambers = relationship("ChamberModel", order_by="ChamberModel.name",
                            secondary=session_chamber, backref="sessions")
    data = relationship("DataModel", order_by="DataModel.chamber_id",
                        back_populates="session", cascade="all, delete")

    # protocol_id = Column(Integer, ForeignKey('protocol.id'))
    # protocol = relationship('Protocol', backref='sessions')
    # # project_id = Column(Integer, ForeignKey('project.id'))
    # # project = relationship('Project', backref='sessions')

    # @property
    # def param_dict(self):
    #     params = self.params.split('&')
    #     params = {p.split('=')[0]: p.split('=')[1] for p in params}
    #     return params


class ChamberModel(Base):
    __tablename__ = "chamber"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    inputs = Column(JSON)
    outputs = Column(JSON)
    output_led_matrix = Column(JSON)
    port = Column(Text)

    data = relationship("DataModel", order_by="DataModel.chamber_id",
                        back_populates="chamber")


class DataModel(Base):
    __tablename__ = "data"

    # id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("session.id"), primary_key=True)
    chamber_id = Column(Integer, ForeignKey("chamber.id"), primary_key=True)
    subject = Column(Text)
    data = Column(JSON)

    session = relationship("SessionModel", back_populates="data")
    chamber = relationship("ChamberModel", back_populates="data")


# class ProtocolModel(Base):
#     __tablename__ = 'protocol'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(Text, unique=True, nullable=False)

# class ProjectModel(Base):
#     __tablename__ = 'project'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(Text)
