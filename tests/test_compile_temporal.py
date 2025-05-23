import compileall


def test_temporal_compiles():
    assert compileall.compile_file('greeum/temporal_reasoner.py', quiet=True) 