#must run all the scripts in the dir scripts/photo where for each plant there is a script called as the plant
path_script=$1
path_photos=$2
cd $path_script
script_photo=$(ls photo)
cd photo #  dir where there are scripts to retrieve the photos
for script in ${script_photo[@]}; do
  ./$script $path_photos
done
