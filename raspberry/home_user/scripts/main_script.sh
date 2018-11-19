# va eseguito nel file rc.local come utente pi e con la sintassi main_script.sh /home/pi/scripts  /home/pi/photos ortobotanico demo/foto
path_script=$1
path_photos=$2
bucket=$3
prefix_photos=$4

cd $path_script
pwd
#deve lanciare tutti gli script presenti nella dir script_photo dove per ogni pianta c'è uno script che si chiama come la pianta
./retrieve_photos.sh $path_script $path_photos
#poi lancia sync_photos.sh
./sync_photos.sh $path_photos $bucket/$prefix_photos
#poi lancia kill_rasp.sh però in background
nohup ./kill_rasp.sh > /dev/null 2>&1 &
