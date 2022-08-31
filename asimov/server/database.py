"""
Asimov databse interface
------------------------

This module implements the asimov database and its interfaces.


"""

import json

import sqlalchemy as db
from sqlalchemy.orm import declarative_base, sessionmaker

# FIXME: Use the configuration file to allow a choice of database engine
engine = db.create_engine('sqlite:///foo.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)

def install():
    """Install the tables in a new database.

    Examples
    --------
    FIXME: Add docs.

    """
    Logger()
    Base.metadata.create_all(engine)

class Logger(Base):
    """Database interface for the log collector.

    Parameters
    ----------
    Base : sqlalchemy.orm.declarative_base
        The declarative base for the database table.

    Examples
    --------
    
    >>> from asimov.server import database
    >>> entry = database.Logger(pipeline="bilby", 
                        module="sampling", 
                        level="update", 
                        time=datetime.datetime.now(),
                        event="GW150914",
                        production="ProdX8",
                        message="This is a test message."
                        )

    """

    __tablename__ = "logging"
    levels = {"critical": 0,
              "error": 1,
              "warning": 2,
              "info": 3,
              "debug": 4,
              "update": 5}
    levels_ix = dict((v,k) for k,v in levels.items())

    id = db.Column("id", db.Integer, primary_key=True)
    pipeline = db.Column("pipeline", db.String(255), nullable=False)
    module = db.Column("module", db.String(255), nullable=True)
    level = db.Column("level", db.Integer)
    time = db.Column("time", db.DateTime)
    event = db.Column("event", db.String(20))
    production = db.Column("production", db.String(10))
    message = db.Column("message", db.Text)

    def save(self):
        """Insert this log entry into the database.

        Examples
        --------
        FIXME: Add docs.

        """
        session = Session()
        session.add(self)
        session.commit()

    def __init__(self, **kwargs):
        if "level" in kwargs:
            kwargs['level'] = self.levels[kwargs['level']]
        super().__init__(**kwargs)

    def __repr__(self):
        return f"""Log message
-----//------
TYPE:  {self.levels_ix[self.level]}\t PIPELINE: {self.pipeline}
EVENT: {self.event}\t MODULE:   {self.module}
-----//------
{self.message}
        """

    def __json__(self, indent: int = 2):
        """Show a representation of the log entry in JSON format.

        Parameters
        ----------
        indent : int
            The indentation of the JSON block.

        Examples
        --------
        FIXME: Add docs.

        """
        return json.dumps(self.__dictrepr__(), indent=indent)


    def __dictrepr__(self):
        """Show a representation of the log entry as a dictionary.

        Examples
        --------
        FIXME: Add docs.

        """
        data = {"level": self.levels_ix[self.level],
                "time": str(self.time),
                "production": self.production,
                "pipeline": self.pipeline,
                "event": self.event,
                "module": self.module,
                "message": self.message}
        return data

    @classmethod
    def list(cls, **filters):
        """List all of the entries in the log database which match a set of filtering conditions.

        Parameters
        ----------
        **filters : dict
            Keyword arguments for the filters

        Examples
        --------
        FIXME: Add docs.


        """
        session = Session()
        if filters:
            result = session.query(cls).filter_by(**filters).all()
        else:
            result = session.query(cls).all()
        return result
