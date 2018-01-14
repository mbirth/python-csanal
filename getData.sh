#!/bin/sh
# LOC is one of: berlin, frankfurt, hamburg, muenchen, rheinland, stuttgart
LOC="berlin"
OAUTH_CONSUMER_KEY="car2gowebsite"
FORMAT="json"
OUTPUT_DIR="data"

# URL found via browser's dev tools' "Networking" view
URL="https://www.car2go.com/api/v2.1/vehicles?loc=${LOC}&oauth_consumer_key=${OAUTH_CONSUMER_KEY}&format=${FORMAT}"
echo "URL: $URL"

while [ 1 ]; do
    STAMP=`date +%Y-%m-%d_%H%M%S`
    OUTPUT="$OUTPUT_DIR/$STAMP.json"
    wget -q "$URL" -O "$OUTPUT"
    if [ $? -eq 0 ]; then
        echo -n "."
    else
        echo -n "!"
        rm "$OUTPUT"
    fi
    sleep 30
done
