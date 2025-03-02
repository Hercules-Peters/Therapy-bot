document.addEventListener("DOMContentLoaded", function () {
    // Initialize the OpenLayers map centered on Nairobi
    const map = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([36.8219, -1.2921]), // Nairobi coordinates
            zoom: 3  // Zoomed out to view markers worldwide
        })
    });

    // Define an icon style for markers using your custom icon from static/img
    const iconStyle = new ol.style.Style({
        image: new ol.style.Icon({
            anchor: [0.5, 1],
            src: '/static/img/location_pin.png'
        })
    });

    // Array of locations (Kenyan cities and 10 additional world locations)
    const locations = [
        // Kenyan cities
        { lon: 36.8219, lat: -1.2921, title: "Nairobi" },
        { lon: 37.0833, lat: -1.0333, title: "Thika" },
        { lon: 37.6667, lat: 0.0333, title: "Chuka" },
        { lon: 36.0800, lat: -0.3031, title: "Nakuru" },
        { lon: 36.9564, lat: -0.4167, title: "Nyeri" },
        { lon: 37.4500, lat: -0.5700, title: "Embu" },
        { lon: 37.6500, lat: 0.0500, title: "Meru" },
        { lon: 36.3167, lat: -0.2667, title: "Nyahururu" },
        // Additional world locations
        { lon: -0.1278, lat: 51.5074, title: "London" },
        { lon: 2.3522, lat: 48.8566, title: "Paris" },
        { lon: -74.0060, lat: 40.7128, title: "New York" },
        { lon: 139.6917, lat: 35.6895, title: "Tokyo" },
        { lon: 151.2093, lat: -33.8688, title: "Sydney" },
        { lon: 37.6173, lat: 55.7558, title: "Moscow" },
        { lon: -43.1729, lat: -22.9068, title: "Rio de Janeiro" },
        { lon: 31.2357, lat: 30.0444, title: "Cairo" },
        { lon: 72.8777, lat: 19.0760, title: "Mumbai" },
        { lon: 18.4241, lat: -33.9249, title: "Cape Town" }
    ];

    // Create features (markers) for each location
    const features = locations.map(location => {
        const feature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat([location.lon, location.lat])),
            name: location.title
        });
        feature.setStyle(iconStyle);
        return feature;
    });

    // Create a vector source and layer to hold the marker features
    const vectorSource = new ol.source.Vector({ features: features });
    const vectorLayer = new ol.layer.Vector({ source: vectorSource });
    map.addLayer(vectorLayer);
});
