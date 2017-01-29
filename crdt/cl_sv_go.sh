numPeers=$1
encrypt=$2

prefix="172.18.0."

# DOCKER RUN WITH APPROPRIATE ARGUMENTS
for i in $(seq 2 $((numPeers+1))); do
    ip="$prefix$i"
    args="$ip 127.0.0.1 8889 $encrypt"
    gnome-terminal -x sh -c "cd src; python3 run_cl_sv.py ${args} ; bash"
done
cd src
python3 run_sv.py 172.18.0.1 8889 $encrypt