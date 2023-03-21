import os


current_dir = os.getcwd()
current_dir_linux = current_dir.replace('\\', '/')
dir_with_settings = '/'.join(current_dir_linux.split('/')[:-1]) + '/settings/requirements.txt'
os.system('pip install -r {}'.format(dir_with_settings))
print(current_dir)
print(current_dir_linux)
print(dir_with_settings)
