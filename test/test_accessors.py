import wxee.accessors


def test_accessor_adds_attribute() -> None:
    """Test that the accessor correctly adds accessed attributes"""

    class TestClass:
        pass

    @wxee.accessors.wx_accessor(TestClass)
    class TestAccessor:
        def __init__(self, *args):
            pass

        def accessed_method(self):
            pass

    assert hasattr(TestClass().wx, "accessed_method")
