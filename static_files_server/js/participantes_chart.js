google.charts.load('current', { 'packages': ['corechart'] });
google.charts.setOnLoadCallback(drawChart);

function drawChart() {

    const datosParticipantes = JSON.parse(document.getElementById('datosParticipantes').textContent);


    var data = google.visualization.arrayToDataTable([
        ['Evento', 'Asistencias'],
        ...datosParticipantes
    ]);

    var options = {
        title: 'Participantes'
    };

    var chart = new google.visualization.PieChart(document.getElementById('piechart'));

    chart.draw(data, options);
}