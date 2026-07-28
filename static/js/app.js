async function actualizar() {

    const r = await fetch("/api/status");
    const d = await r.json();

    document.getElementById("estado").innerHTML =
        "🎥 " + (d.recording ? "GRABANDO" : "PARADO") + "<br>" +
        "💻 CPU " + d.cpu + "%<br>" +
        "🌡️ TEMP " + d.temp + "°C<br>" +
        "💾 DISCO " + d.disk + "%<br>" +
        "📹 VÍDEOS " + d.videos;

    const start = document.getElementById("start");
    const stop = document.getElementById("stop");

    if (d.recording) {

        start.disabled = true;
        stop.disabled = false;

        start.style.opacity = "0.4";
        stop.style.opacity = "1";

    } else {

        start.disabled = false;
        stop.disabled = true;

        start.style.opacity = "1";
        stop.style.opacity = "0.4";
    }

}

setInterval(actualizar, 1000);

actualizar();