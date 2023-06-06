TEST_DIR=$(pwd)
SAT_ROOT_=$(dirname "$TEST_DIR")

testname1=${TEST_DIR}"/barycentric_coordinates/SAT/barycentric_coordinates.txt"
testname2=${TEST_DIR}"/circleofpts/SAT/circleofpts.txt"
testname3=${TEST_DIR}"/ClosestPtPointSegment2/SAT/ClosestPtPointSegment2.txt"
testname4=${TEST_DIR}"/cubicspline/SAT/cubicspline.txt"
testname5=${TEST_DIR}"/DistSinusoid/SAT/distsinusoid.txt"
testname6=${TEST_DIR}"/EigenSphere/SAT/EigenSphere.txt"
testname7=${TEST_DIR}"/EnclosingSphere/SAT/EnclosingSphere.txt"
testname8=${TEST_DIR}"/gram-schmidt/SAT/gram-schmidt.txt"
testname9=${TEST_DIR}"/Interpolator/SAT/interpolator.txt"
testname10=${TEST_DIR}"/Jacobi/SAT/Jacobi.txt"
testname11=${TEST_DIR}"/lead-lag/SAT/lead-lag.txt"
testname12=${TEST_DIR}"/MD/SAT/md.txt"
testname13=${TEST_DIR}"/nonline-interpolation/SAT/interpol.txt"
testname14=${TEST_DIR}"/Poisson/SAT/poisson.txt"
testname15=${TEST_DIR}"/ray_tracing/SAT/ray_tracing.txt"
testname16=${TEST_DIR}"/smartRoot/SAT/smartRoot.txt"
testname17=${TEST_DIR}"/SphereOfSphereAndPt/SAT/SphereOfSphereAndPt.txt"
testname18=${TEST_DIR}"/squareRoot3/SAT/squareRoot3.txt"
testname19=${TEST_DIR}"/styblinski/SAT/styblinski.txt"
testname20=${TEST_DIR}"/SymSchur/SAT/SymSchur2.txt"
testname21=${TEST_DIR}"/test2/SAT/test2.txt"

export SAT_ROOT=${SAT_ROOT_}

cd ../src
echo ${testname1}
python3 satire+.py  \
    --std \
		--file ${testname1} \
		--enable-constr

echo ${testname2}
python3 satire+.py  \
        --std \
		--file ${testname2} \
		--enable-constr

echo ${testname3}
python3 satire+.py  \
        --std \
		--file ${testname3} \
		--enable-constr

echo ${testname4}
python3 satire+.py  \
        --std \
		--file ${testname4} \
		--enable-constr

echo ${testname5}
python3 satire+.py  \
        --std \
		--file ${testname5} \
		--enable-constr

echo ${testname6}
python3 satire+.py  \
        --std \
		--file ${testname6} \
		--enable-constr

echo ${testname7}
python3 satire+.py  \
        --std \
		--file ${testname7} \
		--enable-constr

echo ${testname8}
python3 satire+.py  \
        --std \
		--file ${testname8} \
		--enable-constr

echo ${testname9}
python3 satire+.py  \
        --std \
		--file ${testname9} \
		--enable-constr

echo ${testname10}
python3 satire+.py  \
        --std \
		--file ${testname10} \
		--enable-constr

echo ${testname11}
python3 satire+.py  \
        --std \
		--file ${testname11} \
		--enable-constr

echo ${testname12}
python3 satire+.py  \
        --std \
		--file ${testname12} \
		--enable-constr

echo ${testname13}
python3 satire+.py  \
        --std \
		--file ${testname13} \
		--enable-constr

echo ${testname14}
python3 satire+.py  \
        --std \
		--file ${testname14} \
		--enable-constr

echo ${testname15}
python3 satire+.py  \
        --std \
		--file ${testname15} \
		--enable-constr

echo ${testname16}
python3 satire+.py  \
        --std \
		--file ${testname16} \
		--enable-constr

echo ${testname17}
python3 satire+.py  \
        --std \
		--file ${testname17} \
		--enable-constr

echo ${testname18}
python3 satire+.py  \
        --std \
		--file ${testname18} \
		--enable-constr

echo ${testname19}
python3 satire+.py  \
        --std \
		--file ${testname19} \
		--enable-constr

echo ${testname20}
python3 satire+.py  \
        --std \
		--file ${testname20} \
		--enable-constr

echo ${testname21}
python3 satire+.py  \
        --std \
	    --file ${testname21} \
	    --enable-constr
		
