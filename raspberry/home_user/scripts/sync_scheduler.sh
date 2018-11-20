#deve scaricare il file .wpi confrontarlo con quello in uso e se sono diversi, ricaricarlo sul wittipy
BUCKET=$1
KEY_SCHEDULER=$2
path_script=$3
path_utils=$4
scheduler='startup_scheduler.wpi'
scheduler_prov='startup_scheduler_prov.wpi'
# inizio script
cd $path_script
aws s3 cp s3://$BUCKET/$KEY_SCHEDULER $scheduler_prov
# confronto i file a byte tanto sono file molto piccoli
if cmp -s $scheduler $scheduler_prov ; then
  echo 'same file sched'
  rm $scheduler_prov
else
  ls
  mv $scheduler_prov $scheduler
  sudo  cp $scheduler $path_utils/schedule.wpi
  echo '  Running the script...'
  sudo $path_utils/runScript.sh | sudo tee -a $path_utils/schedule.log
  echo '  Done :-)'
fi
