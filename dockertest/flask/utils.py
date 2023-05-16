dictfromdatabase = {
    'namecount': 'Название округа',
    'area':'Площадь',
    'schoolnumber':'Количество школ',
    'schoolload':'Средняя загрузка школ',
    'kindergartennumber':'Количество дс',
    'medicinenumber':'Количество мед. учреждений',
    'livingnumber':'Количество жилых домов',
    'residentsnumber':'Количество жильцов',
    'avgyear':'Средний год постройки',
    'withoutschools':'хз школ',
    'withoutkindergartens':'хз дс',
    'withoutmedicine':'хз мед',
    'namedistrict':'Название района',
    'schoolprovisionindex':'Индекс обеспеченности школ',
    'kindergartenprovisionindex':'Индекс обеспеченности дс',
    'schoolprovision':'Обеспеченность школами*',
    'kindergartenprovision':'Обеспеченность дс*',
    'storey': 'Этажность',
    'pupils':'Количество школьников',
    'adress': 'Адрес',
    'adults': 'Количество взрослых',
    'children': 'Количество детей',
    'availablekindergartens': 'Кол-во дс в радиусе R-доступности',
    'availablemedicine': 'Кол-во мед. учреждений в R-доступности',
    'availableschools': 'Кол-во школ в R-доступности',
    'buildyear': 'Год постройки',
    'latitude': 'Широта',
    'longitude': 'Долгота',
    'freeschools': 'Количество свободных школ',
    'fullname': 'Название',
    'calculatedworkload': 'Загруженность (в процентах от номинальной)',
    'currentworkload': 'Количество учеников',
    'stnumber': 'Номинальная вместимость',
    'website': 'Сайт',
    'rating': 'Рейтинг',
    'buildid': 'Идентификатор',
    'idSpatial': 'ГеоИдентификатор'
}

notUsedTypes = [
    'geometry',
    'flats',
    'idspatial', 
    'eoid',
    'storey',
    'totalarea']

def schooltype():
    return " and t.nameType = 'Школа' "

def kindergartentype():
    return " and t.nameType = 'Детский сад' "