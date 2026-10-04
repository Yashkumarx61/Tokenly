from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, NumberRange
from models import Business

class RegistrationForm(FlaskForm):
    business_name = StringField('Business Name', validators=[
        DataRequired(message="Business name is required"),
        Length(min=2, max=120)
    ])
    owner_name = StringField('Owner Full Name', validators=[
        DataRequired(message="Owner name is required"),
        Length(min=2, max=100)
    ])
    phone = StringField('Mobile Number', validators=[
        DataRequired(message="Mobile number is required"),
        Length(min=10, max=15)
    ])
    username = StringField('Choose Username / Business ID', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=60)
    ])
    password = PasswordField('Create Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=6, max=100)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Start Free Trial & Access Terminal →')

    def validate_username(self, username):
        user = Business.query.filter_by(username=username.data.strip().lower()).first()
        if user:
            raise ValidationError('Username/Business ID is already registered. Please choose another or login.')


class LoginForm(FlaskForm):
    username = StringField('Username / Business ID', validators=[
        DataRequired(message="Please enter your username")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Please enter your password")
    ])
    submit = SubmitField('Login to Terminal')


class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[
        DataRequired(message="Item name is required"),
        Length(min=2, max=100)
    ])
    category_id = SelectField('Category', coerce=int, validators=[
        DataRequired(message="Please select a category")
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=300)])
    half_price = FloatField('Half Portion Price (₹)', validators=[
        Optional(),
        NumberRange(min=0, message="Price cannot be negative")
    ])
    full_price = FloatField('Full Portion Price (₹)', validators=[
        DataRequired(message="Full portion price is required"),
        NumberRange(min=1, message="Price must be greater than 0")
    ])
    image_url = StringField('Image URL', validators=[Optional(), Length(max=500)])
    is_veg = BooleanField('Is Veg Item', default=True)
    is_available = BooleanField('Is Available in Menu', default=True)
    submit = SubmitField('Save Item')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
        DataRequired(message="Category name is required"),
        Length(min=2, max=60)
    ])
    sort_order = IntegerField('Sort Order', default=1, validators=[Optional()])
    submit = SubmitField('Save Category')
