google.charts.load('current', {'packages': ['corechart']});
google.charts.setOnLoadCallback(function() {
  var container = document.getElementById('chart');

  $.getJSON(container.dataset.source, function(readings) {
    var min_temp = 0, max_temp = 0, min_humidity = 0, max_humidity = 0;

    for (var i=0; i<readings.length; i++) {
      if (readings[i].ext_temp < readings[min_temp].ext_temp) {
        min_temp = i;
      }
      if (readings[i].ext_temp > readings[max_temp].ext_temp) {
        max_temp = i;
      }
      if (readings[i].humidity < readings[min_humidity].humidity) {
        min_humidity = i;
      }
      if (readings[i].humidity > readings[max_humidity].humidity) {
        max_humidity = i;
      }
    }

    var temp_range = readings[max_temp].ext_temp - readings[min_temp].ext_temp;
    var humidity_range = readings[max_humidity].humidity - readings[min_humidity].humidity;

    var data = new google.visualization.DataTable();

    data.addColumn('datetime', 'Timestamp');
    data.addColumn('number', 'External Temperature');
    data.addColumn({type: 'string', role: 'tooltip'});
    data.addColumn({type: 'string', role: 'annotation'});
    data.addColumn('number', 'Relative Humidity');
    data.addColumn({type: 'string', role: 'tooltip'});
    data.addColumn({type: 'string', role: 'annotation'});
    data.addColumn('number', 'Luminosity');
    data.addColumn({type: 'string', role: 'tooltip'});
    data.addColumn('number', 'Internal Temperature');
    data.addColumn({type: 'string', role: 'tooltip'});

    for (var i=0; i<readings.length; i++) {
      var timestamp = new Date(readings[i].timestamp);
      var ext_temp_f = readings[i].ext_temp * 9/5 + 32;
      var int_temp_f = readings[i].int_temp * 9/5 + 32;
      var humidity = readings[i].humidity;
      var luminosity = Math.pow(10, 6) / readings[i].resistance;
      data.addRow([
        timestamp,
        ext_temp_f,
        ext_temp_f.toFixed(1) + '℉',
        (i==min_temp || i==max_temp) ? ext_temp_f.toFixed(1) + '℉' : null,
        humidity,
        humidity.toFixed(1) + '%',
        (i==min_humidity || i==max_humidity) ? humidity.toFixed(1) + '%' : null,
        luminosity,
        luminosity.toFixed(2),
        int_temp_f,
        int_temp_f.toFixed(1) + '℉'
      ]);
    }

    var chart = new google.visualization.LineChart(container);
    var title = container.dataset.title;
    var options = {
      colors: ['#f44336', '#2196f3', '#fdd835', '#ff9800'],
      focusTarget: 'category',
      hAxis: { format: 'HH:mm', title: '' },
      height: 300,
      legend: { position: 'bottom' },
      series: [
        { targetAxisIndex: 0, curveType: 'function' },
        { targetAxisIndex: 1 },
        { targetAxisIndex: 2, curveType: 'function' },
        { targetAxisIndex: 3, lineDashStyle: [1, 2] },
      ],
      title: title,
      vAxes: [
        {
          format: (temp_range < 2 ? "#.0℉" : "#℉"),
          textStyle: { color: '#f44336' }
        },
        {
          format: (humidity_range < 2 ? "#.#'%" : "#'%"),
          textStyle: { color: '#2196f3' }
        },
        {
          gridlines: { count: 0 },
          scaleType: 'log',
          textPosition: 'none',
          viewWindowMode: 'maximized',
        },
        {
          gridlines: { count: 0 },
          textPosition: 'none',
        },
      ],
    };

    chart.draw(data, options);
  });
});
