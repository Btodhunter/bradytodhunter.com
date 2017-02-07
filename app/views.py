from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import EditForm, PostForm, SearchForm
from .models import User, Post, FavoriteURL, LastUpdateTime
from oauth import OAuthSignIn
from datetime import datetime, timedelta
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, VIDEOS_PER_PAGE
from fav_vids import get_page_numbers, get_video_url, get_embed_page

lm.login_view = 'login'


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/blog')
@app.route('/blog/<int:page>')
def blog(page=1):
    if g.user.is_authenticated:
        posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    else:
        posts = User.query.filter_by(social_id='facebook$10154223194231526').first().posts.paginate(page, POSTS_PER_PAGE, False)
    return render_template('blog.html',
                           title='My Blog',
                           posts=posts)


@app.route('/resume')
def resume():
    return render_template('resume.html', title='Resume')


@app.route('/login')
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('login'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('login'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        nickname = User.make_unique_nickname(username)
        user = User(social_id=social_id, nickname=nickname, email=email)
        db.session.add(user)
        db.session.commit()
        # make the user follow him/herself & Brady
        db.session.add(user.follow(user))
        db.session.add(user.follow(User.query.filter_by(social_id='facebook$10154223194231526').first()))
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()


@app.route('/user/<nickname>', methods=['GET', 'POST'])
@app.route('/user/<nickname>/<int:page>', methods=['GET', 'POST'])
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)

    return render_template('user.html',
                           user=user,
                           posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        g.user.email = form.email.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.email.data = g.user.email
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('user', nickname=g.user.nickname))

    return render_template('create_post.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('index'))
    if user == g.user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('user', nickname=nickname))


@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html',
                           query=query,
                           results=results)


@app.route('/favorite_videos')
@app.route('/favorite_videos/<int:page>')
def fav_vids(page=1):
    today = datetime.now()

    try:
        last_updated = LastUpdateTime.query.all()[0].date
    except IndexError:
        last_updated = today - timedelta(1)
        db.session.add(LastUpdateTime(date=last_updated))
        db.session.commit()

    if (today - last_updated) > timedelta(days=1):
        updated = LastUpdateTime.query.filter_by(id=1).first()
        updated.date = today
        db.session.add(updated)
        db.session.commit()

        page_urls = get_video_url(get_page_numbers())
        db_urls = set()

        for url in FavoriteURL.query.all():
            db_urls.add(url.url)

        if not db_urls:
            for url in page_urls:
                db.session.add(FavoriteURL(url=url))
                db.session.commit()

            favorites = FavoriteURL.query.with_entities(FavoriteURL.url).paginate(page, VIDEOS_PER_PAGE, False)

        elif set(page_urls).symmetric_difference(db_urls):
            for url in (page_urls - db_urls):
                db.session.add(FavoriteURL(url=url))
                db.session.commit()

            for url in (db_urls - page_urls):
                db.session.delete(FavoriteURL.query.filter_by(url=url).first())
                db.session.commit()

            favorites = FavoriteURL.query.with_entities(FavoriteURL.url).paginate(page, VIDEOS_PER_PAGE, False)

        else:
            favorites = FavoriteURL.query.with_entities(FavoriteURL.url).paginate(page, VIDEOS_PER_PAGE, False)

    else:
        favorites = FavoriteURL.query.with_entities(FavoriteURL.url).paginate(page, VIDEOS_PER_PAGE, False)

    return render_template('favorite_videos.html', title='My Favorite Videos', favorites=favorites)


@app.route('/embed_video/<video_id>')
def embed_video(video_id):
    embeded_html = get_embed_page(video_id)

    return render_template('embed_video.html', embeded_html=embeded_html)