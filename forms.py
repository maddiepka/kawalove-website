from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, \
    URLField, SelectField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, URL
from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):
    email = EmailField('e-mail', validators=[DataRequired(), Email()])
    password = PasswordField('hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się!')


class RegisterForm(FlaskForm):
    name = StringField('nick', validators=[DataRequired()])
    email = EmailField('e-mail', validators=[DataRequired(), Email()])
    password = PasswordField('hasło', validators=[DataRequired()])
    submit = SubmitField('Zarejestruj się!')


class CafeForm(FlaskForm):
    name = StringField('nazwa', validators=[DataRequired()])
    location = StringField('adres', validators=[DataRequired()])
    district = SelectField('dzielnica', validators=[DataRequired()],
                           choices=['Jeżyce', 'Grunwald', 'Wilda',
                                    'Stare Miasto', 'Nowe Miasto'])
    img_url = URLField('zdjęcie', validators=[URL()])
    map_url = URLField('url do mapy', validators=[DataRequired(), URL()])
    open = StringField('Otwarcie', validators=[DataRequired()])
    close = StringField('Zamknięcie', validators=[DataRequired()])

    # info
    has_food = BooleanField('Oferuje jedzenie')
    has_cakes = BooleanField('Oferuje ciasta')
    has_toilet = BooleanField('Posiada toaletę')
    allow_long_stays = BooleanField('Możliwość długiego pobytu')
    allow_calls = BooleanField('Możliwość rozmów')

    # price
    americano_price = FloatField('~Cena americano')
    cake_price = FloatField('~Cena ciasta')
    submit = SubmitField('Dodaj!')


class ReviewForm(FlaskForm):
    # review
    user_rating = SelectField(label='Twoje KawaLove?', choices=[n * '🤎' for n in range(1, 6)])
    coffee = SelectField(label='Ocena kawy', choices=['✘', *(n * '☕' for n in range(1, 6))])
    wifi = SelectField(label='Dostęp do wifi', choices=['✘', *(n * '📶' for n in range(1, 6))])
    power = SelectField(label='Dostęp do gniazdka', choices=['✘', *(n * '🔌' for n in range(1, 6))])
    text = CKEditorField(label='Twój komentarz')
    submit = SubmitField('Dodaj!')


class SearchForm(FlaskForm):
    district = SelectField('Gdzie chcesz dziś napić się kawy?', validators=[DataRequired()],
                           choices=['POZNAŃ', 'Jeżyce', 'Grunwald', 'Wilda',
                                    'Stare Miasto', 'Nowe Miasto'])
    submit = SubmitField('Szukaj')