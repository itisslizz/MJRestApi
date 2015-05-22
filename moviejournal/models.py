from django.db import models
from django.contrib.auth.models import User


class MJUser(models.Model):
    user = models.OneToOneField(User)
    private = models.BooleanField(default=False)

    
# Create your models here.
class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    imdb_id = models.CharField(max_length=32)


class Screening(models.Model):
    movie = models.ForeignKey(Movie)
    owner = models.ForeignKey(User)
    time = models.DateTimeField('date added', auto_now_add=True)
    hidden = models.BooleanField(default=True)
    # users = models.ManyToManyField(User)


class Watchlist(models.Model):
    movie = models.ForeignKey(Movie)
    owner = models.ForeignKey(User)
    time = models.DateTimeField('date added', auto_now_add=True)
    time_removed = models.DateTimeField('date removed')
    hidden = models.BooleanField(default=True)


class Follow(models.Model):
    owner = models.ForeignKey(User, related_name='owner')
    following = models.ForeignKey(User, related_name='following')
    accepted = models.BooleanField(default=True)


class Review(models.Model):
    owner = models.ForeignKey(User)
    movie = models.ForeignKey(Movie)
    value = models.IntegerField()
    review = models.CharField(max_length=1024)
