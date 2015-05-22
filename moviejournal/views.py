from django.shortcuts import render

from django.http import HttpResponse

from moviejournal.dbqueries import *
from moviejournal.models import *
from moviejournal.helper import create_answer

import json

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login


# Create your views here.

def register(request):
    """
    Create new user
    Need params for username, password, email, is_private
    Perform checks
    respond with user created Automatic Login? Redirect? need Confirmation mail?
    """
    """
    username = request.POST.get('u', '')
    password = request.POST.get('p', '')
    email = request.POST.get('e', '')
    is_private = request.POST.get('i_p', False)
    """
    data = json.loads(request.body)
    username = data['u']
    password = data['p']
    email = data['e']
    is_private = False
    response = {}
    # DO CHECKS PASSWORD STRENGTH (ALSO CLIENT SIDE)
    # EMAIL CORRECT UNIQUE
    try:
        user = User.objects.create_user(username, email, password)
        mj_user = MJUser(user=user)
        if is_private:
            mj_user.private = True
        user.save()
        mj_user.save()
        status = 201
    except Exception as e:
        response["error"] = str(e.__cause__)
        status = 400
    return HttpResponse(create_answer(request, response), content_type="application/json", status=status)
    

def login(request):
    """
    Check username and password against db
    NEEDS TOKEN??
    respond with necessary data for following requests
    
    ALLOWED METHODS: POST
    """
    data = json.loads(request.body)
    username = data['u']
    password = data['p']
    user = authenticate(username=username, password=password)
    response = {}
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            response['login'] = 'success'
        else:
            response['login'] = 'inactive'
    else:
        response['login'] = 'failed'
        response['user'] = user
    
    return HttpResponse(create_answer(request, response), content_type="application/json")
    
    
def timeline(request):
    """
    1. Get the list of users the user follows
    2. Get the movies in the journal of these
       users sorted by entry date (descending)
       Grouped By Movie (e.g. one entry per movie)
    3. Get the Movies from themoviedb, RT and OMDB, MJ
    
    ALLOWED METHODS: GET
    """
    
    if request.user.is_authenticated():
        user = request.user
        if request.method != "GET":
            return HttpResponse(create_answer(request, {"Error": "Method Not Allowed"}), status=405)
        else:
            pass
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}),status=401)
    return HttpResponse(create_answer(request, response), content_type="application/json")


def journal(request, user_id):
    """
    1. Check if allowed (e.g. user not private or accepted follow request by USER)
    2. if allowed fetch journal list
    3. Get the Movies from themoviedb, RT, OMDB, MJ
    
    ALLOWED METHODS: GET
    """
    if request.user.is_authenticated():
        print >>sys.stderr, "journal"
        user = request.user
        if request.method == "GET":
            offset = request.GET.get("offset", 0)
            size = request.GET.get("size", 10)
            response = get_journal(user, user_id, offset, size)
            return HttpResponse(create_answer(request, response['result']), status=response['status'])
        else: 
            return HttpResponse(create_answer(request, {"Error": "Method Not Allowed"}), status=405)
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)


def screening(request, screening_id=None):
    """
    1. Check if allowed (e.g. Logged In)
    
    Allowed Methods: GET, POST, PUT, DELETE
    """
    if request.user.is_authenticated():
        user = request.user
        if request.method == "GET":
            answer = get_screening(user, screening_id)
            return HttpResponse(create_answer(request, answer), status=answer['status'])
        elif request.method == "POST":
            try:
                data = json.loads(request.body)
                status = post_screening(user, data["movie_id"])
                return HttpResponse(status=status)
            except:
                return HttpResponse(status=400)
        elif request.method == "DELETE":

            print >>sys.stderr, "delete"
            status = delete_screening(user, screening_id)
            return HttpResponse(status=status)
        else:
            # Method Not Allowed
            return HttpResponse(status=403)
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)


def watchlist(request, user_id):
    """
    1. Check if allowed (e.g. user not private or accepted follow request by USER)
    2. if allowed fetch watchlist
    3. Get Movies from themoviedb, RT, OMDB, MJ
    
    ALLOWED METHODS: GET, POST
    """
    if request.user.is_authenticated():
        user = request.user
        if request.method == "GET":
            # sanity does user exist
            user_watchlist = User.objects.get(id=user_id)
            offset = request.GET.get("offset",0)
            size = request.GET.get("size",10)
            response = get_watchlist(user_watchlist,offset,size)
            return HttpResponse(create_answer(request, response), content_type="application/json")
        elif request.method == "POST":
            movie_id = request.POST["movie_id"]
            user_watchlist = User.objects.get(id=user_id)
            if user == user_watchlist:
                success = post_screening(user_watchlist, movie_id)
                if success:
                    return HttpResponse(status=201)
                else:
                    return HttpResponse(status=400)
            else:
                return HttpResponse(create_answer(request, {"Error": "Cannot post to this Journal"}), status=403)
            
        else: 
            return HttpResponse(create_answer(request, {"Error": "Method Not Allowed"}), status=405)
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)


def watchlist_entry(request, watchlist_entry_id=None):
    """

    :param request:
    :param watchlist_entry_id:
    :return:
    """
    if request.user.is_authenticated():
        user = request.user
        if request.method == "GET":
            answer = get_watchlist_entry(user, watchlist_entry_id)
            return HttpResponse(create_answer(request, answer), content_type="application/json", status=answer['status'])
        elif request.method == "POST":
            status = post_watchlist_entry(user, request.POST["movie_id"])
            return HttpResponse(status=status)
        elif request.method == "DELETE":
            status = delete_watchlist_entry(user, watchlist_entry_id)
            return HttpResponse(status=status)
        else:
            # Method Not Allowed
            return HttpResponse(status=403)
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)


def movie(request, movie_id):
    """
    1. Get Movies from themoviedb, RT, OMDB, MJ
    
    ALLOWED METHODS: GET
    """
    if request.user.is_authenticated():
        user = request.user
        if request.method != "GET":
            return HttpResponse(create_answer(request, {"Error": "Method Not Allowed"}), status=405)
        else:
            response = get_movie(movie_id, user)
            if response['status'] == 404:
                return HttpResponse(create_answer(request, {"Error": "No Movie Found"}), status=404)
            
            return HttpResponse(create_answer(request, response['result']))
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)


def user(request, user_id=None):
    """
    get a user if no user_id is specified return the logged in user

    :param request:
    :param user_id:
    :return:
    """
    if request.user.is_authenticated():
        user = request.user
        query = request.GET.get("query", False)
        if user_id is None:
            user_id = user.id
        if request.method != "GET":
            data = create_answer(request, {"Error": "Method Not Allowed"})
            return HttpResponse(data, status=405)
        else:
            if query:
                response = search_user(user, query)
            else:
                response = get_user(user, user_id)
            if response['status'] == 404:
                data = create_answer(request, {"Error": "No User Found"})
                return HttpResponse(data, status=404)
            return HttpResponse(create_answer(request, response["result"]))
    else:
        data = create_answer(request, {"Error": "Not Logged in"})
        return HttpResponse(data, status=401)


def person(request, person_id):
    """
    2. Get Person from themoviedb
    
    ALLOWED METHODS: GET
    """


def follow(request, user_id):
    """
    GET:
        Check if allowed
        Get list of users, user_id is following
    POST:
        USER starts following user_id
        (if user_id = private) sends REQUEST
    DELETE:
        USER stops following user_id
        (if user_id = private) cancel REQUEST
    """
    if request.user.is_authenticated():
        user = request.user
        if request.method == "GET":
            pass
            #answer = get_screening(user, screening_id)
            #return HttpResponse(create_answer(request, answer), status=answer['status'])
        elif request.method == "POST":
            try:
                data = json.loads(request.body)
                status = post_follow(user, data["user_id"])
                return HttpResponse(status=status)
            except:
                return HttpResponse(status=400)
        elif request.method == "DELETE":
            status = delete_follow(user, user_id)
            return HttpResponse(status=status)
        else:
            # Method Not Allowed
            return HttpResponse(status=403)
    else:
        return HttpResponse(create_answer(request, {"Error": "Not Logged in"}), status=401)