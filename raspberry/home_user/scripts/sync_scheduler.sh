#must download the .wpi file comparing it with the one in use and if they are different, reload it to the wittipy
BUCKET=$1
KEY_SCHEDULER=$2
path_script=$3
scheduler='scheduler.wpi'
scheduler_prov='scheduler_prov.wpi'

cd $path_script
aws s3 cp s3://$BUCKET/$KEY_SCHEDULER $scheduler_prov
# Compare byte files so much as they are very small files
if cmp -s $scheduler $scheduler_prov ; then
  echo 'same file sched'
  rm $scheduler_prov
else
  ls
  mv $scheduler_prov $scheduler
  sudo  cp $scheduler /home/pi/wittyPi/schedule.wpi
  echo '  Running the script...'
  sudo /home/pi/wittyPi/runScript.sh | sudo tee -a /home/pi/wittyPi/schedule.log
  echo '  Done :-)'
fi
