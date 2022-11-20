import os
import sys
import re
from checker import Checker


def main():
    path = sys.argv[1]
    if path.endswith(".py"):
        Checker.test(path)
    else:
        tests_list = os.listdir(path)
        for file in tests_list:
            if re.match("test_[0-9]*.py", file):
                Checker.test(os.path.join(path, file))


if __name__ == "__main__":
    main()
