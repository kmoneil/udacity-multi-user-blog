import os
import re
import hmac
import json
import jinja2
import hashlib
import webapp2

from slugify import slugify
from time import sleep
from google.appengine.ext import db

# Setup jinja template path
templates = os.path.join(os.path.dirname(__file__), 'templates')

# Setup the templete enviroment
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates),
                               extensions=['jinja2.ext.autoescape'],
                               autoescape=True)

# Your secret key for hashing
secret = 'NWBYSPF9iiiZVHCTcSJKjafPUG1L6Z8CETC2ffME0qpCsJsfrqfY5hBAxawO7ouu'


def cookie_hash_value(value):
    """Returns a value and hash separated by a pipe |"""

    return '%s|%s' % (value, hmac.new(secret, str(value)).hexdigest()) \
        if value else None


def is_valid_cookie(cookie):
    """Check if a cookie is valid"""

    if cookie:
        return cookie_hash_value(cookie.split("|")[0])


def is_valid_email(email):
    """Check if email address is valid"""

    return re.match(r'^[\S]+@[\S]+\.[\S]+$', email)


def get_password_hash(password):
    """Returns password hash"""

    return hashlib.sha512(password + secret).hexdigest()


class AppHandler(webapp2.RequestHandler):
    """Basic class to define the basic properties of a Movie."""

    def is_user_logged_in(self):
        cookie = self.read_cookie('user_id')
        if cookie:
            return User.by_id(cookie.split('|')[0])

    def get_current_user(self):
        return self.is_user_logged_in()

    def read_cookie(self, id):
        return is_valid_cookie(self.request.cookies.get(id))

    def set_cookie(self, id, value):
        cookie_data = cookie_hash_value(value)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/'
                                         % (id, cookie_data))

    def delete_cookie(self, id):
        self.response.headers.add_header('Set-Cookie', '%s=; Path=/' % id)


class Login(AppHandler):
    """Class to handle the login page."""

    def get(self):
        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("login.html")
        self.response.write(rendered_template.render())

    def post(self):
        errors = {}
        username = self.request.get("username")
        password = self.request.get("password")

        if not username:
            errors["username"] = "Please enter a valid username."

        if not password:
            errors["password"] = "Please enter a valid password."

        if not errors:
            user = User.login(username, password)
            if user:
                self.set_cookie("user_id", user.key().id())
                return self.redirect("/")
            else:
                errors["nouser"] = True

        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("login.html")
        self.response.write(rendered_template.render(errors=errors))


class Logout(AppHandler):
    """Class to handle the logout page."""

    def get(self):
        self.delete_cookie("user_id")
        return self.redirect("/")


class Blog(AppHandler):
    """Class to handle the index / home page.

       Will display 10 latest blog posts.
    """

    def get(self):
        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("index.html")

        # Fetch 10 of the most recent posts
        posts = Post.all().order("-created").fetch(10)

        # see if user is logged in and get user.
        user = self.get_current_user()

        self.response.write(rendered_template.render(user=user, posts=posts))


class PostShow(AppHandler):
    """Class to handle a blog post page.

       Will display the post and comments for the post.
    """

    def get(self, post_id, slug):

        print "%s -- %s" % (post_id, slug)

        user = self.get_current_user()
        post = Post.by_id_slug(post_id, slug)

        if not post:
            return self.redirect('/error/404')
        else:
            self.response.headers["Content-Type"] = "text/html"
            rendered_template = jinja_env.get_template("post.html")
            self.response.write(rendered_template.render(user=user, post=post))


class PostByAuthor(AppHandler):
    """Class to show all posts by a given author."""

    def get(self, username):
        user = self.get_current_user()
        blog_author = User.by_username(username)

        if not blog_author:
            return self.redirect('/error/404')
        else:
            self.response.headers["Content-Type"] = "text/html"
            rendered_template = jinja_env.get_template("user.html")
            self.response.write(rendered_template.render(user=user,
                                blog_author=blog_author))


class Register(AppHandler):
    """Class to handle the registration page."""

    def get(self):
        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("register.html")
        self.response.write(rendered_template.render())

    def post(self):
        # Set errors to empty
        errors = {}

        # Get all request vars
        username = self.request.get("username")
        password = self.request.get("password")
        verify_password = self.request.get("verify_password")
        email = self.request.get("email")

        if not username:
            errors["username"] = "Please enter a valid username."
        elif User.by_username(username):
            errors["username"] = """Username is already in use. Please choose
                                    a different username."""

        if not password:
            errors["password"] = "Please enter a password."
        elif not password == verify_password:
            errors["password"] = "Password do not match."

        if email:
            if not is_valid_email(email):
                errors["email"] = "Please enter a valid email."
            elif User.by_email(email):
                errors["email"] = "Email address is already in use."

        # If no errors add user
        if not errors:
            user_id = User.add_user(username, password, email)
            self.set_cookie("user_id", user_id)
            return self.redirect("/")

        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("register.html")
        self.response.write(rendered_template.render(username=username,
                            email=email, errors=errors))


class PostCreate(AppHandler):
    """Class to handle the create new post page."""

    def get(self):
        user = self.get_current_user()

        if not user:
            return self.redirect("/login")

        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("create_post.html")
        self.response.write(rendered_template.render(user=user))

    def post(self):
        user = self.get_current_user()

        if not user:
            return self.redirect("/login")

        errors = {}
        title = self.request.get("title")
        body = self.request.get("body")

        if not title:
            errors["title"] = "Please enter a valid title."

        if not body:
            errors["body"] = "Please enter a valid body."

        if not errors:
            slug = slugify(title)
            post = Post(user=user, slug=slug, title=title, body=body)
            post.put()

            # Sleeping for 100ms you can avoid the eventual consistency
            sleep(.1)

            return self.redirect("/blog/%s/%s" % (post.key().id(), slug))

        self.response.headers["Content-Type"] = "text/html"
        rendered_template = jinja_env.get_template("create_post.html")
        self.response.write(rendered_template.render(user=user,
                            post_title=title, post_body=body,
                            errors=errors))


class PostEdit(AppHandler):
    """Class to handle the edit post page."""

    def get(self, post_id, slug):
        user = self.get_current_user()

        if not user:
            return self.redirect("/login")
        else:
            post = Post.by_id_slug(post_id, slug)

            if post and post.user.key().id() == user.key().id():
                self.response.headers["Content-Type"] = "text/html"
                rendered_template = jinja_env.get_template("edit_post.html")
                self.response.write(rendered_template.render(user=user,
                                    post=post, errors={}))
            else:
                return self.redirect('/error/404')

    def post(self, post_id, slug):
        user = self.get_current_user()

        if not user:
            return self.redirect("/login")

        post = Post.by_id_slug(post_id, slug)

        if post:
            if post.user.key().id() == user.key().id():
                errors = {}
                title = self.request.get("title")
                body = self.request.get("body")

                if not title:
                    errors["title"] = "Please enter a valid title."

                if not body:
                    errors["body"] = "Please enter a valid body."

                if not errors:
                    slug = slugify(title)
                    post.slug = slug
                    post.title = title
                    post.body = body
                    post.put()

                    # Sleeping 100ms you can avoid the eventual consistency
                    sleep(.1)

                    return self.redirect("/blog/%s/%s" % (post.key().id(),
                                         slug))
                else:
                    self.response.headers["Content-Type"] = "text/html"
                    rendered_template = jinja_env.get_template(
                                            "edit_post.html"
                                        )
                    self.response.write(rendered_template.render(user=user,
                                        post=post, errors=errors))
            else:
                return self.redirect('/error/403')
        else:
            return self.redirect('/error/404')


class PostDelete(AppHandler):
    """Class to delete a post."""

    def post(self):
        user = self.get_current_user()

        # This is only for ajax requests
        if self.request.headers['X-Requested-With'] == 'XMLHttpRequest':
            response = {
                "status": 200,
                "redirect": "/"
            }

            if not user:
                response['status'] = '401'
                response['redirect'] = '/login'
            else:
                post = Post.by_id_user(self.request.get('id'), user)

                if post:
                    comments = Comment.by_post(post)
                    if comments:
                        for cmt in comments:
                            cmt.delete()

                    likes = PostLike.by_post(post)
                    if likes:
                        for like in likes:
                            like.delete()

                    post.delete()

                    # Sleeping 100ms you can avoid the eventual consistency
                    sleep(.1)
                else:
                    response['status'] = '403'
                    response['redirect'] = '/error/403'

            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(response))


class CommentDelete(AppHandler):
    """Class to delete a comment."""

    def post(self):
        user = self.get_current_user()

        if self.request.headers['X-Requested-With'] == 'XMLHttpRequest':
            response = {
                "status": 200,
                "redirect": self.request.referer
            }

            if not user:
                response['status'] = '401'
                response['redirect'] = '/login'
            else:
                comment = Comment.by_id_user(self.request.get('id'), user)

                if comment:
                    comment.delete()

                    # Sleeping 100ms you can avoid the eventual consistency
                    sleep(.1)
                else:
                    response['status'] = '403'
                    response['redirect'] = '/error/403'

            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(response))


class CommentCreate(AppHandler):
    """Class to post a comment."""

    def post(self):
        user = self.get_current_user()

        if not user:
            return self.redirect("/login")
        else:
            comment = self.request.get("comment").strip("\s\t\n\r")

            if len(comment) < 10:
                return self.redirect(self.request.referer)
            else:
                post = Post.get_by_id(int(self.request.get("post_ref")))

                if not post:
                    return self.redirect(self.request.referer)
                else:
                    comment = Comment(user=user, post=post, comment=comment)
                    comment.put()

                    # Sleeping 100ms you can avoid the eventual consistency
                    sleep(.1)

                    # redirect back to the post to see the ocmment
                    return self.redirect(self.request.referer)


class CommentEdit(AppHandler):
    """Class to edit a comment."""

    def post(self):
        user = self.get_current_user()

        if self.request.headers["X-Requested-With"] == "XMLHttpRequest":
            response = {
                "status": 200,
                "redirect": ""
            }

            if not user:
                response["status"] = "401"
                response["redirect"] = "/login"
            else:
                body = self.request.get("comment").strip("\s\t\n\r")

                if body:
                    comment = Comment.by_id_user(self.request.get("id"), user)

                    if comment:
                        comment.comment = body
                        comment.put()

                        # Sleeping 100ms to avoid the eventual consistency
                        sleep(.1)
                    else:
                        response["status"] = "403"
                        response["redirect"] = "/error/403"

            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(response))


class LikePost(AppHandler):
    """Class to like a post."""

    def post(self):
        user = self.get_current_user()

        # This is only for ajax requests
        if self.request.headers["X-Requested-With"] == "XMLHttpRequest":
            response = {
                "status": 200,
                "redirect": ""
            }

            if not user:
                response["status"] = "401"
                response["redirect"] = "/login"
            else:
                post = Post.get_by_id(int(self.request.get("post_ref")))

                if not post:
                    response["status"] = "404"
                    response["redirect"] = "/login"
                else:
                    # Make user the user cannot like their own posts.
                    if not user.key().id() == post.user.key().id():
                        # Check to see if already liked, if so, unlike
                        liked_post = PostLike.by_user_post(user, post)

                        if liked_post:
                            liked_post.delete()
                        else:
                            like = PostLike(user=user, post=post)
                            like.put()

                        # Sleeping 100ms to avoid the eventual consistency
                        sleep(.1)
                    else:
                        response["status"] = "403"
                        response["redirect"] = "/error/403"

            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(response))


class NotFoundPageHandler(webapp2.RequestHandler):
    """Class to handle a page not found."""

    def get(self):
        return self.redirect("/error/404")


class ShowError(AppHandler):
    """Class to handle error pages."""

    def get(self, error):
        # Get user if they're logged in.
        user = self.get_current_user()

        self.response.headers["Content-Type"] = "text/html"

        errorTmp = "errors/" + error + ".html"

        if os.path.exists(templates + "/" + errorTmp):
            rendered_template = jinja_env.get_template(errorTmp)
            self.error(error)
            self.response.write(rendered_template.render(user=user))
        else:
            return self.redirect('/error/404')


# DB models
class User(db.Model):
    """Class represents the structure of entities
       stored in the Datastore for the users.
    """

    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def by_id(cls, id):
        return User.get_by_id(int(id), parent=None)

    @classmethod
    def by_username(cls, username):
        return User.gql("WHERE username = :username", username=username).get()

    @classmethod
    def add_user(cls, username, password, email=""):
        user = User(username=username,
                    password=get_password_hash(password),
                    email=email)

        user.put()

        return user.key().id()

    @classmethod
    def login(cls, username, password):
        return User.gql("WHERE username = :username AND password = :password",
                        username=username,
                        password=get_password_hash(password)).get()


class Post(db.Model):
    """Class represents the structure of entities
       stored in the Datastore for the posts.
    """

    user = db.ReferenceProperty(User, collection_name='posts', required=True)
    slug = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def by_id_slug(cls, id, slug):
        return Post.gql("WHERE __key__ = KEY('Post', :id) AND slug = :slug",
                        id=int(id), slug=slug).get()

    @classmethod
    def by_id_user(cls, id, user):
        return Post.gql("WHERE __key__ = KEY('Post', :id) AND user = :user",
                        id=int(id), user=user).get()


class Comment(db.Model):
    """Class represents the structure of entities
       stored in the Datastore for the post comments.
    """

    user = db.ReferenceProperty(User, collection_name='comments',
                                required=True)
    post = db.ReferenceProperty(Post, collection_name='comments',
                                required=True)
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def by_post(cls, post):
        return Comment.gql("WHERE post = :post", post=post)

    @classmethod
    def by_id_user(cls, id, user):
        return Comment.gql("WHERE __key__ = KEY('Comment', :id) AND user = \
                            :user", id=int(id), user=user).get()


class PostLike(db.Model):
    """Class represents the structure of entities
       stored in the Datastore for the post likes.
    """

    user = db.ReferenceProperty(User, collection_name='likes', required=True)
    post = db.ReferenceProperty(Post, collection_name='likes', required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    @classmethod
    def by_post(cls, post):
        return PostLike.gql("WHERE post = :post", post=post)

    @classmethod
    def by_user_post(cls, user, post):
        return PostLike.gql("WHERE user = :user AND post = :post", user=user,
                            post=post).get()


app = webapp2.WSGIApplication([("/?", Blog),
                              ("/login", Login),
                              ("/logout", Logout),
                              ("/register", Register),
                              ("/post/create", PostCreate),
                              ("/post/delete", PostDelete),
                              ("/post/like", LikePost),
                              ("/post/edit/([0-9]+)/([a-z0-9\-]+)", PostEdit),
                              ("/blog/([0-9]+)/([a-z0-9\-]+)", PostShow),
                              ("/author/@([a-z0-9\-]+)", PostByAuthor),
                              ("/comment", CommentCreate),
                              ("/comment/delete", CommentDelete),
                              ("/comment/update", CommentEdit),
                              ("/error/([0-9]+)", ShowError),
                              ("/.*", NotFoundPageHandler)],
                              debug=True)
