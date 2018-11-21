#cycle for that launches n times the command sync photos, you need an ls to know how many and which folders should be synchronized, evaluate parameterization path_key photo
PATH_PHOTOS=$1
OUT=$2 # bucket/key
plants=($(ls $PATH_PHOTOS))
for plant in ${plants[@]}; do
  aws s3 sync $PATH_PHOTOS/$plant  s3://$OUT/$plant
done
