from flask import Flask
import folium


def run_flask(osm):

    app = Flask(__name__)

    #Тестовая фигня, убрать потом
    def start():
        df_school = osm.read_data(osm.school_data_name_transform)
        df_school_test_with_444 = df_school.loc[df_school['district_name'] == 'район Измайлово']
        df_borders = osm.read_data(osm.borders_data_name_transform)
        df_borders_izm = df_borders.loc[df_borders['district_name'] == 'район Измайлово']
        return df_school_test_with_444, df_borders_izm

    @app.route('/hello_sasha')
    def hello_sasha():
        return 'Hello, Sasha! This is our diploma. CRY!'

    #Фигня с картой
    @app.route('/')
    def basic_map():
        df_school_test_with_444, df_borders_izm = start()
        print(df_borders_izm)
        map = folium.Map()

        #Вывод границ района, координаты указаны не в том порядке,
        #поэтому координаты каждой точки необходимо поменять местами, иначе оказываемся где-то в Иране
        geom = list(df_borders_izm['geometry'])[0]
        points = list(geom.exterior.coords)
        for i in range(len(points)):
            points[i] = points[i][::-1]
        print(points)

        #Добавление маркеров школы на карту
        for i in range(df_school_test_with_444.shape[0]):
            location_latitude = df_school_test_with_444.iloc[i]['centroid latitude']
            location_longitude = df_school_test_with_444.iloc[i]['centroid longitude']
            folium.Marker(location=[location_latitude, location_longitude],
                          popup='<i>Школа №444</i>', tooltip='Click here').add_to(map)

        #Добавление границ района на карту
        folium.PolyLine(locations=points, color='red').add_to(map)

        #location_latitude = df_school_test_with_444.iloc[0]['centroid latitude']
        #location_longitude = df_school_test_with_444.iloc[0]['centroid longitude']
        #folium.Marker(location=[location_latitude, location_longitude],
        #              popup='<i>Marker</i>', tooltip='Click here').add_to(map)
#
        #location_latitude = df_school_test_with_444.iloc[1]['centroid latitude']
        #location_longitude = df_school_test_with_444.iloc[1]['centroid longitude']
        #folium.Marker(location=[location_latitude, location_longitude],
        #              popup='<i>Marker</i>', tooltip='Click here').add_to(map)

        return map._repr_html_()


    #Адрес сервера, раскомментить на сервере
    #app.run(host='82.148.28.79', port=5001)

    #Адрес локальный отладочный, закомментить на серврее
    app.run(host='127.0.0.1', port=5001)

if __name__ == '__main__':
    run_flask()

