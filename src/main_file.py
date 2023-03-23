#this is the main file
#from smth import do_all

from flask_file import run_flask
from OSM_module import osm_parser


if __name__ == '__main__':
    osm = osm_parser()
    osm.get_path()
    df_school = osm.read_data(osm.school_data_name_transform)
    run_flask(df_school)
