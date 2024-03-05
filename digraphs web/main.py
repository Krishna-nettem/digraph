from flask import Flask, render_template,url_for, flash, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Alienx_best_allien_in_ben10'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()
books_authors = db.Table('books_authors',
    db.Column('book_id', db.Integer, db.ForeignKey('book.book_id')),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'))
)
class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    books = db.relationship('Book', secondary=books_authors, backref=db.backref('authors', lazy='dynamic'))
class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(50), nullable=False, unique=True)
    is_available = db.Column(db.String(10), nullable=False)
app.app_context().push()

@app.route("/")
def home() :
  return render_template("home.html")

@app.route("/add", methods = ['GET', 'POST'])
def add() : 
  if request.method == "POST":
    book_name = request.form.get("book_name")
    authors = request.form.get("author").split(',')
    is_available = request.form.get("is_available")

    existing_book = Book.query.filter_by(book_name=book_name).first()
    if existing_book:
        flash('A book with the same name already exists', 'danger')
        return render_template("add.html")

    if is_available and is_available.lower() not in ["yes", "no"]:
      flash('Invalid input for the book available', 'danger')
      return render_template("add.html")

    new_book = Book(book_name=book_name, is_available=is_available)

    for author_name in authors:
        author = Author.query.filter_by(name=author_name.strip()).first()
        if not author:
            author = Author(name=author_name.strip())
            db.session.add(author)
        new_book.authors.append(author)

    db.session.add(new_book)
    db.session.commit()

    flash('Book details added successfully', 'success')
    return redirect(url_for('home'))

  return render_template("add.html")


engine = create_engine('sqlite:///instance/db.sqlite3')
@app.route("/digraph")
def digraph():
  # create a session object
  Session = sessionmaker(bind=engine)
  session = Session()

  # query the database and get the book names and author names
  result = session.query(Book.book_name, Author.name).select_from(Book).join(books_authors, Book.book_id == books_authors.c.book_id).join(Author, Author.id == books_authors.c.author_id).all()

  # convert the query result into a pandas dataframe
  df = pd.DataFrame(result, columns=['book', 'author'])

  # create a digraph from the dataframe using networkx
  G = nx.from_pandas_edgelist(df, source='book', target='author', create_using=nx.DiGraph())

  # draw the graph using matplotlib
  nx.draw(G, with_labels=True, node_size=1000, node_color='lightblue', edge_color='gray')

  # save the graph as an image file
  plt.savefig("graph.png", format="PNG")

  # return the image file as a flask response
  return send_file("graph.png", mimetype='image/png')
  
if __name__ == "__main__":
  app.run(debug=True)



  