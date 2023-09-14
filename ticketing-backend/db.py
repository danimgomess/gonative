import datetime
import hashlib
import os
#import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ticket(db.Model):
    """
    Ticket Model
    """

    __tablename__ = "ticket"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(db.String, nullable=False)
    code = db.Column(db.String, nullable = False, unique = True)
    timestamp = db.Column(db.String, nullable = False)
    expiration = db.Column(db.String, nullable = True)
    is_used = db.Column(db.Boolean, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=True)
    user = db.relationship('User', back_populates='ticket', uselist=False)




    def __init__(self, **kwargs):
        """
        Initializes a Ticket object
        """

        self.event = kwargs.get("event", "")
        self.code = kwargs.get("code", "")
        self.timestamp = kwargs.get("timestamp", "")
        self.expiration = kwargs.get("expiration", "")
        self.is_used = False

    
    def serialize(self):
        """
        Serializes a Ticket object with a readable date format
        """
        expiration_date_final = None
        if (self.expiration is not None):
            expiration_date = str(self.expiration)
            expiration_date_final = ""
            expiration_date_final += expiration_date[:16]



        return {
            "id" : self.id,
            "event" : self.event,
            "code" : self.code,
            "timestamp" : self.timestamp,
            "expiration" : expiration_date_final,
            "is_used" : self.is_used,
            "ticket_holder" : self.user.simple_serialize()
        }
    
    def simple_serialize(self):
        """
        Serializes a Ticket object without the ticket_holder field
        """
        expiration_date_final = None
        if (self.expiration is not None):
            expiration_date = str(self.expiration)
            expiration_date_final = ""
            expiration_date_final += expiration_date[:16]


        return {
            "id" : self.id,
            "event" : self.event,
            "code" : self.code,
            "timestamp" : self.timestamp,
            "expiration" : expiration_date_final,
            "is_used" : self.is_used
        }
    


class User(db.Model):
    """
    User Model
    """


    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable=False)
    ticket = db.relationship('Ticket', back_populates='user', uselist=False, cascade = "delete")


    def __init__(self, **kwargs):
        """
        Initialize an User object
        """
        self.name = kwargs.get("name", "")
        self.phone_number = kwargs.get("phone_number", "")            
        self.email = kwargs.get("email")

    def serialize(self):
        """
        Serialize a User object
        """
        return{
            "id": self.id,
            "name": self.name,
            "phone_number": self.phone_number,
            "email": self.email,
            "ticket": self.ticket.simple_serialize()
        
        } 
        
    def simple_serialize(self):
        """
        Serialize a User object without the ticket field
        """
        return{
            "id": self.id,
            "name": self.name,
            "phone_number": self.phone_number,
            "email": self.email
        
        } 