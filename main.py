"""
KawaLove app - create database of cafes in Poznan and remote workers' reviews who work there.

"""

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, logout_user, LoginManager, current_user, \
    login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, CafeForm, ReviewForm, SearchForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cd6bd383d4886c1345a9a3ed337407c16cddcce2'
ckeditor = CKEditor(app)
Bootstrap(app)

# DB CONNECTION
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# TABLES CONFIGURATION


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # parent relationship with review
    reviews = relationship('Review', back_populates='review_author')


class Cafe(db.Model):
    __tablename__ = 'cafes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(255))
    map_url = db.Column(db.String(255), nullable=False)
    open = db.Column(db.String(50))
    close = db.Column(db.String(50))

    # info
    has_food = db.Column(db.Boolean)
    has_cakes = db.Column(db.Boolean)
    has_toilet = db.Column(db.Boolean)
    allow_long_stays = db.Column(db.Boolean)
    allow_calls = db.Column(db.Boolean)

    avg_rating = db.Column(db.Float)
    avg_coffee = db.Column(db.String)
    avg_wifi = db.Column(db.String)
    avg_power = db.Column(db.String)

    # price
    americano_price = db.Column(db.Float)
    cake_price = db.Column(db.Float)


    # parent relationship with review
    reviews = relationship('Review', back_populates='parent_cafe')



class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    user_rating = db.Column(db.String)
    coffee = db.Column(db.String)
    wifi = db.Column(db.String)
    power = db.Column(db.String)


    # child relationship with author
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_author = relationship("User", back_populates="reviews")

    # child relationship with cafe
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id"))
    parent_cafe = relationship("Cafe", back_populates="reviews")


with app.app_context():
    db.create_all()


def checkbox_to_bolean(answer):
    if answer == 'y':
        return True
    return False

def icon_to_number(score):
    if score == '✘':
        return 0
    return len(score)

def number_to_icon(score, icon):
    return score * icon

def update_avg_ratings(cafe):
    all_reviews = Review.query.filter_by(parent_cafe=cafe).all()
    ratings_sum = [0, 0, 0, 0]
    for review in all_reviews:
        ratings_sum[0] += icon_to_number(review.user_rating)
        ratings_sum[1] += icon_to_number(review.coffee)
        ratings_sum[2] += icon_to_number(review.wifi)
        ratings_sum[3] += icon_to_number(review.power)

    avg_ratings = [rating_sum/len(all_reviews) for rating_sum in ratings_sum]
    updated_ratings = change_ratings_to_good_type(avg_ratings)
    return updated_ratings

def change_ratings_to_good_type(ratings):
    avg_rating = round(ratings[0], 1)
    avg_coffee = number_to_icon(round(ratings[1]), '☕')
    avg_wifi = number_to_icon(round(ratings[2]), '📶')
    avg_power = number_to_icon(round(ratings[3]), '🔌')
    return [avg_rating, avg_coffee, avg_wifi, avg_power]


# login manager
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.id != 1:
            return abort(403)
        return function(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)


# logging
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(email=request.form.get('email')).first():
                flash('Konto już zarejestrowane, zaloguj się poniżej')
                return redirect(url_for('login'))

            safe_password = generate_password_hash(
                password=request.form.get('password'),
                method="pbkdf2:sha256",
                salt_length=16,
            )
            new_user = User(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=safe_password,
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for('home'))

                flash('Hasło nieprawidłowe, spróbuj ponownie')
                return redirect(url_for('login'))

            flash('Nie znaleziono użytkownika o podanym adresie email')
            return redirect(url_for('login'))

    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@login_required
@app.route('/add', methods=['GET', 'POST'])
def add():
    form = CafeForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if Cafe.query.filter_by(name=request.form.get('name')).first():
                flash('Kawiarnia już jest u nas w bazie, koniecznie dodaj swoją recenzję!')
                return redirect(url_for('add'))
            new_cafe = Cafe(
                name=request.form.get('name'),
                location=request.form.get('location'),
                district=request.form.get('district'),
                img_url=request.form.get('img_url'),
                map_url=request.form.get('map_url'),
                open=request.form.get('open'),
                close=request.form.get('close'),
                has_food=checkbox_to_bolean(request.form.get('has_food')),
                has_cakes=checkbox_to_bolean(request.form.get('has_cakes')),
                has_toilet=checkbox_to_bolean(request.form.get('has_toilet')),
                allow_long_stays=checkbox_to_bolean(request.form.get('allow_long_stays')),
                allow_calls=checkbox_to_bolean(request.form.get('allow_calls')),
                americano_price=request.form.get('americano_price'),
                cake_price=request.form.get('cake_price'),
            )

            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for('show_all'))

    return render_template('add.html', form=form, current_user=current_user)


@app.route('/cafes', methods=['GET', 'POST'])
def show_all():
    cafes = db.session.query(Cafe).order_by(Cafe.avg_rating.desc()).all()
    form = SearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user_district = request.form.get('district')
            return redirect(url_for('show_district', district=user_district))

    return render_template('all.html', cafes=cafes, form=form)


@app.route('/cafes?district=<district>', methods=['GET', 'POST'])
def show_district(district):
    form = SearchForm()
    if district == 'POZNAŃ':
        return redirect(url_for('show_all'))

    cafes = Cafe.query.filter_by(district=district).order_by(Cafe.avg_rating.desc()).all()
    if request.method == 'POST':
        if form.validate_on_submit():
            user_district = request.form.get('district')
            return redirect(url_for('show_district', district=user_district))

    return render_template('all.html', cafes=cafes, form=form)


@app.route('/cafe/<int:cafe_id>', methods=['GET', 'POST'])
def show_cafe(cafe_id):
    requested_cafe = db.session.get(Cafe, cafe_id)
    form = ReviewForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash('Musisz być zalogowany, aby dodać komentarz.')
                return redirect(url_for('login'))

            new_review = Review(
                user_rating=request.form.get('user_rating'),
                coffee=request.form.get('coffee'),
                wifi=request.form.get('wifi'),
                power=request.form.get('power'),
                text=form.text.data,
                review_author=current_user,
                parent_cafe=requested_cafe
            )
            db.session.add(new_review)
            db.session.commit()
            new_avg_scores = update_avg_ratings(requested_cafe)
            requested_cafe.avg_rating = new_avg_scores[0]
            requested_cafe.avg_coffee = new_avg_scores[1]
            requested_cafe.avg_wifi = new_avg_scores[2]
            requested_cafe.avg_power = new_avg_scores[3]
            db.session.commit()

    return render_template('cafe.html', form=form, cafe=requested_cafe, current_user=current_user)


@app.route('/edit/<int:cafe_id>', methods=['GET', 'POST'])
@admin_only
def edit(cafe_id):
    cafe_to_update = db.session.get(Cafe, cafe_id)
    edit_form = CafeForm(
        name=cafe_to_update.name,
        location=cafe_to_update.location,
        district=cafe_to_update.district,
        img_url=cafe_to_update.img_url,
        map_url=cafe_to_update.map_url,
        open=cafe_to_update.open,
        close=cafe_to_update.close,
        has_food=cafe_to_update.has_food,
        has_cakes=cafe_to_update.has_cakes,
        has_toilet=cafe_to_update.has_toilet,
        allow_long_stays=cafe_to_update.allow_long_stays,
        allow_calls=cafe_to_update.allow_calls,
        americano_price=cafe_to_update.americano_price,
        cake_price=cafe_to_update.cake_price
    )
    if request.method == 'POST':
        if edit_form.validate_on_submit():
            cafe_to_update.name = edit_form.name.data
            cafe_to_update.location = edit_form.location.data
            cafe_to_update.district = edit_form.district.data
            cafe_to_update.img_url = edit_form.img_url.data
            cafe_to_update.map_url = edit_form.map_url.data
            cafe_to_update.open = edit_form.open.data
            cafe_to_update.close = edit_form.close.data
            cafe_to_update.has_food = edit_form.has_food.data
            cafe_to_update.has_cakes = edit_form.has_cakes.data
            cafe_to_update.has_toilet = edit_form.has_toilet.data
            cafe_to_update.allow_long_stays = edit_form.allow_long_stays.data
            cafe_to_update.allow_calls = edit_form.allow_calls.data
            cafe_to_update.americano_price = edit_form.americano_price.data
            cafe_to_update.cake_price = edit_form.cake_price.data
            db.session.commit()
            return redirect(url_for('home'))

    return render_template('edit.html', form=edit_form, current_user=current_user)


@admin_only
@app.route('/delete/<int:cafe_id>')
def delete(cafe_id):
    cafe_to_delete = db.session.get(Cafe, cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('home'), current_user=current_user)


if __name__ == '__main__':
    app.run(debug=True)
