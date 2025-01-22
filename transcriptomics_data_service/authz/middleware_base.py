from fastapi import Depends, FastAPI, Request, Response

from typing import Awaitable, Callable, Sequence


class BaseAuthzMiddleware:
    # Middleware lifecycle functions

    def attach(self, app: FastAPI):
        """
        Attaches itself to the TDS FastAPI app, all requests will go through the dispatch function.
        """
        app.middleware("http")(self.dispatch)

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
        raise NotImplementedError()

    def mark_authz_done(self, request: Request):
        """
        Implement and use in authz check function to mark that the given request has been checked.
        Used by the Bento specific authz middleware to return 403 by default.
        Ignore if you plan on simply raising exceptions in the authz check methods (recommended).
        """
        pass

    # Dependency injections

    def dep_public_endpoint(self) -> Depends:
        """
        Dependency for public endpoints.
        Used to set the /service-info endpoint's dependencies.
        Does nothing by default, override according to your needs.
        """

        def _inner():
            pass

        return Depends(_inner)

    def dep_app(self) -> None | Sequence[Depends]:
        """
        Specify dependencies to be added on ALL paths of the API.
        """
        return None

    def dep_ingest_router(self) -> None | Sequence[Depends]:
        """
        Specify dependencies to be added to the ingest router.
        This dependency will apply on all the router's paths.
        """
        return None

    def dep_expression_router(self) -> None | Sequence[Depends]:
        """
        Specify dependencies to be added to the expression_router.
        This dependency will apply on all the router's paths.
        """
        return None

    def dep_experiment_result_router(self) -> None | Sequence[Depends]:
        """
        Specify dependencies to be added to the experiment_router.
        This dependency will apply on all the router's paths.
        """
        return None

    ###### Endpoint specific dependency creators for authorization logic

    ###### INGEST router paths

    def dep_authz_ingest(self) -> None | Sequence[Depends]:
        return None

    def dep_authz_normalize(self) -> None | Sequence[Depends]:
        return None

    ###### EXPRESSIONS router paths

    def dep_authz_expressions_list(self) -> None | Sequence[Depends]:
        return None

    ###### EXPERIMENT RESULTS router paths
    def dep_authz_delete_experiment_result(self) -> None | Sequence[Depends]:
        return None

    def dep_authz_get_experiment_result(self) -> None | Sequence[Depends]:
        return None
    
    def dep_authz_list_experiment_results(self) -> None | Sequence[Depends]:
        return None
