

function getRandomColor() {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}



function setRandomColor() {
  $("#colorpad").css("background-color", getRandomColor());
}
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<div id="colorpad" style="width:300px;height:300px;background-color:#000">

</div>
<button onclick="setRandomColor()">Random Color</button>






const labels = {{ tournament.names }}
const data = {
    datasets: [
        {% for sorted_tournament in sorted_tournaments %}
            {
                label: {{ sorted_tournament.event.name }},
                data: Utils.numbers(), generate a list of scores for each tournamnet
                backgroundColor: Utils.CHART_COLORS.random color,
                stack: 'Stack 0',
            }
        {% endfor %}
    ],
    datasets: [{
        axis: 'y',
        label: '',
        data: [65, 59, 80, 81, 56, 55, 40],
        fill: false,
    backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(255, 159, 64, 0.2)',
        'rgba(255, 205, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(201, 203, 207, 0.2)'
    ],
        borderColor: [
        'rgb(255, 99, 132)',
        'rgb(255, 159, 64)',
        'rgb(255, 205, 86)',
        'rgb(75, 192, 192)',
        'rgb(54, 162, 235)',
        'rgb(153, 102, 255)',
        'rgb(201, 203, 207)'
    ],
        borderWidth: 1
    }]
};