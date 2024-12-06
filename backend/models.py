# backend/models.py

from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Should store hashed passwords
    role = db.Column(db.String(50), nullable=False, default='user')  # Roles: user, admin, agent, referrer
    leads = db.relationship('Lead', backref='referrer', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    loan_tenure = db.Column(db.Integer, nullable=False)  # in years
    current_repayment = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='New')  # Status: New, In Progress, Closed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lead {self.id} - {self.name}>"

class BankPackage(db.Model):
    __tablename__ = 'bank_packages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)  # Annual interest rate in percentage
    tenure_options = db.Column(db.String(200), nullable=False)  # Comma-separated list of tenure options (years)

    def __repr__(self):
        return f"<BankPackage {self.name}>"
