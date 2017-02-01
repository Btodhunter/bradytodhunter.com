from flask_wtf import FlaskForm as Form
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email
from app.models import User


class EditForm(Form):
    nickname = StringField('nickname', validators=[DataRequired()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])
    email = StringField('email', validators=[DataRequired(), Email()])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user is not None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


class LoginForm(Form):
    remember_me = BooleanField('remember_me', default=False)


class PostForm(Form):
    post = TextAreaField('post', validators=[Length(min=0, max=140), DataRequired()])


class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])

