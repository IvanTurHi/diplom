import folium
from OSM_module import osm_parser

class Map_master():

    #Загружаем датасет границ и выбираем нужные нам по id
    def get_districts(self, districts_list):
        self.osm.get_path()
        df_borders = self.osm.read_data(self.osm.borders_data_name_transform)
        df_target_borders = df_borders.loc[df_borders['district_id'].isin(districts_list)]

        return df_target_borders

    #Функция меняет долготу и широту местами
    def swap_points(self, points):
        for j in range(len(points)):
            points[j] = points[j][::-1]

        return points

    #функция для формирования линий границ районов
    def get_borders_in_right_oreder(self, df_target_borders):
        borders_map = {}
        #Если район целый и его тип Полигон, то все супер, просто меняем последовательность долготы и широты
        #На выходе словарь, где каждому району id соответствует список, содержаший список точек
        #Для полигонов там один список, для мультиполигонов несколько, это сделано чтоб все отображлось корректно
        #И не было линий от конца одной части района к началу другой
        for i in range(df_target_borders.shape[0]):
            if str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.polygon.Polygon':
                points = list(df_target_borders.iloc[i]['geometry'].exterior.coords)
                borders_map[df_target_borders.iloc[i]['district_id']] = [self.swap_points(points)]
            #Если же район раздлене пространственно и его тип Мультиполигон, то мы добавляем его части по отдельности
            elif str(type(df_target_borders.iloc[i]['geometry'])).split("'")[1] == 'shapely.geometry.multipolygon.MultiPolygon':
                mycoordslist = [list(x.exterior.coords) for x in df_target_borders.iloc[i]['geometry'].geoms]
                for j in mycoordslist:
                    points = j
                    points = self.swap_points(points)
                    if df_target_borders.iloc[i]['district_id'] not in borders_map:
                        borders_map[df_target_borders.iloc[i]['district_id']] = [points]
                    else:
                        borders_map[df_target_borders.iloc[i]['district_id']] += [points]

            #geom = list(df_target_borders['geometry'])[0]
            #points = list(geom.exterior.coords)
            #for j in range(len(points)):
            #    points[j] = points[j][::-1]
            #borders_map[df_target_borders.loc[i]['district_id']] = points

        return borders_map

    #Функция по выводу границ районов. На вход получает список id районов
    def print_district_borders(self, map, districts_list):
        df_target_borders = self.get_districts(districts_list)
        borders_map = self.get_borders_in_right_oreder(df_target_borders)

        color = 'red'
        #fill_color отвечает за заливку внутри полигона
        #fill_opacity отвечает за прозрачность заливки
        for i in borders_map:
            for j in borders_map[i]:
                folium.PolyLine(locations=j, color=color, fill_color="blue", fill_opacity=0.3).add_to(map)

        return map




    osm = osm_parser()