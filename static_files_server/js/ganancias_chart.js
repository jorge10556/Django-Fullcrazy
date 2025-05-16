google.charts.load('current', { packages: ['corechart'] }); 
google.charts.setOnLoadCallback(drawChart);

function drawChart() {

    const datosEventos = JSON.parse(document.getElementById('datosEventos').textContent);

    const data = google.visualization.arrayToDataTable([
        ['Evento', 'Ganancias'],
        ...datosEventos 
    ]);

    const options = {
        title: 'Ganancias',
        hAxis: { title: 'Evento' },
        vAxis: { title: 'Ganancias' },
        legend: 'none'
    };

    const chart = new google.visualization.LineChart(document.getElementById('myChart'));
    chart.draw(data, options);
}
