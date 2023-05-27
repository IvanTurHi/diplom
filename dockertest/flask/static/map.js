function readData() {
    let cusid_ele = document.getElementsByClassName('inner');
    let districtsArray = [];
    for (var i = 0; i < cusid_ele.length; ++i) {
        var item = cusid_ele[i];
        if (item.checked) {
            districtsArray.push(item.id);
        }
    }
    if (districtsArray.length == 0) {
        alert('Районы не выбраны');
        return 1;
    };
    builddatabaseCheck = document.querySelector('input[name="buldtype"]:checked');
    if (!builddatabaseCheck) {
        alert('Тип зданий не выбран');
        return 1;
    };
    builddatabase = builddatabaseCheck.value;

    return {
        districtsArray: districtsArray,
        builddatabase: builddatabase,
    }
};
function getbuildings() {
    let data = readData();
    if (data == 1) {
        return
    };
    const { districtsArray, builddatabase } = data;
    clearlayer();
    if (builddatabase == 2) {
        document.getElementById('loadingImg').style.display = '';
    }
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/buildingfullinfo', true); // false for synchronous request
    body = JSON.stringify({
        "IDsource": districtsArray,
        "isCounty": false,
        "database": parseInt(builddatabase)
    });
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            if (xmlHttp.responseText) {
                document.getElementById('loadingImg').style.display = 'none';
                textJSON = xmlHttp.responseText;
                let res = JSON.parse(textJSON);
                drawLiving(res, builddatabase);
            }
        }
    };
    xmlHttp.send(body);
}
function gethexagones() {
    let data = readData();
    if (data == 1) {
        return
    };
    const { districtsArray, builddatabase } = data;
    const hexsize = document.querySelector('input[name="hexsize"]:checked');
    if (!hexsize) {
        alert('Размер гексагона не задан');
        return 1;
    };
    const hexsizevalue = hexsize.value;
    clearlayer();
    if (builddatabase == 2) {
        document.getElementById('loadingImg').style.display = '';
    }
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/buildingfullinfo', true); // false for synchronous request
    body = JSON.stringify({
        "IDsource": districtsArray,
        "isCounty": false,
        "database": parseInt(builddatabase)
    });
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            if (xmlHttp.responseText) {

                textJSON = xmlHttp.responseText;
                let res = JSON.parse(textJSON);

                let pointsArrayWithValue = []
                if (builddatabase == 2) {
                    res['features'].forEach((element) => {
                        pointsArrayWithValue.push({
                            point: L.latLng(element.properties['Широта'], element.properties['Долгота']),
                            value: element.properties['Количество взрослых']
                        });
                    });
                } else {
                    res['features'].forEach((element) => {
                        pointsArrayWithValue.push({
                            point: L.latLng(element.properties['Широта'], element.properties['Долгота']),
                            value: 1
                        });
                    });
                }
                let xmlHttp1 = new XMLHttpRequest();
                xmlHttp1.open("POST", 'http://127.0.0.1:80/hexForDistricts', false); // false for synchronous request
                body = JSON.stringify({
                    "IDsource": districtsArray,
                    "hexagone_size": parseInt(hexsizevalue)
                });
                xmlHttp1.send(body);
                textJSON1 = xmlHttp1.responseText;
                res1 = JSON.parse(textJSON1);
                drawHexagones(res1, builddatabase, pointsArrayWithValue);
                drawLiving(res, builddatabase);
                document.getElementById('loadingImg').style.display = 'none';
            }
        }
    };
    xmlHttp.send(body);
};
function getanalysis() {
    let data = readData();
    if (data == 1) {
        return
    };
    const { districtsArray, builddatabase } = data;
    clearlayer();
    let xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/districtsfullinfo', false); // false for synchronous request
    let body = JSON.stringify({
        "IDsource": districtsArray
    });
    xmlHttp.send(body);
    textJSON_districts = xmlHttp.responseText;
    //было тут


    if (builddatabase == 2) {
        document.getElementById('loadingImg').style.display = '';
    }

    xmlHttp.open("POST", 'http://127.0.0.1:80/buildingfullinfo', true); // false for synchronous request
    body = JSON.stringify({
        "IDsource": districtsArray,
        "isCounty": false,
        "database": parseInt(builddatabase)
    });
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            if (xmlHttp.responseText) {
                document.getElementById('loadingImg').style.display = 'none';
                textJSON = xmlHttp.responseText;
                let res = JSON.parse(textJSON);
                drawLiving(res, builddatabase);
                drawdisricts(textJSON_districts, builddatabase);
            }
        }
    };
    xmlHttp.send(body);

};
function drawHexagones(res, builddatabase, pointsArrayWithValue) {

    counter = 0;
    let layerGroupBounds = L.layerGroup();
    let layerGroupHexs = L.layerGroup();
    res.forEach((element) => {
        let h3Bounds = h3.cellToBoundary(element);
        for (var i = 0; i < h3Bounds.length; i++) {
            h3Bounds[i] = [h3Bounds[i][1], h3Bounds[i][0]];
        }
        counter = 0;
        var polygon = L.polygon(h3Bounds, { color: 'blue', fillOpacity: 0.0, weight: 1, });

        polygon.myTag = "myGeoJSON"
        pointsArrayWithValue.forEach((point) => {
            if (polygon.getBounds().contains(point.point)) {
                counter += point.value;
            };
        });
        let dictGrades = {
            0: [1, 2, 3],
            1: [1, 2, 3],
            2: [1000, 2000, 3000],
            3: [1, 2, 3],
        };
        gradesHex = dictGrades[builddatabase];
        polygon.setStyle(getStyleForHexagone(gradesHex, counter));
        polygon.bindTooltip(counter)
        polygon.addTo(map_init);
        layerGroupHexs.addLayer(polygon);


        var polygon = L.polygon(h3Bounds, { color: 'black', fillOpacity: 0.0, weight: 1, });
        polygon.myTag = "myGeoJSON"
        polygon.addTo(map_init);
        layerGroupBounds.addLayer(polygon);

    });

    controlsLayer.addOverlay(layerGroupBounds, "Гексагональная сетка").expand();
    map_init.addLayer(layerGroupBounds);
    overLayers.push(layerGroupBounds);
    controlsLayer.addOverlay(layerGroupHexs, "Распределение школ внутри района");
    map_init.addLayer(layerGroupHexs);
    overLayers.push(layerGroupHexs);

    var legend = L.control({ position: 'bottomleft' });

    legend.onAdd = function (map) {
        var div = L.DomUtil.create("div", "legend");
        div.innerHTML += "<h4> Раскраска гексагонов </h4>";
        for (var i = 0; i < gradesHex.length; i++) {
            div.innerHTML += '<i style="background: ' + getStyleForHexagone(gradesHex, gradesHex[i]).color + '"></i><span>' + parseInt(gradesHex[i]) + '+</span><br>';
        }
        return div;
    };
    legend.addTo(map_init);
    legendsOnMap.push(legend);
};
function drawdisricts(textJSON, builddatabase) {
    addBordersToMap(textJSON);
    controlsLayer.addOverlay(GeoJson, "Границы районов");
    map_init.addLayer(GeoJson);
    overLayers.push(GeoJson);
    addDistrictsToMap(textJSON, builddatabase);
    controlsLayer.addOverlay(GeoJson, "Районы").expand();
    map_init.addLayer(GeoJson);
    overLayers.push(GeoJson);
};
function getStyleForHexagone(grades, d) {
    return d >= grades[2] ? { color: "#12A328", fillOpacity: 0.5, weight: 0 } :
        d >= grades[1] ? { color: '#ffff00', fillOpacity: 0.5, weight: 0 } :
            d >= grades[0] ? { color: '#E82A2A', fillOpacity: 0.5, weight: 0 } :
                { color: '#E82A2A', fillOpacity: 0.0, weight: 0 };
}
function getAttrBase(number) {
    innerDict = {
        0: ['Школы', 'Название', 'Количество школ'],
        1: ['Медицина', '', 'Количество мед. учреждений'],
        2: ['Жилые здания', 'Адрес', 'Количество жильцов'],
        3: ['Детские сады', 'Название', 'Количество дс']
    }
    return innerDict[number]
}
function getColor(grades, d) {
    return d > grades[6] ? "#7a0177" :
        d > grades[5] ? '#12A328' :
            d > grades[4] ? '#12A318' :
                d > grades[3] ? '#7CF18F' :
                    d > grades[2] ? '#FED976' :
                        d > grades[1] ? '#ffa500' :
                            d > grades[0] ? '#E82A2A' :
                                '#C91E16';
};
function addDistrictsToMap(text, builddatabase) {
    const res = JSON.parse(text);
    field = getAttrBase(builddatabase)[2]
    maxvalue = 0
    minvalue = 100000
    L.geoJson(res, {
        onEachFeature: function (feature, layer) {
            if (feature.properties[field] > maxvalue) {
                maxvalue = feature.properties[field]
            } else {
                if (feature.properties[field] < minvalue) {
                    minvalue = feature.properties[field]
                }
            }
        }
    });

    if (minvalue == 100000) {
        maxvalue = 40;
        minvalue = 10;
    }
    grades = [minvalue, minvalue + 0.1 * (maxvalue - minvalue), minvalue + 0.25 * (maxvalue - minvalue), minvalue + 0.4 * (maxvalue - minvalue), minvalue + 0.6 * (maxvalue - minvalue), minvalue + 0.8 * (maxvalue - minvalue), maxvalue];
    GeoJson = L.geoJson(res, {
        onEachFeature: function (feature, layer) {
            layer.myTag = "myGeoJSON"
            layer.setStyle({
                color: getColor(grades, feature.properties[field]),
                fillOpacity: .5,
                weight: 0,
            })
        }
    }).addTo(map_init);
    var legend = L.control({ position: 'bottomleft' });

    legend.onAdd = function (map) {
        var div = L.DomUtil.create("div", "legend");
        div.innerHTML += "<h4>" + field + "</h4>";
        for (var i = 0; i < grades.length; i++) {
            div.innerHTML += '<i style="background: ' + getColor(grades, grades[i]) + '"></i><span>' + parseInt(grades[i]) + '+</span><br>';
        }
        return div;
    };
    legend.addTo(map_init);
    legendsOnMap.push(legend);
};
function addBordersToMap(text) {
    const res = JSON.parse(text);
    GeoJson = L.geoJson(res, {
        onEachFeature: function (feature, layer) {
            layer.myTag = "myGeoJSON"
            layer.setStyle({
                color: 'black',
                fillOpacity: 0.0,
                weight: 1,
            })
        }
    }).bindPopup(function (layer) {
        return String(layer.feature.properties.nameDistrict);
    }).addTo(map_init);
};
function clearlayer() {
    map_init.eachLayer(function (layer) {
        if (layer.myTag && layer.myTag === "myGeoJSON") {
            map_init.removeLayer(layer)
        }
    });
    overLayers.forEach(function (entry) {
        controlsLayer.removeLayer(entry);
    });
    legendsOnMap.forEach(function (entry) {
        map_init.removeControl(entry);
    });
    /*
    var ul = document.getElementById('listOfChanges');
    if (ul) {
        while (ul.firstChild) {
            ul.removeChild(ul.firstChild);
        }
    };
    */
};
function addInfoAvailRinCard(newlon, newlat) {
    return "<button onclick='availRfromCard(this);'>Построить радиус доступности</button><label id='hiddencoordinates' hidden>" + newlat + ',' + newlon + "</label>"
};
function addEditinCard() {
    return "<button onclick='EditInfo(this);'>Изменить информацию о здании</button>"
};
function drawLiving(res, builddatabase) {

    features = getAttrBase(builddatabase);
    main_feature = features[1];
    let newlon = 0.0
    let newlat = 0.0
    dictType = {0:"Школа",1:"Мед",2:"Жилое",3:"Детский сад"}

    var GeoJson = L.geoJson(res, {
        onEachFeature: function (feature, layer) {
            layer.myTag = "myGeoJSON";
            layer.type = dictType[builddatabase]
            stringTable = '';
            main_value = '';
            if (feature.properties) {
                stringTable += '<tr style="display:none;"><td>objectid</td><td>' + feature.properties['Идентификатор'] + '</td></tr>';
                stringTable += '<tr style="display:none;"><td>type</td><td>' + builddatabase + '</td></tr>'
                for (key in feature.properties) {
                    switch (key) {
                        case (main_feature): main_value = feature.properties[key]; break;
                        case ('Широта'): newlat = feature.properties[key]; break;
                        case ('Долгота'): newlon = feature.properties[key]; break;
                        case ('iddistrict'): break;
                        case ('Идентификатор'):
                            layer.objectid = feature.properties[key];
                            break;
                        case ('ГеоИдентификатор'): break;
                        default: stringTable += '<tr><td>' + key + '</td><td>' + feature.properties[key] + '</td></tr>'
                    }
                }
            }
            layer.bindTooltip(main_value);
            popupText = '<h2>' + main_value + "</h2><table border='1' style='width:400px;'>" + stringTable + "</table>"
            if (builddatabase != 2) {
                popupText += addInfoAvailRinCard(newlon, newlat)
            }
            if (builddatabase != 1) {
                popupText += addEditinCard()
            }
            layer.bindPopup(popupText, { maxWidth: 410 });
            if (builddatabase == 2) {
                color = getColorForLiving(feature.properties['Год постройки'])
                layer.setStyle({
                    fillColor: color,
                    fillOpacity: 0.5,
                    weight: 1,
                    color: 'black'
                })
            } else {
                if (builddatabase == 0) {
                    color = getColorForSchool(feature.properties['Количество учеников'], feature.properties['Номинальная вместимость'])
                    layer.setStyle({
                        fillColor: color,
                        fillOpacity: 0.5,
                        weight: 1,
                        color: 'black'
                    })
                }
            }

        }
    })//.bindPopup(function (layer) {
    // return String(layer.feature.properties.adress);
    //})
    //.addTo(map_init);
    controlsLayer.addOverlay(GeoJson, features[0]).expand();
    map_init.addLayer(GeoJson);
    controlsLayer._update();
    overLayers.push(GeoJson);
    implementChangesOnMap();
};
function getColorForLiving(buildyear) {
    return buildyear >= 2000 ? 'green' :
        buildyear >= 1980 ? 'yellow' :
            buildyear >= 1960 ? 'orange' :
                buildyear > 0 ? 'red' :
                    'blue';
};
function getColorForSchool(currentworkload, calculatedworkload) {
    let value = currentworkload / calculatedworkload;
    return value >= 2 ? 'red' :
        value >= 1 ? 'yellow' :
            'green';
};
function getnewradius(lon, lat) {
    var field = document.getElementsByClassName('leaflet-popup-content')[0];
    table = field.childNodes[1];
    type = parseInt(table.rows[1].cells[1].innerText)
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/nearcoordinates', false); // false for synchronous request
    let body = JSON.stringify({
        "lat": lat,
        "lon": lon,
        "database": type
    });
    marker = L.marker([lat, lon])
    marker.myTag = "myGeoJSON";
    marker.addTo(map_init);

    xmlHttp.send(body);
    resp = xmlHttp.responseText;
    let res = JSON.parse(resp);
    drawLiving(res.data, 2);
    var circle = L.circle([lat, lon], {
        color: "red",
        fillColor: "#f03",
        fillOpacity: 0.5,
        radius: res.radius
    });
    circle.myTag = "myGeoJSON";
    circle.addTo(map_init);
};
let toggle = button => {
    var resp = httpGet();
    //alert(resp);
    let res = JSON.parse(resp);
    drawLiving(res);
};
let clearLayer = button => {
    clearlayer();
};
let availRfromCard = button => {
    var fields = document.getElementById('hiddencoordinates').textContent.split(',');
    var fValuelat = parseFloat(fields[0]);
    var fValuelon = parseFloat(fields[1]);
    clearlayer();
    getnewradius(fValuelon, fValuelat);
};
let EditInfo = button => {
    var field = document.getElementsByClassName('leaflet-popup-content')[0];
    table = field.childNodes[1];
    type = table.rows[1].cells[1].innerText
    switch (parseInt(type)) {
        case (0): field.innerHTML = editPopupForSchool(table.rows[0].cells[1].innerText, table.rows[2].cells[1].innerText, table.rows[4].cells[1].innerText, table.rows[5].cells[1].innerText, table.rows[7].cells[1].innerText); break;
        case (2): field.innerHTML = editPopupForLiving(table.rows[0].cells[1].innerText, field.childNodes[0].innerText, table.rows[6].cells[1].innerText); break;
        case (3): field.innerHTML = editPopupForKindergarten(table.rows[0].cells[1].innerText, table.rows[2].cells[1].innerText, table.rows[3].cells[1].innerText); break;
        default: alert(type);
    }
};

function editPopupForSchool(objectid, adress, number, load, rating) {
    html = '<p hidden>Идентификатор<input type="text" value="' + objectid + '"></p>'
    html += '<p hidden>Тип здания<input type="text" value="Школа"></p>'
    html += '<p hidden>Адрес<input type="text" value="' + adress + '"></p>'
    html += '<p hidden class="oldInfo">Количество учеников<input type="text" value=' + number + '></p>'
    html += '<p>Количество учеников<input type="number" min="0" step="1" value=' + number + '></p>'
    html += '<p hidden class="oldInfo">Номинальная вместимость<input type="text" value=' + load + '></p>'
    html += '<p>Номинальная вместимость<input type="number" min="0" step="1" value=' + load + '></p>'
    html += '<p hidden class="oldInfo">Рейтинг<input type="text" value=' + rating + '></p>'
    html += '<p>Рейтинг<input type="number" value=' + rating + '></p>'
    html += '<button onclick="savechanges(this);"name="button" id="newButton2" >Сохранить изменения</button>'
    return html
};
function editPopupForLiving(objectid, adress, numberResidents) {
    html = '<p hidden>Идентификатор<input type="text" value="' + objectid + '"></p>'
    html += '<p hidden>Тип здания<input type="text" value="Жилое"></p>'
    html += '<p hidden>Адрес<input type="text" value="' + adress + '"></p>'
    html += '<p hidden class="oldInfo">Количество взрослых<input type="text" value=' + numberResidents + '></p>'
    html += '<p>Количество взрослых<input type="number" min="0" step="1" value=' + numberResidents + '></p>'
    html += '<button onclick="savechanges(this);"name="button" id="newButton2" >Сохранить изменения</button>'
    return html
};
function editPopupForKindergarten(objectid, adress, load) {
    html = '<p hidden>Идентификатор<input type="text" value="' + objectid + '"></p>'
    html += '<p hidden>Тип здания<input type="text" value="Детский сад"></p>'
    html += '<p hidden>Адрес<input type="text" value="' + adress + '"></p>'
    html += '<p hidden class="oldInfo">Номинальная вместимость<input type="text" value=' + load + '></p>'
    html += '<p>Номинальная вместимость<input type="number" min="0" step="1" value=' + load + '></p>'
    html += '<button onclick="savechanges(this);"name="button" id="newButton2" >Сохранить изменения</button>'
    return html
};
let savechanges = button => {

    var ul = document.getElementById("listOfChanges");
    var field = document.getElementsByClassName('leaflet-popup-content')[0];

    for (var i = 0; i < field.childNodes.length - 1; i++) {
        var tableChild = field.childNodes[i];
        
    }
    var ulInner = document.createElement("ul");
    flagOFchanged = false;
    for (var i = 0; i < field.childNodes.length - 1; i++) {
        var tableChild = field.childNodes[i];
        var li = document.createElement("li");
        if (tableChild.className == "oldInfo") {
            if (field.childNodes[i + 1].childNodes[1].value == 0){
                alert(1)
            }
            li.appendChild(document.createTextNode(`${tableChild.innerText}:${tableChild.childNodes[1].value}->${field.childNodes[i + 1].childNodes[1].value}`));
            i++;
        } else {
            li.appendChild(document.createTextNode(`${tableChild.innerText}:${tableChild.childNodes[1].value}`));
        };
        ulInner.appendChild(li);
        if (tableChild.innerText == "Идентификатор") {
            li.style.display = "none"
        }
    }

    for (var i = 0; i < ul.childNodes.length; i++) {
        let adress = ul.childNodes[i].childNodes[1].childNodes[0].childNodes[2].innerText;
        let clearAdress = adress.substring(6, adress.length);
        if (clearAdress == field.childNodes[2].childNodes[1].value) {
            for (var j = 0; j < ul.childNodes[i].childNodes[1].childNodes[0].children.length; j++) {
                let oldAndNewValue = ul.childNodes[i].childNodes[1].childNodes[0].childNodes[j].innerText.split(':')[1];
                if (~oldAndNewValue.indexOf("->")) {
                    oldValue = oldAndNewValue.split('->')[0];
                    newValue = ulInner.childNodes[j].innerText.split('->')[1]
                    if (parseInt(newValue) == 0) {
                        alert(field.childNodes[i + 1].childNodes[1].value);
                        alert("Хорошая попытка проверки крайнего случая, но... нет");
                        return;
                    }
                    olddata = ul.childNodes[i].childNodes[1].childNodes[0].childNodes[j].innerText.split('->')[0] 
                    ul.childNodes[i].childNodes[1].childNodes[0].childNodes[j].innerText = olddata + '->' + newValue;
                }
            }
            //ul.childNodes[i] = ulInner;
            ul.childNodes[0].childNodes[0].textContent = "Измененный элемент";
            return
        }
    }

    var li = document.createElement("li");
    li.appendChild(document.createTextNode("Измененный элемент"));

    var divList = document.createElement("div");
    divList.setAttribute('class', 'insideeditlist');

    divList.appendChild(ulInner);

    var buttonElement = document.createElement("input");
    buttonElement.type = "button";
    buttonElement.classList.add('button-add')
    buttonElement.onclick = function () {
        delElem(this);
    };
    var divButton = document.createElement("div");
    divButton.setAttribute('class', 'insideeditlist');
    //divButton.setAttribute('style', 'width: 30%;')
    divButton.appendChild(buttonElement);
    li.appendChild(divList);
    li.appendChild(divButton);
    ul.appendChild(li);
    //field.innerHTML = '<h1>' + type + '</hi>'
};

let delElem = button => {
    button.parentElement.parentElement.remove()
};

function applychanges() {
    var ul = document.getElementById("listOfChanges");
    for (var i = 0; i < ul.childNodes.length; i++) {
        let dictElem = { data: {}, service: {} , olddata: {}}
        let listOfCharacteristics = ul.childNodes[i].childNodes[1].childNodes[0]
        ul.childNodes[i].childNodes[0].textContent = "Изменения применены"
        let oldCurrentWorkload;
        let oldNormalWorkload;
        for (var j = 2; j < listOfCharacteristics.childNodes.length; j++) {
            let characteristics = listOfCharacteristics.childNodes[j].innerText.split(':')[0];
            let oldAndNewValue = listOfCharacteristics.childNodes[j].innerText.split(':')[1];
            if (~oldAndNewValue.indexOf("->")) {
                oldValue = oldAndNewValue.split('->')[0];
                newValue = oldAndNewValue.split('->')[1];
                if (newValue != oldValue) {
                    dictElem.data[characteristics] = newValue - oldValue;
                    dictElem.olddata[characteristics] = oldValue;
                    //dictElem.data[characteristics] = newValue;
                };
                switch (characteristics) {
                    case 'Количество учеников':
                        oldCurrentWorkload = oldValue;
                        break;
                    case 'Номинальная вместимость':
                        oldNormalWorkload = oldValue;
                        break;
                    default:
                        break;
                };

            };
        };
        if (Object.keys(dictElem.data).length != 0) {
            dictElem.service.objectid = listOfCharacteristics.childNodes[0].innerText.split(':')[1];
            dictElem.service.type = listOfCharacteristics.childNodes[1].innerText.split(':')[1];
            dictElem.service.adress = listOfCharacteristics.childNodes[2].innerText.split(':')[1];

            //дополнительная проверка для школ, для изменения количества доступных школ
            if (dictElem.service.type == 'Школа') {
                oldPercentage = oldCurrentWorkload / oldNormalWorkload;
                newPercentage = (parseInt(oldCurrentWorkload) + (dictElem.data['Количество учеников'] || 0)) / (parseInt(oldNormalWorkload) + (dictElem.data['Номинальная вместимость'] || 0));
                //newPercentage = ((dictElem.data['Количество учеников'] || parseInt(oldCurrentWorkload))) / (dictElem.data['Номинальная вместимость'] || parseInt(oldNormalWorkload));
                if (oldPercentage > 1 && newPercentage < 1) {
                    dictElem.service.spec = true;
                };
                if (oldPercentage < 1 && newPercentage > 1) {
                    dictElem.service.spec = false;
                };
                dictElem.data['Загруженность (в процентах от номинальной)'] = (newPercentage - oldPercentage) * 100;
                dictElem.olddata['Загруженность (в процентах от номинальной)'] = oldPercentage * 100;
                //dictElem.data['Загруженность (в процентах от номинальной)'] = (newPercentage)*100;
            };
            insertIntoChanges(dictElem);
        };
    };
    getchangesForSchool();
    implementChangesOnMap();
};
function getchangesForSchool(dictElem) {
    let changedSchool = {}
    changesArray.forEach(function (elem) {
        if (elem.service.type == 'Школа') {
            if (elem.service.hasOwnProperty('spec')) {
                changedSchool[elem.service.objectid] = elem.service.spec
            };
        };
    });
    if (Object.keys(changesArray).length == 0) {return};
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/checkforschool', false); // false for synchronous request
    let body = JSON.stringify(changedSchool);
    xmlHttp.send(body);
    resp = xmlHttp.responseText;
    let res = JSON.parse(resp);
    res.forEach(function (elem) {
        insertIntoChanges(elem);
    })

};
function insertIntoChanges(dictElem) {
    let flag = false;
    changesArray.forEach(function (elem) {
        if (elem.service.objectid == dictElem.service.objectid && elem.service.type == dictElem.service.type) {
            flag = true;
            for (let k in dictElem.data) {
                elem.data[k] = dictElem.data[k]
                elem.olddata[k] = dictElem.olddata[k]
            }
        };
    });
    if (!flag) {
        changesArray.push(dictElem);
    }
}

function implementChangesOnMap() {
    map_init.eachLayer(function (layer) {
        changesArray.forEach(function (elem) {
            if (layer.objectid == elem.service.objectid && layer.type == elem.service.type) {
                let popup = layer.getPopup()._content;
                let percentageForSchool;
                for (let k in elem.data) {
                    //console.log(k + ' is ' + elem.data[k])
                    let startPosition = popup.indexOf(k) + k.length + 9
                    let endPosition = popup.indexOf("td", startPosition) - 2
                    let newValue = parseInt(elem.olddata[k]) + parseInt(elem.data[k]);
                    //let newValue = parseInt(elem.data[k])
                    popup = popup.substring(0, startPosition) + newValue + popup.substring(endPosition);
                    if (k == 'Загруженность (в процентах от номинальной)') {
                        percentageForSchool = parseInt(newValue);
                    }
                }
                layer.bindPopup(popup);
                if (elem.service.type == 'Школа') {
                    if (percentageForSchool != null) {
                        color = getColorForSchool(percentageForSchool, 100)
                        layer.setStyle({
                            fillColor: color,
                            fillOpacity: 0.5,
                            weight: 1,
                            color: 'black'
                        })
                    }
                }
            }
        });
    });
};
function getstatisticsdistricts(){
    let data = readData();
    if (data == 1) {
        return
    };
    const {districtsArray, builddatabase } = data;
    let araraywithData = []
    changesArray.forEach(function (elem) {
        dictwithdata = elem.data;
        dictwithdata.id = parseInt(elem.service.objectid);
        dictwithdata.type = elem.service.type;
        araraywithData.push(dictwithdata);
    });
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/checkchanges', false); // false for synchronous request
    let body = JSON.stringify({
        data: araraywithData,
        districts: districtsArray
    });
    xmlHttp.send(body);
    resp = xmlHttp.responseText;
    var tab = window.open('Статистика по выбранным районам', '_blank');
    tab.document.write(resp);
    tab.document.close();
}

function getstatisticscounties(){
    let cusid_ele = document.getElementsByClassName('outer');
    let countiesArray = [];
    for (var i = 0; i < cusid_ele.length; ++i) {
        var item = cusid_ele[i];
        if (item.checked) {
            countiesArray.push(item.id.slice(0, -1));
        }
    }
    if (countiesArray.length == 0) {
        alert('Округа не выбраны');
        return 1;
    };
    let araraywithData = []
    changesArray.forEach(function (elem) {
        dictwithdata = elem.data;
        dictwithdata.id = parseInt(elem.service.objectid);
        dictwithdata.type = elem.service.type;
        araraywithData.push(dictwithdata);
    });
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", 'http://127.0.0.1:80/checkchanges_county', false); // false for synchronous request
    let body = JSON.stringify({
        data: araraywithData,
        counties: countiesArray
    });
    xmlHttp.send(body);
    resp = xmlHttp.responseText;
    var tab = window.open('Статистика по выбранным районам', '_blank');
    tab.document.write(resp);
    tab.document.close();
}