window.nextState = ->
    if window.keyidx > window.data["keys"].length
        console.log "ERROR: No more keys."
        return false
    stamp = window.data["keys"][window.keyidx]
    for i in window.data[stamp][1]
        window.carstate.push i
    for i in window.data[stamp][0]
        ridx = window.carstate.indexOf i
        window.carstate.splice ridx, 1
    time = new Date stamp * 1000
    window.map.attributionControl.setPrefix time.toString()
    window.heatmap.redraw()
    window.keyidx++
    setTimeout 'nextState();', 333

document.addEventListener 'DOMContentLoaded', (event) ->
    console.log 'Data: %o', window.data

    berlin_topleft = L.latLng 52.575463, 13.182306
    berlin_botrght = L.latLng 52.425506, 13.549104
    berlin = L.latLngBounds berlin_topleft, berlin_botrght

    window.map = L.map('map', {maxBounds: berlin}).setView berlin.getCenter(), 12
    window.tiles = L.tileLayer('berlin/{z}/{x}/{y}.png', {minZoom: 11, maxZoom: 13, bounds: berlin, opacity: 0.4}).addTo map

    window.keyidx = 0
    window.carstate = []

    window.heatmap = L.heatLayer(window.carstate, {radius: 15}).addTo map

    setTimeout 'nextState();', 500
