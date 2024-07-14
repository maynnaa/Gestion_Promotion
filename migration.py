from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///promotion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'USER'

    email = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"User(email='{self.email}')"


# Add your migration logic here
def perform_migration():
    with app.app_context():
        db.create_all()  # Create all tables based on models
        print("Migration successful")


if __name__ == '__main__':
    perform_migration()
