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

    for (var i=0; i<readings.length; i++) {
      var timestamp = new Date(readings[i].timestamp);
      var temp_f = readings[i].ext_temp * 9/5 + 32;
      var humidity = readings[i].humidity;
      var luminosity = Math.pow(10, 6) / readings[i].resistance;
      data.addRow([
        timestamp,
        temp_f,
        temp_f.toFixed(1) + '°F',
        (i==min_temp || i==max_temp) ? temp_f.toFixed(1) + '°F' : null,
        humidity,
        humidity.toFixed(1) + '%',
        (i==min_humidity || i==max_humidity) ? humidity.toFixed(1) + '%' : null,
        luminosity,
        luminosity.toFixed(2),
      ]);
    }

    var chart = new google.visualization.LineChart(container);
    var title = new google.visualization.DateFormat({
      pattern: 'EEEE, MMMM d, yyyy',
    }).formatValue(new Date(container.dataset.date));
    var options = {
      colors: ['#f44336', '#2196f3', '#fdd835'],
      curveType: 'function',
      focusTarget: 'category',
      hAxis: { format: 'HH:mm', title: '' },
      height: 300,
      legend: { position: 'bottom' },
      series: [
        { targetAxisIndex: 0 },
        { targetAxisIndex: 1 },
        { targetAxisIndex: 2 },
      ],
      title: title,
      vAxes: [
        { format: "#°F", textStyle: { color: '#f44336' } },
        { format: "#'%", textStyle: { color: '#2196f3' } },
        {
          gridlines: { count: 0 },
          scaleType: 'log',
          textPosition: 'none',
          viewWindowMode: 'maximized',
        },
      ],
    };

    chart.draw(data, options);
  });
});
