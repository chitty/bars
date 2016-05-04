import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(100), nullable=False)
    picture = Column(String(250))


class Bar(Base):
    __tablename__ = 'bar'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'id': self.id,
        }


class Drink(Base):
    __tablename__ = 'drink'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    price = Column(String(8))
    type = Column(String(250))
    bar_id = Column(Integer, ForeignKey('bar.id'))
    bar = relationship(Bar)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    created = Column(DateTime, default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'description': self.description,
           'id': self.id,
           'price': self.price,
           'type': self.type,
        }


engine = create_engine('sqlite:///bars.db')

Base.metadata.create_all(engine)
