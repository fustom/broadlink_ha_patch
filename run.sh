CONTAINER=$(docker container ls | grep home-assistant | cut -f 1 -d ' ')
docker cp ./br_climate.py $CONTAINER:/usr/local/lib/python3.10/site-packages/broadlink/climate.py
docker cp ./ha_climate.py $CONTAINER:/usr/src/homeassistant/homeassistant/components/broadlink/climate.py
docker cp ./const.py $CONTAINER:/usr/src/homeassistant/homeassistant/components/broadlink/const.py
docker cp ./updater.py $CONTAINER:/usr/src/homeassistant/homeassistant/components/broadlink/updater.py
docker cp ./manifest.json $CONTAINER:/usr/src/homeassistant/homeassistant/components/broadlink/manifest.json