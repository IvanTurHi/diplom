from flask import Flask
import folium


def run_flask(df_school):

    app = Flask(__name__)

    #Тестовая фигня, убрать потом
    def start():
        df_school_test_with_444 = df_school.loc[df_school['name'] == 'Школа №444']
        return df_school_test_with_444

    @app.route('/hello_sasha')
    def hello_sasha():
        return 'Hello, Sasha! This is our diploma. CRY!'

    #Фигня с картой
    @app.route('/')
    def basic_map():
        df_school_test_with_444 = start()
        #print(df_school_test_with_444.iloc[0])
        map = folium.Map()

        for i in range(df_school_test_with_444.shape[0]):
            location_latitude = df_school_test_with_444.iloc[i]['centroid latitude']
            location_longitude = df_school_test_with_444.iloc[i]['centroid longitude']
            folium.Marker(location=[location_latitude, location_longitude],
                          popup='<i>Школа №444</i>', tooltip='Click here').add_to(map)

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
    app.run(host='82.148.28.79', port=5001)

    #Адрес локальный отладочный, закомментить на серврее
    #app.run(host='127.0.0.1', port=5001)

if __name__ == '__main__':
    run_flask()

