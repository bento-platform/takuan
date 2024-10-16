from fastapi import Depends, FastAPI, Request, Response, status

from typing import Awaitable, Callable


class BaseAuthzMiddleware:

    def attach(self, app: FastAPI):
        """
        Attaches itself to the TDS FastAPI app, all requests will go through the dispatch function.
        """
        raise NotImplemented()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Defines the way requests are handled by the authorization middleware, if it is attached to the FastAPI app.
        This is to allow adopters to implement custom authorization logic.
        When implementing this function, you can do the following on all incoming requests, before they get to their respective routers:
        -   Modify the request (e.g. add a header, modify the state before authz check)
        -   Pass the request to the rest of the application with call_next
            - The request will first hit an endpoint dependency function (e.g. dep_authorize_ingest)
            - The endpoint dep function evaluates if the request should be authorized and raises an exception if not
            - If authorized, the request proceeds to the endpoint function
            - If unauthorized, an exception should be caught and handled here, the request never reaches the endpoint function
        -   Modify the request before it is returned to the client
        -   Raise and catch exception based on authorization results
        -   Handle unauthorized responses
        """
        raise NotImplemented()

    def dep_authorize_ingest(self):
        """
        Authorization function for the /ingest endpoint.

        Returns an inner function as a dependency, which is
        """
        raise NotImplemented()

    def dep_authorize_normalize(self):
        """
        Endpoint:   /normalize

        Authorizes the normalize endpoint
        """
        raise NotImplemented()
