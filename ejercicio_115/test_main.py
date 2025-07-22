def truncate_to_two_decimals(num):
    return int(num * 100) / 100

def round_to_two_decimals(num):
    return round(num, 2)

def test_truncate_to_two_decimals():
    assert truncate_to_two_decimals(3.14159) == 3.14
    assert truncate_to_two_decimals(2.71828) == 2.71
    assert truncate_to_two_decimals(1.005) == 1.00

def test_round_to_two_decimals():
    assert round_to_two_decimals(3.14159) == 3.14
    assert round_to_two_decimals(2.71828) == 2.72
    assert round_to_two_decimals(1.005) == 1.01

test_truncate_to_two_decimals()
test_round_to_two_decimals()