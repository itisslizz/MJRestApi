from moviejournal.models import *
from moviejournal.helper import obj_to_json, user_to_json

from tmdb.tmdb import TMDB
from rt.rt import RT

from django.db.models import Avg, Count
import sys


def check_movie(movie_id):
    """
    Takes a movie_id checks whether it is valid
    which is either retrieved or created if it does not exist.
    If the

    :type  movie_id: number
    :param movie_id: the id of the movie

    :rtype:          number
    :return:         HTTP Status Code (404, 200, 201)
    """
    if len(Movie.objects.filter(movie_id=movie_id)):
        return 200
    else:
        tmdb = TMDB()
        movie_info = tmdb.getMovieInfo(movie_id, 'en')
        if movie_info is None:
            return 404
        else:
            movie = Movie(movie_id, movie_info['imdb_id'])
            movie.save()
            return 201


def is_allowed(user, owner_id):
    """
    Checks whether a user is allowed to access
    the owners data

    :param user: the user who wants to access data
    :param owner_id: the owner_id of the owner of the data
    :return: a status code 403,404,200
    """
    owner = User.objects.filter(id=owner_id)
    if len(owner) == 0:
        return 404
    owner = owner[0]
    mj_owner = MJUser.objects.get(user=owner)
    print >>sys.stderr, mj_owner.private
    if mj_owner.private:
        follow = Follow.objects.filter(owner=user, following=owner)
        if len(follow) == 0:
            return 403
        elif not follow[0].accepted:
            return 403
    return 200


def get_movie_external(movie):
    """
    Takes a movie object and returns information from both
    TMDB and RottenTomatoes

    :param movie: the movie object we want info for
    :type  movie: Movie

    :return: info from TMDB and RT for movie

    """
    response = {}
    tmdb = TMDB()
    rt = RT()
    response['tmdb'] = tmdb.getMovieInfoTrailer(movie.movie_id, 'en')
    response['rt'] = rt.getMovieInfoFromImdb(movie.imdb_id[2:], 'en')
    return response


def get_movie_internal(movie, session_user, user=None):
    """
    Gets the moviejournal specific information for a movie

    :param movie:        movie for which we want the information
    :param session_user: the user that requested the movie
    :param user:         (optional) the user on which page the movie is viewed

    :return: the desired information
    """
    response = dict()
    # avg Rating
    response['avg_rating'] = Review.objects.filter(movie=movie).aggregate(Avg('value'))
    response['num_rating'] = len(Review.objects.filter(movie=movie))
    response['num_screenings'] = len(Screening.objects.filter(movie=movie))
    response['num_watchlist'] = len(Watchlist.objects.filter(movie=movie))

    # get all reviews from friends
    followees = Follow.objects.filter(owner=session_user, accepted=True).exclude(following=session_user)
    reviews = []
    #watchlists = []
    for followee in followees:
        review = Review.objects.filter(movie=movie, owner=followee)
        if len(review):
            reviews.append(obj_to_json(review[0]))
        #watchlist = Watchlist.objects.filter(movie=movie, owner=followee)
        #if len(watchlist):
        #    watchlists.append(watchlist[0])
    response['reviews'] = reviews
    #response['watchlists'] = watchlists
    return response


def get_movie(movie_id, user):
    """
    Returns all necessary info for a movie with a given id
    requested by a user
    
    :param movie_id: Id of the movie to be seen
    :param user: the user requesting it
    :return: The response or a 404 status if movie does not exist
    """
    response = dict()
    status = check_movie(movie_id)
    if status == 404:
        response['result'] = dict()
        response['status'] = 404
    else:
        result = dict()
        movie = Movie.objects.get(movie_id=movie_id)
        ext_info = get_movie_external(movie)
        result['tmdb'] = ext_info['tmdb']
        result['rt'] = ext_info['rt']
        result['mj'] = get_movie_internal(movie, user)
        response['result'] = result
        response['status'] = 200
    return response


"""
JOURNALS AND SCREENINGS
"""


def get_journal(user, owner_id, offset, size):
    """
    We check if user is allowed to see owners journal
    if so we return the journal

    :param user: the owner of the journal
    :param owner_id: the owner of the journal
    :param offset: offset of the screening_entries we want
    :param size: how many screenings we want
    :return: list of journal entries
    """
    response = dict()
    response['status'] = is_allowed(user, owner_id)
    response['result'] = {}
    if response['status'] != 200:
        return response
    owner = User.objects.get(id=owner_id)
    screening_list = Screening.objects.filter(owner=owner).order_by('-time')[offset:offset+size]
    response['result']['total'] = Screening.objects.filter(owner=owner).aggregate(Count('id'))['id__count']
    response['result']['offset'] = offset
    results = []
    for screening_raw in screening_list:
        screening = dict()
        ext = get_movie_external(screening_raw.movie)
        screening['tmdb'] = ext['tmdb']
        screening['rt'] = ext['rt']
        screening['review'] = obj_to_json(Review.objects.get(owner=owner, movie=screening_raw.movie))
        screening['info'] = obj_to_json(screening_raw)
        results.append(screening)
    response['result']['results'] = results
    return response


def get_screening(user, screening_id):
    """

    :param user: the user requesting the screening
    :param screening_id: the id of the requested screening
    :return: if allowed all the info of the screening
    """
    answer = dict()
    try:
        screening = Screening.objects.get(id=screening_id)
        answer['status'] = is_allowed(user, screening.owner.id)
        if answer['status'] != 200:
            return answer
        ext = get_movie_external(screening.movie)
        answer['tmdb'] = ext['tmdb']
        answer['rt'] = ext['rt']
        answer['info'] = obj_to_json(screening)
        answer['rating'] = obj_to_json(Review.objects.get(owner=screening.owner, movie=screening.movie))
    except Screening.DoesNotExist:
        answer['status'] = 404
    return answer


def post_screening(user, movie_id):
    """
    creates a new screening

    :param user: the user making the request
    :param movie_id: the id of the movie to post
    :return: status code (201 or 400)
    """
    success = check_movie(movie_id)
    if success == 404:
        return 400
    movie = Movie.objects.get(movie_id=movie_id)
    screening = Screening(owner=user, movie=movie)
    screening.save()

    if len(Review.objects.filter(owner=user, movie=movie)) == 0:
        review = Review(owner=user, movie=movie)
        review.value = 0
        review.review = ""
        review.save()
    return 201


def delete_screening(user, screening_id):
    """
    deletes a screening

    :param user: user that requests
    :param screening_id: screening to delete
    :return: status code
    """
    try:
        screening = Screening.objects.get(id=screening_id)
        if user.id != screening.owner.id:
            return 403
        screening.delete()
        return 204
    except Screening.DoesNotExist:
        return 404


"""
WATCHLIST AND ITS ENTRIES
"""


def get_watchlist(user, owner_id, offset, size):
    """

    :param user: the user making the request
    :param owner_id: the owner of the watchlist requested
    :param offset: offset of movies
    :param size: amount of movies requested
    :return:
    """
    answer = dict()
    answer['status'] = is_allowed(user, owner_id)
    if answer['status'] != 200:
        return answer
    owner = User.objects.get(id=owner_id)
    watchlist = Watchlist.objects.filter(owner=owner).order_by('time')[offset:offset+size]
    answer['total'] = Screening.objects.filter(owner=owner).aggregate(Count('id'))
    answer['offset'] = offset
    results = []
    for watchlist_raw in watchlist:
        watchlist_entry = dict()
        ext = get_movie_external(watchlist_raw.movie)
        watchlist_entry['tmdb'] = ext['tmdb']
        watchlist_entry['rt'] = ext['rt']
        watchlist_entry['info'] = watchlist_raw
        results.append(watchlist_entry)
    answer['results'] = results
    return answer


def post_watchlist_entry(user, movie_id):
    """
    creates a new watchlist_entry
    only allowed if not on watchlist already and no screening exists for this movie

    :param user: the user making the request
    :param movie_id: the id of the movie to post
    :return: status code (201 or 400)
    """
    success = check_movie(movie_id)
    if success == 404:
        return 400
    movie = Movie.objects.get(movie_id=movie_id)
    if Watchlist.objects.filter(movie=movie, owner=user)\
            + Screening.objects.filter(movie=movie, owner=user):
        return 400
    watchlist = Watchlist(owner=user, movie=movie)
    watchlist.save()

    return 201
    
    
def get_watchlist_entry(user, watchlist_entry_id):
    """

    :param user: the user requesting the watchlist_entry
    :param watchlist_entry_id: the id of the requested watchlist_entry
    :return: if allowed all the info of the screening
    """
    answer = dict()
    try:
        watchlist = Watchlist.objects.filter(id=watchlist_entry_id)
        answer['status'] = is_allowed(user, watchlist.owner.id)
        if answer['status'] != 200:
            return answer
        ext = get_movie_external(watchlist.movie)
        answer['tmdb'] = ext['tmdb']
        answer['rt'] = ext['rt']
        answer['info'] = watchlist
    except Screening.DoesNotExist:
        answer['status'] = 404
    return answer


def delete_watchlist_entry(user, watchlist_entry_id):
    """
    deletes a screening

    :param user: user that requests
    :param watchlist_entry_id: screening to delete
    :return: status code
    """
    try:
        watchlist = Watchlist.objects.get(id=watchlist_entry_id)
        if user.id != watchlist.owner.id:
            return 403
        watchlist.delete()
        return 204
    except Screening.DoesNotExist:
        return 404

"""
FOLLOWS
"""


def post_follow(owner, following_id):
    """
    creates a new follow entity/request
    need to check if there isn't already one and if user
    is private (needs to accept)

    :param owner: The user requesting the follow
    :param following_id: the user_id to follow
    :return: status code
    """
    try:
        following = User.objects.get(id=following_id)
        mj_following = MJUser.objects.get(user=following)
        if Follow.objects.filter(owner=owner, following=following):
            return 400

        follow = Follow(owner=owner, following=following)
        if mj_following.private:
            follow.accepted = False
        follow.save()
        return 204

    except User.DoesNotExist:
        return 404


def accept_follow(user, follow_id):
    """

    :param user: the user who wants to accept
    :param follow_id: the id of the request to be accepted
    :return: status code
    """
    try:
        follow = Follow.objects.get(id=follow_id)
        if follow.following == user:
            follow.accepted = True
            follow.save()
        else:
            return 403
    except Follow.DoesNotExist:
        return 404


def reject_follow(user, follow_id):
    """

    :param user: the user wo wants to reject
    :param follow_id: the id of the request to be rejected
    :return: status code
    """
    try:
        follow = Follow.objects.get(id=follow_id)
        if follow.following == user and not follow.accepted:
            follow.delete()
            return 203
        else:
            return 403
    except Follow.DoesNotExist:
        return 404


def delete_follow(user, follow_id):
    """

    :param user: the user who wants to delete the follow
    :param follow_id: the id of the follow to be deleted
    :return: status code
    """
    try:
        follow = Follow.objects.get(id=follow_id)
        if follow.owner == user:
            follow.delete()
            return 203
        else:
            return 403
    except Follow.DoesNotExist:
        return 404


"""
USERS
"""


def search_user(user, query):
    """
    Searches for a user
    :param user: the user issuing the search
    :param query:
    :return: a search result
    """
    response = dict()
    try:
        results_temp = User.objects.filter(username__icontains=query)
        results = []
        for result in results_temp:
            results.append(user_to_json(result))
        response['result'] = results
        response['status'] = 200
        return response
    except:
        response['result'] = []
        response['status'] = 500
        return response


def get_user(user, owner_id):
    """

    :param user: the user making the request
    :param owner_id: the user_id of the user we want info on
    :return: answer
    """
    status = is_allowed(user, owner_id)
    response = dict()
    if status == 200:
        owner = User.objects.get(id=owner_id)
        result = dict()
        result = user_to_json(owner)
    response["result"] = result
    response["status"] = status
    return response


def set_private(user, value):
    """

    :param user: the user who wants to be private
    :param value: the value (True/False)
    :return: status
    """
    try:
        mj_user = MJUser.objects.get(user=user)
        mj_user.private = value
        mj_user.save()
        return 204
    except:
        return 404



