from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET")
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-10-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), unique=True, nullable=False)
    rating = db.Column(db.Integer)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(500))
    img_url = db.Column(db.String(500), unique=True, nullable=False)


# db.drop_all()
# db.create_all()


class AddForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


class EditForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Submit")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    counter = len(movies)
    for movie in movies:
        movie.ranking = counter
        counter -= 1
    return render_template("index.html", movies=movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        title = form.title.data
        return redirect(url_for('select', title=title))
    return render_template("add.html", form=form)


@app.route("/search_results/<title>", methods=["GET", "POST"])
def select(title):
    params = {
        "languages": "en-US",
        "page": 1,
        "include_adult": False,
        "query": title
    }
    headers = {
        "Authorization": os.environ.get("TOKEN"),
        "Content-Type": "application/json;charset=utf-8"
    }
    movies = requests.get(url=f"https://api.themoviedb.org/3/search/movie", params=params, headers=headers).json()[
        'results']
    return render_template("select.html", movies=movies)


@app.route("/add_movie/<int:movie_id>", methods=["GET", "POST"])
def add_movie(movie_id):
    params = {
        "movie_id": movie_id
    }
    headers = {
        "Authorization": os.environ.get("TOKEN"),
        "Content-Type": "application/json;charset=utf-8"
    }
    movie = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params=params, headers=headers).json()
    title = movie['title']
    year = movie['release_date'].split('-')[0]
    description = movie['overview']
    img_url = f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}"
    new_movie = Movie(title=title, year=year, description=description, img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    movie_id = new_movie.id
    return redirect(url_for('edit', movie_id=movie_id))


@app.route("/edit/<int:movie_id>", methods=["POST", "GET"])
def edit(movie_id):
    form = EditForm()
    movie = Movie.query.filter_by(id=movie_id).first()

    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        movie.rating = rating
        movie.review = review
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
