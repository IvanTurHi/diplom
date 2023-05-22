def form_geom_list_of_polygons(big_list):
        list_of_p = []
        for i in range(len(big_list)):
            for j in range(len(big_list[i])):
                list_of_p += list(big_list[i][j])
        return list_of_p