import pytest


@pytest.fixture(scope="session", autouse=True)
def db_conn():
    # Will be executed before the first test
    yield
    # Will be executed after the last test
    with open("testlog.json", "r") as f:
        for line in f:
            print(line)
    print("Read all lines from testlog!")
