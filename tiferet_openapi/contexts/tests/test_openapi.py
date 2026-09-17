'''Tiferet OpenAPI Context Tests'''

# *** imports

# ** core
from typing import Callable
from unittest import mock

# ** infra
import pytest
from tiferet import TiferetError, TiferetAPIError, use_tester
from tiferet.contexts.app import AppSessionContext
from tiferet.domain import AppSession

# ** app
from ...domain import ApiRoute, ApiRouter
from ..openapi import OpenApiSessionContext
from ..request import OpenApiRequestContext
from .models import NotAPydanticModel, SpecRequestModel, SpecResponseModel

# *** fixtures

# ** fixture: app_session
@pytest.fixture
def app_session() -> AppSession:
    '''
    AppSession bound to the OpenAPI session context under test.

    :return: An AppSession domain object.
    :rtype: AppSession
    '''

    return AppSession(id='test_api', name='Test API')

# ** fixture: get_dependency
@pytest.fixture
def get_dependency() -> Callable:
    '''
    Mock DI resolution handler.

    :return: A mock callable.
    :rtype: Callable
    '''

    return mock.Mock()

# ** fixture: response_handler
@pytest.fixture
def response_handler() -> Callable:
    '''
    Mock response-building handler.

    :return: A mock callable returning a sample response.
    :rtype: Callable
    '''

    return mock.Mock(return_value={'sum': 3})

# ** fixture: raise_error_handler
@pytest.fixture
def raise_error_handler() -> Callable:
    '''
    Mock error handler that raises TiferetAPIError.

    :return: A mock callable that raises TiferetAPIError.
    :rtype: Callable
    '''

    # Raise a TiferetAPIError for any incoming error.
    def handler(error, **kwargs):
        raise TiferetAPIError(
            error_code=getattr(error, 'error_code', 'APP_ERROR'),
            name='App Error',
            message=str(error),
        )

    return mock.Mock(side_effect=handler)

# ** fixture: get_route_handler
@pytest.fixture
def get_route_handler() -> Callable:
    '''
    Mock route-lookup handler.

    :return: A mock callable.
    :rtype: Callable
    '''

    return mock.Mock()

# ** fixture: get_status_code_handler
@pytest.fixture
def get_status_code_handler() -> Callable:
    '''
    Mock status-code-lookup handler.

    :return: A mock callable.
    :rtype: Callable
    '''

    return mock.Mock()

# ** fixture: get_routers_handler
@pytest.fixture
def get_routers_handler() -> Callable:
    '''
    Mock routers-lookup handler.

    :return: A mock callable.
    :rtype: Callable
    '''

    return mock.Mock()

# ** fixture: context
@pytest.fixture
def context(
        app_session: AppSession,
        get_dependency: Callable,
        get_route_handler: Callable,
        get_status_code_handler: Callable,
        get_routers_handler: Callable,
        raise_error_handler: Callable,
        response_handler: Callable,
    ) -> OpenApiSessionContext:
    '''
    Create an OpenApiSessionContext for testing.

    :param app_session: The bound AppSession domain object.
    :type app_session: AppSession
    :param get_dependency: The mock DI resolution handler.
    :type get_dependency: Callable
    :param get_route_handler: The mock route-lookup handler.
    :type get_route_handler: Callable
    :param get_status_code_handler: The mock status-code-lookup handler.
    :type get_status_code_handler: Callable
    :param get_routers_handler: The mock routers-lookup handler.
    :type get_routers_handler: Callable
    :param raise_error_handler: The mock error-handling handler.
    :type raise_error_handler: Callable
    :param response_handler: The mock response-building handler.
    :type response_handler: Callable
    :return: The OpenApiSessionContext instance.
    :rtype: OpenApiSessionContext
    '''

    return OpenApiSessionContext.from_domain(
        app_session,
        get_dependency=get_dependency,
        get_route_handler=get_route_handler,
        get_status_code_handler=get_status_code_handler,
        get_routers_handler=get_routers_handler,
        raise_error_handler=raise_error_handler,
        response_handler=response_handler,
    )

# *** testers

# ** tester: test_open_api_session_context
@use_tester(
    type='context',
    target_cls=OpenApiSessionContext,
    domain_cls=AppSession,
    sample_data={'id': 'test_api', 'name': 'Test API'},
    domain_type_cases=[{'declares': False}],
    for_domain_cases=[
        {
            'domain_module_path': 'tiferet.domain.app',
            'domain_class_name': 'AppSession',
            'context_module_path': 'tiferet.contexts.app',
            'context_class_name': 'AppSessionContext',
        },
    ],
)
class TestOpenApiSessionContext:
    '''
    Bound context tester for OpenApiSessionContext.
    '''

    # * test: open_api_session_context_extends_app_session_context
    def test_open_api_session_context_extends_app_session_context(self, test_ctx) -> None:
        '''
        Test that OpenApiSessionContext extends AppSessionContext.

        :param test_ctx: The bound context tester context.
        :type test_ctx: object
        '''

        assert issubclass(OpenApiSessionContext, AppSessionContext)
        test_ctx.assert_domain_type()
        test_ctx.assert_for_domain()

    # * test: open_api_session_context_stores_handlers
    def test_open_api_session_context_stores_handlers(
            self,
            context: OpenApiSessionContext,
            get_route_handler: Callable,
            get_status_code_handler: Callable,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that OpenApiSessionContext stores the OpenAPI handler callables.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_route_handler: The mock route-lookup handler.
        :type get_route_handler: Callable
        :param get_status_code_handler: The mock status-code-lookup handler.
        :type get_status_code_handler: Callable
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        assert context._get_route is get_route_handler
        assert context._get_status_code is get_status_code_handler
        assert context._get_routers is get_routers_handler

# ** tester: test_open_api_session_context_behavior
@use_tester(
    type='generic',
    target_cls=OpenApiSessionContext,
)
class TestOpenApiSessionContextBehavior:
    '''
    Bound generic tester for OpenApiSessionContext behavior.
    '''

    # * test: handle_error_tiferet_error_status_code
    def test_handle_error_tiferet_error_status_code(
            self,
            context: OpenApiSessionContext,
            get_status_code_handler: Callable,
        ) -> None:
        '''
        Test that handle_error resolves status code via get_status_code_handler for TiferetError.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_status_code_handler: The mock status-code-lookup handler.
        :type get_status_code_handler: Callable
        '''

        # Configure the mock to return 400 status code.
        get_status_code_handler.return_value = 400

        # Create a TiferetError.
        error = TiferetError('INVALID_INPUT', 'bad input')

        # Assert TiferetAPIError is raised with the correct status code.
        with pytest.raises(TiferetAPIError) as exc_info:
            context.handle_error(error)

        assert exc_info.value.status_code == 400
        get_status_code_handler.assert_called_once_with(error_code='INVALID_INPUT')

    # * test: handle_error_non_tiferet_error_500
    def test_handle_error_non_tiferet_error_500(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that handle_error returns 500 for non-Tiferet exceptions.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Create a generic exception.
        error = RuntimeError('unexpected failure')

        # Assert TiferetAPIError is raised with status code 500.
        with pytest.raises(TiferetAPIError) as exc_info:
            context.handle_error(error)

        assert exc_info.value.status_code == 500

    # * test: build_response_returns_tuple
    def test_build_response_returns_tuple(
            self,
            context: OpenApiSessionContext,
            get_route_handler: Callable,
            response_handler: Callable,
        ) -> None:
        '''
        Test that build_response returns (response, status_code) tuple.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_route_handler: The mock route-lookup handler.
        :type get_route_handler: Callable
        :param response_handler: The mock response-building handler.
        :type response_handler: Callable
        '''

        # Create a mock route with status_code.
        mock_route = mock.Mock()
        mock_route.status_code = 201
        get_route_handler.return_value = mock_route

        # Create a request.
        request = OpenApiRequestContext(feature_id='calc.add')

        # Build the response.
        response, status_code = context.build_response(request)

        # Assert the response and status code.
        assert response == response_handler.return_value
        assert status_code == 201
        response_handler.assert_called_once_with(request)
        get_route_handler.assert_called_once_with(endpoint='calc.add')

    # * test: build_response_unknown_route_defaults_200
    def test_build_response_unknown_route_defaults_200(
            self,
            context: OpenApiSessionContext,
            get_route_handler: Callable,
        ) -> None:
        '''
        Test that build_response defaults to status code 200 when the route is unknown.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_route_handler: The mock route-lookup handler.
        :type get_route_handler: Callable
        '''

        # Configure the mock to return no route.
        get_route_handler.return_value = None

        # Create a request for an unknown feature.
        request = OpenApiRequestContext(feature_id='unknown.feature')

        # Build the response.
        response, status_code = context.build_response(request)

        # Assert the unknown route defaults to 200.
        assert status_code == 200

    # * test: generate_spec_single_router
    def test_generate_spec_single_router(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec produces a valid OpenAPI 3.0 spec for a single router.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure mock routers.
        get_routers_handler.return_value = [
            ApiRouter(
                name='calc',
                prefix='/calc',
                routes=[
                    ApiRoute(id='add', endpoint='calc.add', path='/add', methods=['POST'], status_code=200),
                    ApiRoute(id='subtract', endpoint='calc.subtract', path='/subtract', methods=['POST'], status_code=200),
                ],
            ),
        ]

        # Generate the spec.
        spec = context.generate_spec(title='Calculator API', version='1.0.0', description='A calculator.')

        # Assert the spec structure.
        assert spec['openapi'] == '3.0.3'
        assert spec['info']['title'] == 'Calculator API'
        assert spec['info']['version'] == '1.0.0'
        assert spec['info']['description'] == 'A calculator.'
        assert '/calc/add' in spec['paths']
        assert '/calc/subtract' in spec['paths']
        assert spec['paths']['/calc/add']['post']['operationId'] == 'calc.add'
        assert spec['paths']['/calc/subtract']['post']['operationId'] == 'calc.subtract'
        assert '200' in spec['paths']['/calc/add']['post']['responses']

    # * test: generate_spec_includes_documentation_fields_and_schemas
    def test_generate_spec_includes_documentation_fields_and_schemas(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec includes all declared route documentation fields.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure a route with every documentation field declared.
        get_routers_handler.return_value = [
            ApiRouter(
                name='calc',
                prefix='/calc',
                routes=[
                    ApiRoute(
                        id='add',
                        endpoint='calc.add',
                        path='/add',
                        methods=['POST'],
                        status_code=201,
                        summary='Add numbers',
                        description='Adds two supplied numbers.',
                        tags=['calculation'],
                        request_model=f'{SpecRequestModel.__module__}.SpecRequestModel',
                        response_model=f'{SpecResponseModel.__module__}.SpecResponseModel',
                    ),
                ],
            ),
        ]

        # Generate the specification.
        spec = context.generate_spec()

        # Assert the complete documented operation shape.
        assert spec['paths']['/calc/add']['post'] == {
            'operationId': 'calc.add',
            'responses': {
                '201': {
                    'description': 'Successful response',
                    'content': {
                        'application/json': {
                            'schema': SpecResponseModel.model_json_schema(),
                        },
                    },
                },
            },
            'summary': 'Add numbers',
            'description': 'Adds two supplied numbers.',
            'tags': ['calculation'],
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': SpecRequestModel.model_json_schema(),
                    },
                },
            },
        }

    # * test: generate_spec_preserves_bare_operation_without_documentation_fields
    def test_generate_spec_preserves_bare_operation_without_documentation_fields(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec preserves the bare operation shape when undeclared.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure a route with no documentation fields declared.
        get_routers_handler.return_value = [
            ApiRouter(
                name='health',
                prefix='/health',
                routes=[
                    ApiRoute(
                        id='ping',
                        endpoint='health.ping',
                        path='/ping',
                        methods=['GET'],
                        status_code=200,
                    ),
                ],
            ),
        ]

        # Generate the specification.
        spec = context.generate_spec()

        # Assert the current bare operation shape is preserved.
        assert spec['paths']['/health/ping']['get'] == {
            'operationId': 'health.ping',
            'responses': {
                '200': {
                    'description': 'Successful response',
                },
            },
        }

    # * test: generate_spec_propagates_unresolvable_model_error
    def test_generate_spec_propagates_unresolvable_model_error(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec raises when a route's model path cannot resolve.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure a route with nonexistent request and response model paths.
        get_routers_handler.return_value = [
            ApiRouter(
                name='health',
                prefix='/health',
                routes=[
                    ApiRoute(
                        id='ping',
                        endpoint='health.ping',
                        path='/ping',
                        methods=['GET'],
                        status_code=200,
                        request_model='missing.models.Request',
                        response_model='missing.models.Response',
                    ),
                ],
            ),
        ]

        # Assert the first unresolvable path aborts spec generation.
        with pytest.raises(TiferetError) as exc_info:
            context.generate_spec()

        assert exc_info.value.error_code == 'OPENAPI_MODEL_RESOLUTION_FAILED'
        assert exc_info.value.kwargs['model_path'] == 'missing.models.Request'

    # * test: resolve_model_schema_valid_model_returns_schema
    def test_resolve_model_schema_valid_model_returns_schema(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that a resolvable Pydantic model path returns its JSON schema.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Resolve the test request model by its dotted path.
        schema = context._resolve_model_schema(
            f'{SpecRequestModel.__module__}.SpecRequestModel',
        )

        # Assert the resolved schema matches the model's JSON schema.
        assert schema == SpecRequestModel.model_json_schema()

    # * test: resolve_model_schema_malformed_path_raises
    def test_resolve_model_schema_malformed_path_raises(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that a path without a module separator raises TiferetError.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Assert a malformed path raises the structured resolution error.
        with pytest.raises(TiferetError) as exc_info:
            context._resolve_model_schema('NoDotModel')

        assert exc_info.value.error_code == 'OPENAPI_MODEL_RESOLUTION_FAILED'
        assert exc_info.value.kwargs['model_path'] == 'NoDotModel'

    # * test: resolve_model_schema_missing_module_raises
    def test_resolve_model_schema_missing_module_raises(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that a missing module path raises TiferetError.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Assert a missing module raises the structured resolution error.
        with pytest.raises(TiferetError) as exc_info:
            context._resolve_model_schema('nonexistent.module.path.Model')

        assert exc_info.value.error_code == 'OPENAPI_MODEL_RESOLUTION_FAILED'
        assert exc_info.value.kwargs['model_path'] == 'nonexistent.module.path.Model'

    # * test: resolve_model_schema_missing_class_raises
    def test_resolve_model_schema_missing_class_raises(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that a missing class on an existing module raises TiferetError.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Assert a missing class raises the structured resolution error.
        with pytest.raises(TiferetError) as exc_info:
            context._resolve_model_schema(f'{__name__}.NonexistentModel')

        assert exc_info.value.error_code == 'OPENAPI_MODEL_RESOLUTION_FAILED'
        assert exc_info.value.kwargs['model_path'] == f'{__name__}.NonexistentModel'

    # * test: resolve_model_schema_non_pydantic_class_raises
    def test_resolve_model_schema_non_pydantic_class_raises(
            self,
            context: OpenApiSessionContext,
        ) -> None:
        '''
        Test that a non-Pydantic class path raises TiferetError.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        '''

        # Assert a class without model_json_schema raises the structured error.
        with pytest.raises(TiferetError) as exc_info:
            context._resolve_model_schema(
                f'{NotAPydanticModel.__module__}.NotAPydanticModel',
            )

        assert exc_info.value.error_code == 'OPENAPI_MODEL_RESOLUTION_FAILED'
        assert exc_info.value.kwargs['model_path'] == (
            f'{NotAPydanticModel.__module__}.NotAPydanticModel'
        )

    # * test: generate_spec_multi_router
    def test_generate_spec_multi_router(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec handles multiple routers.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure mock routers.
        get_routers_handler.return_value = [
            ApiRouter(
                name='calc',
                prefix='/calc',
                routes=[
                    ApiRoute(id='add', endpoint='calc.add', path='/add', methods=['POST'], status_code=200),
                ],
            ),
            ApiRouter(
                name='health',
                prefix='',
                routes=[
                    ApiRoute(id='ping', endpoint='health.ping', path='/ping', methods=['GET'], status_code=200),
                ],
            ),
        ]

        # Generate the spec.
        spec = context.generate_spec()

        # Assert paths from both routers.
        assert '/calc/add' in spec['paths']
        assert '/ping' in spec['paths']
        assert spec['paths']['/ping']['get']['operationId'] == 'health.ping'

    # * test: generate_spec_defaults
    def test_generate_spec_defaults(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec uses default parameter values.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure mock with empty routers.
        get_routers_handler.return_value = []

        # Generate the spec with defaults.
        spec = context.generate_spec()

        # Assert default values.
        assert spec['info']['title'] == 'API'
        assert spec['info']['version'] == '1.0.0'
        assert spec['info']['description'] == ''
        assert spec['paths'] == {}

    # * test: generate_spec_multiple_methods
    def test_generate_spec_multiple_methods(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that generate_spec maps each HTTP method to a separate operation entry.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure mock with a route that has multiple methods.
        get_routers_handler.return_value = [
            ApiRouter(
                name='items',
                prefix='/api',
                routes=[
                    ApiRoute(id='item', endpoint='items.item', path='/item', methods=['GET', 'POST'], status_code=200),
                ],
            ),
        ]

        # Generate the spec.
        spec = context.generate_spec()

        # Assert both methods are present.
        assert 'get' in spec['paths']['/api/item']
        assert 'post' in spec['paths']['/api/item']
        assert spec['paths']['/api/item']['get']['operationId'] == 'items.item'
        assert spec['paths']['/api/item']['post']['operationId'] == 'items.item'

    # * test: get_docs_spec_returns_openapi_spec
    def test_get_docs_spec_returns_openapi_spec(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that get_docs_spec returns a well-formed OpenAPI specification.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure a router with one route.
        get_routers_handler.return_value = [
            ApiRouter(
                name='calc',
                prefix='/calc',
                routes=[
                    ApiRoute(
                        id='add',
                        endpoint='calc.add',
                        path='/add',
                        methods=['POST'],
                        status_code=200,
                    ),
                ],
            ),
        ]

        # Retrieve the generated specification through the public accessor.
        spec = context.get_docs_spec()

        # Assert the returned document is a non-empty OpenAPI 3.0 specification.
        assert spec
        assert spec['openapi'].startswith('3.0.')
        assert spec['info'] == {
            'title': 'API',
            'version': '1.0.0',
            'description': '',
        }
        assert spec['paths']['/calc/add']['post']['operationId'] == 'calc.add'

    # * test: create_docs_handler_delegates_with_deprecation_warning
    def test_create_docs_handler_delegates_with_deprecation_warning(
            self,
            context: OpenApiSessionContext,
            get_routers_handler: Callable,
        ) -> None:
        '''
        Test that create_docs_handler delegates to get_docs_spec with a warning.

        :param context: The OpenApiSessionContext instance.
        :type context: OpenApiSessionContext
        :param get_routers_handler: The mock routers-lookup handler.
        :type get_routers_handler: Callable
        '''

        # Configure a router with one route.
        get_routers_handler.return_value = [
            ApiRouter(
                name='health',
                prefix='',
                routes=[
                    ApiRoute(
                        id='ping',
                        endpoint='health.ping',
                        path='/ping',
                        methods=['GET'],
                        status_code=200,
                    ),
                ],
            ),
        ]

        # Retrieve the expected specification from the replacement method.
        expected_spec = context.get_docs_spec(
            title='Health API',
            version='2.0.0',
            description='Health check endpoints.',
        )

        # Invoke the deprecated alias with matching arguments.
        with pytest.warns(DeprecationWarning, match='create_docs_handler is deprecated'):
            spec = context.create_docs_handler(
                title='Health API',
                version='2.0.0',
                description='Health check endpoints.',
            )

        # Assert the alias returns exactly the replacement method's result.
        assert spec == expected_spec
