"""Module for hiring a service in order to get or manipulate resources.
"""
from service import registry as service
from helpers import utils


def route_get_person(person_id: str):
    """
    Calls the service for looking up a person's data and
    returns a response with the information found.

    :returns: flask.Response - A flask.Response object to be
        sent to the client.
    """
    response = service.get_person(person_id)
    return utils.build_response(response)
