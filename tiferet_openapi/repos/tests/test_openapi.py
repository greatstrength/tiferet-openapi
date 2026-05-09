'''Tiferet OpenAPI YAML Repository Tests'''

# *** imports

# ** core
from pathlib import Path

# ** infra
import pytest

# ** app
from ..openapi import OpenApiYamlRepository


# *** constants

# ** constant: openapi_yaml_content
OPENAPI_YAML_CONTENT = """\
openapi:
  routers:
    calc:
      prefix: /calc
      routes:
        add:
          path: /add
          methods:
            - POST
          status_code: 200
        subtract:
          path: /subtract
          methods:
            - POST
          status_code: 200
    health:
      routes:
        ping:
          path: /ping
          methods:
            - GET
          status_code: 200
  errors:
    INVALID_INPUT: 400
    DIVISION_BY_ZERO: 422
    NOT_FOUND: 404
"""

# ** constant: fast_yaml_content
FAST_YAML_CONTENT = """\
fast:
  routers:
    api:
      prefix: /api
      routes:
        list_items:
          path: /items
          methods:
            - GET
          status_code: 200
  errors:
    UNAUTHORIZED: 401
"""


# *** fixtures

# ** fixture: openapi_yaml_file
@pytest.fixture
def openapi_yaml_file(tmp_path: Path) -> Path:
    '''
    Create a temporary openapi.yml file for testing.

    :param tmp_path: The temporary directory path.
    :type tmp_path: Path
    :return: Path to the temporary YAML file.
    :rtype: Path
    '''

    # Write the YAML content to a temporary file.
    file_path = tmp_path / 'openapi.yml'
    file_path.write_text(OPENAPI_YAML_CONTENT, encoding='utf-8')
    return file_path


# ** fixture: fast_yaml_file
@pytest.fixture
def fast_yaml_file(tmp_path: Path) -> Path:
    '''
    Create a temporary fast.yml file for testing.

    :param tmp_path: The temporary directory path.
    :type tmp_path: Path
    :return: Path to the temporary YAML file.
    :rtype: Path
    '''

    # Write the YAML content to a temporary file.
    file_path = tmp_path / 'fast.yml'
    file_path.write_text(FAST_YAML_CONTENT, encoding='utf-8')
    return file_path


# ** fixture: repo
@pytest.fixture
def repo(openapi_yaml_file: Path) -> OpenApiYamlRepository:
    '''
    Create an OpenApiYamlRepository with default root_key.

    :param openapi_yaml_file: Path to the temporary YAML file.
    :type openapi_yaml_file: Path
    :return: The repository instance.
    :rtype: OpenApiYamlRepository
    '''

    # Return a repository instance with the default root key.
    return OpenApiYamlRepository(
        openapi_yaml_file=str(openapi_yaml_file),
    )


# ** fixture: fast_repo
@pytest.fixture
def fast_repo(fast_yaml_file: Path) -> OpenApiYamlRepository:
    '''
    Create an OpenApiYamlRepository with root_key='fast'.

    :param fast_yaml_file: Path to the temporary YAML file.
    :type fast_yaml_file: Path
    :return: The repository instance.
    :rtype: OpenApiYamlRepository
    '''

    # Return a repository instance with the 'fast' root key.
    return OpenApiYamlRepository(
        openapi_yaml_file=str(fast_yaml_file),
        root_key='fast',
    )


# *** tests

# ** test: get_routers_default_root_key
def test_get_routers_default_root_key(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_routers loads and maps routers with the default 'openapi' root key.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Retrieve all routers.
    routers = repo.get_routers()

    # Assert two routers were loaded.
    assert len(routers) == 2

    # Assert router names.
    router_names = [r.name for r in routers]
    assert 'calc' in router_names
    assert 'health' in router_names

    # Assert calc router details.
    calc_router = next(r for r in routers if r.name == 'calc')
    assert calc_router.prefix == '/calc'
    assert len(calc_router.routes) == 2

    # Assert route details.
    add_route = next(r for r in calc_router.routes if r.id == 'add')
    assert add_route.endpoint == 'calc.add'
    assert add_route.path == '/add'
    assert add_route.methods == ['POST']
    assert add_route.status_code == 200


# ** test: get_routers_alternate_root_key
def test_get_routers_alternate_root_key(fast_repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_routers works with root_key='fast'.

    :param fast_repo: The repository instance with fast root key.
    :type fast_repo: OpenApiYamlRepository
    '''

    # Retrieve all routers.
    routers = fast_repo.get_routers()

    # Assert one router was loaded.
    assert len(routers) == 1
    assert routers[0].name == 'api'
    assert routers[0].prefix == '/api'

    # Assert route details.
    assert len(routers[0].routes) == 1
    assert routers[0].routes[0].id == 'list_items'
    assert routers[0].routes[0].endpoint == 'api.list_items'


# ** test: get_route_found
def test_get_route_found(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_route returns the correct route when found.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Retrieve a specific route.
    route = repo.get_route('add')

    # Assert the route was found.
    assert route is not None
    assert route.id == 'add'
    assert route.endpoint == 'calc.add'
    assert route.path == '/add'


# ** test: get_route_not_found
def test_get_route_not_found(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_route returns None when the route is not found.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Retrieve a non-existent route.
    route = repo.get_route('nonexistent')

    # Assert None was returned.
    assert route is None


# ** test: get_route_filtered_by_router_name
def test_get_route_filtered_by_router_name(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_route filters by router_name when provided.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Retrieve a route scoped to the 'calc' router.
    route = repo.get_route('add', router_name='calc')
    assert route is not None
    assert route.endpoint == 'calc.add'

    # Attempt to retrieve 'add' from the 'health' router (should not exist).
    route = repo.get_route('add', router_name='health')
    assert route is None


# ** test: get_route_filtered_by_wrong_router_name
def test_get_route_filtered_by_wrong_router_name(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_route returns None when router_name does not match.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Retrieve 'ping' from the 'calc' router (should not exist there).
    route = repo.get_route('ping', router_name='calc')
    assert route is None

    # Retrieve 'ping' from the correct 'health' router.
    route = repo.get_route('ping', router_name='health')
    assert route is not None
    assert route.endpoint == 'health.ping'


# ** test: get_status_code_mapped
def test_get_status_code_mapped(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_status_code returns the mapped status code.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Assert mapped error codes return the correct status.
    assert repo.get_status_code('INVALID_INPUT') == 400
    assert repo.get_status_code('DIVISION_BY_ZERO') == 422
    assert repo.get_status_code('NOT_FOUND') == 404


# ** test: get_status_code_default
def test_get_status_code_default(repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_status_code returns 500 for unknown error codes.

    :param repo: The repository instance.
    :type repo: OpenApiYamlRepository
    '''

    # Assert unknown error codes default to 500.
    assert repo.get_status_code('UNKNOWN_ERROR') == 500


# ** test: get_status_code_alternate_root_key
def test_get_status_code_alternate_root_key(fast_repo: OpenApiYamlRepository) -> None:
    '''
    Test that get_status_code works with an alternate root key.

    :param fast_repo: The repository instance with fast root key.
    :type fast_repo: OpenApiYamlRepository
    '''

    # Assert mapped error code from the fast config.
    assert fast_repo.get_status_code('UNAUTHORIZED') == 401

    # Assert unknown error codes still default to 500.
    assert fast_repo.get_status_code('UNKNOWN') == 500
