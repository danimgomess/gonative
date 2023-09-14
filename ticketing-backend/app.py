import json
import time
import datetime
import string
from db import db
from db import Ticket, User
from flask import Flask, request, render_template
from flask_mail import Mail
from flask_mail import Message
import random
import os
from datetime import datetime, date, timedelta
import pyqrcode
import time


app = Flask(__name__)

#Email Configurations
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gonative.ticketing@gmail.com'
app.config['MAIL_PASSWORD'] = 'btovmbbnshmoaaji'

mail = Mail(app)

#Database Configurations
db_filename = "tickets.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    return json.dumps(data), code


def failure_response(message, code=404):
    return json.dumps({"error": message}), code


# API routes


# Email routes
@app.route("/api/email/", methods = ["POST"])
def email():
    """
    Endpoint for sending automated email to ticket holder with purchase confirmation
    """
    body = json.loads(request.data)
    if body.get("subject") is None or body.get("recipients") is None or body.get("email_html") is None:
        return failure_response("Arguments not given.", 400)
    
    subject = body.get("subject")
    email_html = body.get("email_html")
    recipients = body.get("recipients")
    attachment_name = body.get("attachment")
    
    msg = Message(subject=subject,
                  sender="gonative.ticketing@gmail.com",
                  recipients=[recipients],
                  html = email_html)
    if body.get("attachment") is not None:
        with app.open_resource(str(attachment_name)) as QRcode:
            msg.attach(str(attachment_name), 'image/jpeg', QRcode.read())
    mail.send(msg)
    return success_response("Email sent.")


# Ticket routes

@app.route("/api/tickets/")
def get_tickets():
    """
    Endpoint for retrieving all tickets
    """
    tickets = [ticket.serialize() for ticket in Ticket.query.all()]
    if tickets is None:
        return failure_response("No ticket found!")
    return success_response({"tickets" : tickets})


@app.route("/api/tickets/<int:ticket_id>/")
def get_ticket(ticket_id):
    """
    Endpoint for retrieving a ticket by id
    """
    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        return failure_response("Ticket not found!")
    
    if ticket.user is None:
        return failure_response("Ticket not initialized properly, please assign it to a user", 400)
    
    return success_response(ticket.serialize())


@app.route("/api/tickets/", methods=["POST"])
def create_ticket():
    """
    Endpoint for creating a new ticket

    Ensure that you assign a user (ticket holder) to a ticket immediately after
    you create it. A ticket without a user (ticket holder) will cause errors.
    """
    body = json.loads(request.data)
    if body.get("event") is None:
        return failure_response("Arguments not given.", 400)
    
    time = str(datetime.now())
    timestamp_final = ""
    timestamp_final += time[:16]

    
    expiration_date = None
    if (body.get("days_valid") is not None):
        expiration_date = get_expiration(int(body.get("days_valid")))

    gen_code = generate_code(10)

    new_ticket = Ticket(
        event = body.get("event"),
        code = gen_code,
        timestamp = timestamp_final, 
        expiration = expiration_date
        
    )

    db.session.add(new_ticket)
    db.session.commit()
    return success_response(new_ticket.simple_serialize(), 201)


@app.route("/api/tickets/<int:ticket_id>/", methods=["DELETE"])
def delete_ticket(ticket_id):
    """"
    Endpoint for deleting a ticket by id

    Ensure you delete the user immediately after deleting the ticket, or errors
    can ensue
    """
    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        return failure_response("Ticket not found!")
    if ticket.user is None:
        return failure_response("Ticket not initialized properly, please assign it to a user", 400)
    db.session.delete(ticket)
    db.session.commit()
    return success_response(ticket.simple_serialize())

@app.route("/api/tickets/", methods=["DELETE"])
def delete_tickets():
    """"
    Endpoint for deleting all tickets. Use with caution.

    Ensure you delete all users immediately after deleting all tickets, or errors
    can ensue
    """
    for ticket in Ticket.query.all():
        db.session.delete(ticket)
    db.session.commit()
    return success_response("All tickets deleted.")


@app.route("/api/tickets/use/<int:ticket_id>/", methods=["PUT"])
def use_ticket(ticket_id):
    """
    Endpoint for spending a ticket whose id is given by the int parameter "ticket_id"
    """
    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        return failure_response("Ticket not found!")
    if ticket.user is None:
        return failure_response("Ticket not initialized properly, please assign it to a user", 400)

    
    ticket.is_used = True
    db.session.commit()
    return success_response(ticket.serialize())


# User routes

@app.route("/api/users/")
def get_users():
    """
    Endpoint for retrieving all users
    """
    users = [user.serialize() for user in User.query.all()]
    return success_response({"users" : users})


@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for retrieving a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    return success_response(user.serialize())


@app.route("/api/users/<int:ticket_id>/", methods=["POST"])
def create_user(ticket_id):
    """
    Endpoint for creating a new user linked with the ticket whose id is given
    by the int parameter "ticket_id"

    Ensure you create a user associated with a ticket immediately after you 
    create a ticket.
    """
    body = json.loads(request.data)
    if body.get("name") is None or body.get("email") is None or body.get("phone_number") is None:
        return failure_response("Arguments not given.", 400)
    
    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        return failure_response("Ticket not found!", 404)
    if ticket.user is not None:
        return failure_response("Ticket already has a user!", 400)


    new_user = User(
        name = body.get("name"),
        email = body.get("email"),
        phone_number = body.get("phone_number")
    )

    new_user.ticket = ticket

    db.session.add(new_user)
    db.session.commit()
    return success_response(new_user.serialize(), 201)


@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """"
    Endpoint for deleting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found!")
    if user.ticket is not None:
        return failure_response("Ticket must be deleted before deleting the user!", 400)
    db.session.delete(user)
    db.session.commit()
    return success_response(user.simple_serialize())

@app.route("/api/users/", methods=["DELETE"])
def delete_users():
    """"
    Endpoint for deleting all users. Use with caution.

    Ensure you delete all tickets immediately after deleting all users, or errors
    can ensue
    """
    for user in User.query.all():
        db.session.delete(user)
    db.session.commit()
    return success_response("All users deleted")


# QR Routes
@app.route("/api/QR/", methods=["POST"])
def generate_qrcode():
    """
    Endpoint for creating a QR code that links to a desired URL.
    
    In its intended use, the qr code links to the ticket validation website that
    displays whether or not the ticket is contained in the database and valid.
    """
    body = json.loads(request.data)
    if body.get("url") is None or body.get("size") is None:
        return failure_response("Arguments not given.", 400)
    
    qr_content = body.get("url")
    size = body.get("size")
    
    ticket_qr = pyqrcode.create(qr_content)
    ticket_qr_png = ticket_qr.png("test.png", scale = 8)
    return success_response({"Base64 link" : ticket_qr.png_as_base64_str(scale=size)}, 201)


#Validation Routes

@app.route("/api/validation/<string:ticket_code>/")
def validate_ticket(ticket_code):
    """
    Endpoint for checking if the string parameter 'ticket_code' has been assigned to
    a previously created ticket.

    Returns true if the ticket passes through all validation checks.
    """
    valid_ticket = Ticket.query.filter_by(code = ticket_code).first()
    if valid_ticket is not None and valid_ticket.expiration is not None:
        valid_ticket.expiration = valid_ticket.expiration[:19]
        valid_ticket.expiration = datetime.strptime(valid_ticket.expiration, '%Y-%m-%d %H:%M:%S')

    if valid_ticket is None:
        return success_response(("Ticket code isn't valid", False))
    elif valid_ticket.is_used:
        return success_response(("Ticket is already used", False))
    elif valid_ticket.expiration is not None and valid_ticket.expiration < datetime.today():
        return success_response(("Ticket is expired", False))

    return success_response(("Ticket is valid", True))


# App functions
"""
Generates alpha-numeric code of length 'size'.
Letters are capitalized
'size' is an int
"""
def generate_code(size):
    assert type(size) == int
    code = ""
    for i in range(size):
        choose = random.randint(0,1)
        if (choose):
            code += random.choice(string.ascii_uppercase)
        else:
            code += str(random.randint(0,9))
    return code


"""
Returns a string representing the date of expiration, which is 'validity'
days after the current date and time.
'validity' is a string in the format 'YYYY-MM-DD'
"""
def get_expiration(validity):
    today = datetime.today()
    return today + timedelta(days=validity)


#Host the App

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)