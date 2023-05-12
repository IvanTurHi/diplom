from OSM_module import osm_parser
import geopandas as gpd

class Stat_master():

    def get_districts(self, districts_list, districts_df):
        district_names = list(districts_df.loc[districts_df['district_id'].isin(districts_list)]['district_name'])
        self.districts_df = districts_df
        return district_names

    def get_regions(self, region_list, regions_df):
        regions_names = list(regions_df.loc[regions_df['region_id'].isin(region_list)]['region_name'])
        self.regions_df = regions_df
        return regions_names

    def get_data(self, name, type_o, target):
        if target == 'density':
            round_value = 4
        else:
            round_value = 0
        if type_o == 'district':
            data = round(float(list(self.districts_df.loc[self.districts_df['district_name'] == name][target])[0]), round_value)
        else:
            data = round(float(list(self.regions_df.loc[self.regions_df['region_name'] == name][target])[0]), round_value)
        return data

    def get_area(self, name, type_o):
        if type_o == 'district':
            area = int(list(self.districts_df.loc[self.districts_df['district_name'] == name]['district_area'])[0])
        else:
            area = int(list(self.regions_df.loc[self.regions_df['region_name'] == name]['region_area'])[0])
        return area


    districts_df = gpd.GeoDataFrame()
    regions_df = gpd.GeoDataFrame()