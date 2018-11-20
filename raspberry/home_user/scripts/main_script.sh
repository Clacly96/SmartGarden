# va eseguito nel file rc.local come utente pi e con la sintassi main_script.sh /home/pi/scripts  /home/pi/photos ortobotanico demo/foto
path_script=$1
path_photos=$2
bucket=$3
prefix_photos=$4
key_scheduler=$5

. "/home/pi/wittyPi/utilities.sh"

cd $path_script
#deve lanciare tutti gli script presenti nella dir script_photo dove per ogni pianta c'è uno script che si chiama come la pianta
./retrieve_photos.sh $path_script $path_photos
#controllo se c'è internet
if $(has_internet); then
  echo 'connesso'
  ./sync_scheduler.sh $bucket $key_scheduler $path_script ../wittyPi
#poi lancia sync_photos.sh
  ./sync_photos.sh $path_photos $bucket/$prefix_photos
fi
#poi lancia kill_rasp.sh però in background
nohup ./kill_rasp.sh > /dev/null 2>&1 &
