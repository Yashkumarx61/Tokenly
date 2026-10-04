from app import app
from models import db, Business, Category, MenuItem
from utils import seed_default_menu
from datetime import datetime, timedelta

def seed_demo_data():
    with app.app_context():
        db.create_all()
        
        demo = Business.query.filter_by(username='sharmafastfood').first()
        if not demo:
            demo = Business(
                business_name='Sharma Fast Food',
                owner_name='Rahul Sharma',
                phone='9876543210',
                username='sharmafastfood',
                theme_preference='crimson',
                address='Shop 12, Main Market, Delhi',
                gstin='07AAAAA0000A1Z5',
                subscription_active=True,
                subscription_start=datetime.utcnow(),
                subscription_expires=datetime.utcnow() + timedelta(days=365)
            )
            demo.set_password('password123')
            db.session.add(demo)
            db.session.commit()
            
            seed_default_menu(demo.id)
            print("Demo business 'Sharma Fast Food' created successfully!")
        else:
            print("Demo business 'Sharma Fast Food' already exists.")

if __name__ == '__main__':
    seed_demo_data()
