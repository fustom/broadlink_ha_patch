CONTAINER=$(docker container ls | grep home-assistant | cut -f 1 -d ' ')
docker cp ./br_climate.py $CONTAINER:/usr/local/lib/python3.12/site-packages/broadlink/climate.py
docker cp ./ha_climate.py $CONTAINER:/usr/src/homeassistant/homeassistant/components/broadlink/climate.py