import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Business
from utils import seed_default_menu
from datetime import datetime, timedelta
from flask_login import login_user

def build_static_site():
    print("Building static export for GitHub Pages...")
    app = create_app()
    app.config['TESTING'] = True

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = os.path.join(project_root, 'dist')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)

    # Copy static assets to dist/static
    static_src = os.path.join(project_root, 'static')
    static_dest = os.path.join(dist_dir, 'static')
    if os.path.exists(static_src):
        shutil.copytree(static_src, static_dest)
        print(f"Copied static assets to {static_dest}")

    with app.app_context():
        # Ensure a demo business user exists for rendering authenticated pages
        demo_user = Business.query.filter_by(username='demopos').first()
        if not demo_user:
            demo_user = Business(
                business_name="Tokenly Demo POS",
                owner_name="Demo Manager",
                phone="9876543210",
                username="demopos",
                theme_preference="crimson",
                subscription_active=True,
                subscription_start=datetime.utcnow(),
                subscription_expires=datetime.utcnow() + timedelta(days=365)
            )
            demo_user.set_password("demo1234")
            db.session.add(demo_user)
            db.session.commit()
            seed_default_menu(demo_user.id)

        client = app.test_client()

        # Perform login session setup
        with client.session_transaction() as sess:
            sess['_user_id'] = str(demo_user.id)
            sess['_fresh'] = True

        pages = {
            'index.html': '/login',
            'register.html': '/register',
            'login.html': '/login',
            'pos.html': '/pos',
            'menu.html': '/admin/',
            'history.html': '/history/',
            'subscription.html': '/subscription',
            '404.html': '/register'
        }

        for filename, route in pages.items():
            res = client.get(route, follow_redirects=True)
            if res.status_code == 200:
                html_content = res.data.decode('utf-8')
                
                # Replace absolute static URL references with relative paths
                html_content = html_content.replace('/static/', './static/')
                html_content = html_content.replace('/register', 'register.html')
                html_content = html_content.replace('/login', 'login.html')
                html_content = html_content.replace('/pos', 'pos.html')
                html_content = html_content.replace('/admin/', 'menu.html')
                html_content = html_content.replace('/history/', 'history.html')

                file_path = os.path.join(dist_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"[OK] Generated {filename} from route {route}")
            else:
                print(f"[FAIL] Warning: Failed to fetch route {route} (Status {res.status_code})")

    print("\nStatic build complete! Output directory: dist/")

if __name__ == '__main__':
    build_static_site()
