// Получение данных для графика
document.addEventListener("DOMContentLoaded", () => {
    var graphPhaseData = JSON.parse(document.getElementById('graphPhaseChart').value);
    var graphDurationQualityData = JSON.parse(document.getElementById('graphDurationQualityChart').value);
    var graphSleepDeepFastData = JSON.parse(document.getElementById('graphSleepDeepFastChart').value);
    var graphQualityData = JSON.parse(document.getElementById('graphQualityChart').value);

      // График для graphPhaseData
    Highcharts.chart('graph-Phase-Chart', {
         credits: {
            enabled: false
        },
        chart: {
            type: 'line'
        },
        title: {
            text: 'Общее время сна (часы)'
        },
        xAxis: {
            categories: graphPhaseData.dates
        },
        yAxis: {
            title: {
                text: 'Продолжительность сна'
            }
        },
        series: [{
            name: 'Продолжительность сна',
            data: graphPhaseData.sleep_duration,
        }]
    });

    // График для graphDurationQualityData
    Highcharts.chart('graph-Duration-QualityChart', {
         credits: {
            enabled: false
        },
        chart: {
            type: 'column'
        },
        title: {
            text: 'Зависимость продолжительности и качестве сна'
        },
        xAxis: {
            categories: graphDurationQualityData.dates
        },
        yAxis: [{
            title: {
                text: 'Продолжительность сна (часы)'
            }
        }, {
            title: {
                text: 'Качество сна (%)'
            },
            opposite: true
        }],
        series: [{
            name: 'Продолжительность сна (часы)',
            data: graphDurationQualityData.sleep_duration,
            yAxis: 0
        }, {
            name: 'Качество сна',
            data: graphDurationQualityData.sleep_quality,
            yAxis: 1
        }]
    });

    // График для graphSleepDeepFastData
    Highcharts.chart('graph-Sleep-DeepFastChart', {
        credits: {
                enabled: false
            },
        chart: {
            type: 'column'
        },
        title: {
            text: 'Зависимость глубокой и лёгкой фазы сна (часы)'
        },
        xAxis: {
            categories: graphSleepDeepFastData.dates
        },
        yAxis: {
            title: {
                text: 'Продолжительность сна (часы)'
            }
        },
        series: [{
            name: 'Фаза глубоко сна (часы)',
            data: graphSleepDeepFastData.deep_sleep_duration
        }, {
            name: 'Фаза лёгкого сна (часы)',
            data: graphSleepDeepFastData.fast_sleep_duration
        }]
    });

    // График для graphQualityData
    Highcharts.chart('graph-Quality-Chart', {
        credits: {
                enabled: false
            },
        chart: {
            type: 'line'
        },
        title: {
            text: 'Качество сна (%)'
        },
        xAxis: {
            categories: graphQualityData.dates
        },
        yAxis: {
            title: {
                text: 'Качество сна (%)'
            }
        },
        series: [{
            name: 'Качество сна (%)',
            data: graphQualityData.sleep_quality
        }]
    });
});