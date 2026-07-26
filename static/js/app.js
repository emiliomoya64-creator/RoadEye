async function actualizar() {

    let r = await fetch("/api/status");

    let d = await r.json();

    document.getElementById("estado").innerHTML =

        "CPU " + d.cpu + "%<br>" +

        "TEMP " + d.temp + "°C<br>" +

        "SSD " + d.disk + "%<br>" +

        "VIDEOS " + d.videos;

}

setInterval(actualizar, 1000);

actualizar();