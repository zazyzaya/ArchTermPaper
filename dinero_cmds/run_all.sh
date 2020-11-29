array=( control cora_w_data cora_no_data citeseer_w_data citeseer_no_data )
for i in "${array[@]}"
do
    for f in [^run_all]*.sh
    do
        ./$f $i.din $i.out
    done
done