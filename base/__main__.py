import sys
import os

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)

from base.base_application import BaSeApplication

if __name__ == '__main__':
	APP = BaSeApplication()
	APP.start()
