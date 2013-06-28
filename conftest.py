
#===================================================================================================
# pytest_addoption
#===================================================================================================
def pytest_addoption(parser):
    '''
    Adds a new "--jenkins-available" option to pytest's command line. If not given, tests that
    require a live Jenkins instance will be skipped.
    '''
    parser.addoption(
        "--jenkins-available", 
        action="store_true", 
        default=False,
        help="if tests with real a jenkins server should be executed",
    )