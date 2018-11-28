# must be executed in rc.local as user pi with syntax main_script.sh /home/pi/scripts  /home/pi/photos ortobotanico demo/foto
path_script=$1
path_photos=$2
bucket=$3
prefix_photos=$4
# key of the scheduler on s3
key_scheduler='demo/sched_wittypi'
# i reuse some functions of the wittypi utilities
. "/home/pi/wittyPi/utilities.sh"

cd $path_script
#must run all the scripts in the dir scripts/photo where for each plant there is a script called as the plant
./retrieve_photos.sh $path_script $path_photos
#check internet connection
if $(has_internet); then
  echo 'connected'
  ./sync_scheduler.sh $bucket $key_scheduler.wpi $path_script
  ./sync_photos.sh $path_photos $bucket/$prefix_photos
fi
#execute kill_rasp.sh in background
nohup ./kill_rasp.sh > /dev/null 2>&1 &
