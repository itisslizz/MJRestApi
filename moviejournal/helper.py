import json
from django.core import serializers


def obj_to_json(obj):
    """
    Turns a Django Object to a normal dict
    :param obj: the object to be converted
    :return: the new dict obj
    """
    json_obj = serializers.serialize('json', [obj, ])
    new_obj = json.loads(json_obj)[0]
    return new_obj


def list_to_json(dj_list):
    """
    turns a list of Django Object to a dict
    :param dj_list: the list to be converted
    :return: the new list
    """
    json_list = serializers.serialize('json', dj_list)
    new_list = json.loads(json_list)
    return new_list


def user_to_json(obj):

    json_obj = serializers.serialize('json', [obj, ], fields=('username',
                'email', 'first_name', 'last_name', 'last_login', 'date_joined'))
    new_obj = json.loads(json_obj)[0]
    return new_obj


def create_answer(request, data):
    data = json.dumps(data)
    if 'callback' in request.REQUEST:
        data = '%s(%s);' % (request.REQUEST['callback'], data)
    return data
